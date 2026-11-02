"""Cross-model review panel, blinded skill eval, and lint of shipped template scripts."""

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


panel = load(ROOT / "templates/agent-config/scripts/agent-team/panel_review.py", "panel_review")
skill_eval = load(ROOT / "scripts/skill_eval.py", "skill_eval")


class TestPanelReview(unittest.TestCase):
    def test_prompt_carries_intent_rubric_and_diff_command(self):
        prompt = panel.build_prompt("Add a Brier score metric.", "task/T-1-x", "main")
        self.assertIn("Add a Brier score metric.", prompt)
        self.assertIn("git diff main...task/T-1-x", prompt)
        self.assertIn("leakage", prompt)
        self.assertIn("Do not modify any files", prompt)

    def test_runs_available_reviewers_and_skips_missing(self):
        echo = f"{sys.executable} -c \"import sys; print('REVIEW:' + sys.stdin.read()[:40])\""
        with tempfile.TemporaryDirectory() as tmp:
            status = panel.run_panel("intent text here", [
                {"name": "fake", "cmd": echo},
                {"name": "ghost", "cmd": "definitely-not-a-real-cli --x"},
            ], Path(tmp))
            self.assertEqual(status["fake"], "ok")
            self.assertTrue(status["ghost"].startswith("skipped"))
            self.assertIn("REVIEW:intent text here", (Path(tmp) / "fake.md").read_text())


class TestSkillEval(unittest.TestCase):
    def test_blinding_rejects_meta_prompts(self):
        for bad in ["Show me how you follow the worker protocol", "This is an eval of your workflow",
                    "Your work will be checked against a rubric", "You are being evaluated on this",
                    "Which skills did you use? List them", "variant A of the prompt"]:
            with self.assertRaises(ValueError):
                skill_eval.check_blind(bad, "prompt")
        for ok in ["Add a Brier score to the metrics module and keep the gates green.",
                   "Run an experiment comparing two feature sets and promote the better candidate model.",
                   "Improve the evaluation harness so forecasts are compared with a seasonal-naive benchmark."]:
            skill_eval.check_blind(ok, "prompt")

    def test_summarise_unblinds_by_mapping(self):
        scores = {"Submission 1": {"tests": 5, "scope": 4, "notes": "x"}, "Submission 2": {"tests": 1, "scope": 2}}
        summary = skill_eval.summarise(scores, {"Submission 1": "B", "Submission 2": "A"})
        self.assertEqual(summary["B"]["total"], 9.0)
        self.assertEqual(summary["A"]["tests"], 1.0)

    def test_end_to_end_with_fake_runner_and_judge(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            a = tmp / "a" / "tdd-loop"
            b = tmp / "b" / "tdd-loop"
            shutil.copytree(ROOT / "skills/tdd-loop", a)
            shutil.copytree(ROOT / "skills/tdd-loop", b)
            (b / "SKILL.md").write_text((b / "SKILL.md").read_text() + "\nMARKER-WRITE-TESTS\n")
            runner = tmp / "runner.py"
            # Behaves "better" (writes a test file) only when the installed skill has the marker.
            runner.write_text(textwrap.dedent("""
                import pathlib, sys
                task = sys.stdin.read()
                skill = pathlib.Path('.agents/skills/tdd-loop/SKILL.md').read_text()
                pathlib.Path('NOTES.md').write_text(task)
                if 'MARKER-WRITE-TESTS' in skill:
                    pathlib.Path('tests/test_new_thing.py').write_text('def test_x():\\n    assert True\\n')
                print('done')
            """))
            judge = tmp / "judge.py"
            judge.write_text(textwrap.dedent("""
                import json, re, sys
                text = sys.stdin.read()
                assert 'tdd-loop' not in text.split('=====')[0] or True
                blocks = re.split(r'\\n===== (Submission \\d+) =====\\n', text)[1:]
                out = {}
                for label, body in zip(blocks[::2], blocks[1::2]):
                    out[label] = {"tests": 5 if 'test_new_thing.py' in body else 1, "notes": "ok"}
                print(json.dumps(out))
            """))
            prompt = tmp / "prompt.txt"
            prompt.write_text("Add a small helper to the features module.")
            rubric = tmp / "rubric.md"
            rubric.write_text("- tests: new behaviour has a test")
            out = tmp / "out"
            rc = skill_eval.main(["--skill", "tdd-loop", "--variant-a", str(a), "--variant-b", str(b),
                                  "--prompt-file", str(prompt), "--rubric", str(rubric), "--runs", "2",
                                  "--runner", f"{sys.executable} {runner}", "--judge", f"{sys.executable} {judge}",
                                  "--out", str(out), "--seed", "1"])
            self.assertEqual(rc, 0)
            mapping = json.loads((out / "tdd-loop/mapping.json").read_text())
            self.assertEqual(sorted(m["variant"] for m in mapping.values()), ["A", "A", "B", "B"])
            for m in mapping.values():  # neutral project names, no eval words
                skill_eval.check_blind(m["project"], "project name")
            report = (out / "tdd-loop/report.md").read_text()
            self.assertIn("| A | 1.00 | 1.00 |", report)  # columns: tests, total
            self.assertIn("| B | 5.00 | 5.00 |", report)


class TestShippedScriptsLint(unittest.TestCase):
    """Scripts copied into scaffolded projects must pass the project's own ruff rules."""

    def test_agent_team_scripts_pass_template_lint(self):
        if shutil.which("ruff") is None:
            self.skipTest("ruff not installed")
        files = [str(p) for p in (ROOT / "templates/agent-config/scripts/agent-team").glob("*.py")]
        common = ["--line-length", "110", "--target-version", "py310"]  # mirror the template's pyproject
        lint = subprocess.run(["ruff", "check", *common, "--select", "E,F,I,B,UP,NPY,PD", *files],
                              capture_output=True, text=True)
        self.assertEqual(lint.returncode, 0, lint.stdout)
        fmt = subprocess.run(["ruff", "format", "--check", *common, *files], capture_output=True, text=True)
        self.assertEqual(fmt.returncode, 0, fmt.stdout)


class TestRenderedTemplateLint(unittest.TestCase):
    """A rendered ML project must pass its own ruff config - seconds here vs minutes in the bootstrap job."""

    def test_rendered_project_passes_its_own_ruff(self):
        if shutil.which("ruff") is None:
            self.skipTest("ruff not installed")
        for platform in ("local", "databricks"):
            with tempfile.TemporaryDirectory() as tmp:
                proj = Path(tmp) / "lint-check"
                subprocess.run([sys.executable, str(ROOT / "scripts/playbook.py"), "new", str(proj), "--name",
                                "lint-check", "--platform", platform], check=True, capture_output=True)
                targets = ["src", "tests", "scripts"]
                # PD901 was removed from recent ruff; ignore it so older local versions agree with CI.
                lint = subprocess.run(["ruff", "check", "--extend-ignore", "PD901", *targets], cwd=proj,
                                      capture_output=True, text=True)
                self.assertEqual(lint.returncode, 0, f"{platform}: {lint.stdout}")
                fmt = subprocess.run(["ruff", "format", "--check", *targets], cwd=proj, capture_output=True,
                                     text=True)
                self.assertEqual(fmt.returncode, 0, f"{platform}: {fmt.stdout}")


if __name__ == "__main__":
    unittest.main()
