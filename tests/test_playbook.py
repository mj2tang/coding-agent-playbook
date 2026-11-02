"""Tests for the playbook itself: manifests, skills, agents, guard hook, and the scaffolder.

Run: python3 -m unittest discover -s tests -v
"""

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLAYBOOK = [sys.executable, str(ROOT / "scripts" / "playbook.py")]


def frontmatter(path: Path) -> dict:
    m = re.match(r"^---\n(.*?)\n---\n", path.read_text(), re.S)
    assert m, f"{path} has no frontmatter"
    return dict(line.split(": ", 1) for line in m.group(1).splitlines() if ": " in line)


def run(*args, cwd=None):
    return subprocess.run([*PLAYBOOK, *args], cwd=cwd, capture_output=True, text=True, check=True).stdout


class TestPackaging(unittest.TestCase):
    def test_manifests_are_valid_json_with_matching_versions(self):
        claude = json.loads((ROOT / ".claude-plugin/plugin.json").read_text())
        codex = json.loads((ROOT / ".codex-plugin/plugin.json").read_text())
        for f in (".claude-plugin/marketplace.json", ".agents/plugins/marketplace.json", "hooks/hooks.json"):
            json.loads((ROOT / f).read_text())
        self.assertEqual(claude["version"], codex["version"])

    def test_skills_have_name_matching_dir_and_routing_description(self):
        skills = sorted((ROOT / "skills").glob("*/SKILL.md"))
        self.assertGreater(len(skills), 10)
        for path in skills:
            fm = frontmatter(path)
            self.assertEqual(fm["name"], path.parent.name)
            self.assertIn("Use ", fm["description"], path)
            self.assertIn("Not ", fm["description"], path)
            self.assertLess(len(fm["description"]), 1024, path)

    def test_agents_reference_existing_skills(self):
        skill_names = {p.parent.name for p in (ROOT / "skills").glob("*/SKILL.md")}
        for path in (ROOT / "agents").glob("*.md"):
            fm = frontmatter(path)
            self.assertEqual(fm["name"], path.stem)
            for skill in re.findall(r"[\w-]+", fm.get("skills", "")):
                self.assertIn(skill, skill_names, f"{path.name} preloads unknown skill {skill}")


class TestGuard(unittest.TestCase):
    def guard(self, mode, tool_input):
        p = subprocess.run([sys.executable, str(ROOT / "hooks/scripts/guard.py"), mode],
                           input=json.dumps({"tool_input": tool_input}), capture_output=True, text=True)
        return p.returncode

    def test_blocks_irreversible_commands(self):
        for cmd in ["git push origin main", "git push -f", "git reset --hard HEAD~1", "rm -rf /",
                    "rm data/raw/a.csv", "dvc push"]:
            self.assertEqual(self.guard("bash", {"command": cmd}), 2, cmd)

    def test_blocks_git_with_global_options(self):
        for cmd in ["git -C ../wt push origin main", "git -c user.name=x push", "git -C /p/wt reset --hard HEAD",
                    "git -C wt clean -fd"]:
            self.assertEqual(self.guard("bash", {"command": cmd}), 2, cmd)

    def ask_reason(self, cmd):
        p = subprocess.run([sys.executable, str(ROOT / "hooks/scripts/guard.py"), "bash"],
                           input=json.dumps({"tool_input": {"command": cmd}}), capture_output=True, text=True)
        if p.returncode != 0 or not p.stdout.strip():
            return None
        out = json.loads(p.stdout)["hookSpecificOutput"]
        return out["permissionDecision"]

    def test_human_approval_actions_force_a_prompt(self):
        for cmd in ["make rebaseline", "make -C wt rebaseline", "make promote APPROVE=1", "make rollback",
                    "uv run python -m pkg.registry.promote --config c --approve", "uv add polars",
                    "make bundle-deploy TARGET=prod", "make bundle-promote-approve"]:
            self.assertEqual(self.ask_reason(cmd), "ask", cmd)
        for cmd in ["make promote", "make -C wt check", "git -C wt status", "make bundle-deploy TARGET=dev"]:
            self.assertIsNone(self.ask_reason(cmd), cmd)

    def test_allows_normal_work(self):
        for cmd in ["make check", "uv run pytest -q", "git commit -m 'T-1: x'", "git worktree add ../w -b task/T-1"]:
            self.assertEqual(self.guard("bash", {"command": cmd}), 0, cmd)

    def test_protects_paths(self):
        for path in ["/p/.env", "/p/data/raw/x.csv", "/p/metrics/baseline.json", "/p/configs/gates.json"]:
            self.assertEqual(self.guard("files", {"file_path": path}), 2, path)
        self.assertEqual(self.guard("files", {"file_path": "/p/src/pkg/model.py"}), 0)


class TestScaffolder(unittest.TestCase):
    def test_new_project_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp) / "churn"
            run("new", str(proj), "--name", "churn-model")
            for rel in ["AGENTS.md", "CLAUDE.md", "Makefile", "src/churn_model/models/train.py",
                        ".claude/agents/orchestrator.md", ".claude/hooks/guard.py",
                        ".agents/skills/worker-protocol/SKILL.md", "tasks/BOARD.md",
                        "scripts/agent-team/run-wave.sh", "scripts/agent-team/audit.py",
                        "docs/pipeline-map/README.md", "docs/pipeline-map/training.md",
                        ".agents/skills/prove-it-works/SKILL.md", ".agents/playbook.lock.json"]:
                self.assertTrue((proj / rel).exists(), rel)
            self.assertTrue((proj / ".claude/skills").is_symlink())
            self.assertNotIn("{{", (proj / "AGENTS.md").read_text())
            self.assertNotIn("__pkg__", "".join(str(p) for p in proj.rglob("*")))
            settings = json.loads((proj / ".claude/settings.json").read_text())
            self.assertIn("Bash(make gate)", settings["permissions"]["allow"])
            self.assertIn(".audit/", (proj / ".gitignore").read_text())
            self.assertNotIn("{{", (proj / "docs/pipeline-map/batch-scoring.md").read_text())
            team = json.loads((proj / "configs/team.json").read_text())
            self.assertEqual(team["trust"]["start_workers"], 1)
            log = subprocess.run(["git", "-C", str(proj), "log", "--oneline"], capture_output=True, text=True)
            self.assertIn("Scaffold churn-model", log.stdout)

    def test_task_type_routes_to_an_existing_evaluator(self):
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp) / "fc"
            run("new", str(proj), "--name", "fc", "--task-type", "forecasting")
            self.assertIn("task_type: forecasting", (proj / "configs/base.yaml").read_text())
            team = json.loads((proj / "configs/team.json").read_text())
            for agent in team["evaluators"].values():
                self.assertTrue((proj / ".claude/agents" / f"{agent}.md").exists(), agent)

    def test_databricks_platform_overlay(self):
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp) / "dbx"
            run("new", str(proj), "--name", "churn-dbx", "--platform", "databricks", "--catalog", "ml", "--schema", "churn")
            for rel in ["databricks.yml", "resources/train.job.yml", "resources/monitor.job.yml",
                        "resources/promote.job.yml", "configs/databricks.yaml", "Makefile.databricks",
                        "scripts/databricks/setup-agents.sh"]:
                self.assertTrue((proj / rel).exists(), rel)
            text = "".join((proj / f).read_text() for f in ["databricks.yml", "configs/databricks.yaml", ".mcp.json",
                                                            "resources/train.job.yml", "AGENTS.md"])
            self.assertNotIn("{{", text)
            self.assertIn("ml.churn.churn_dbx", (proj / "configs/databricks.yaml").read_text())
            self.assertIn('"databricks"', (proj / ".mcp.json").read_text())  # overlay replaced the local MCP config
            self.assertIn("## Databricks", (proj / "AGENTS.md").read_text())
            self.assertIn("churn_dbx-train", (proj / "pyproject.toml").read_text())  # wheel entry points for jobs
            self.assertIn("churn_dbx-train", (proj / "resources/train.job.yml").read_text())

    def test_local_platform_has_no_databricks_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp) / "loc"
            run("new", str(proj), "--name", "loc")
            self.assertFalse((proj / "databricks.yml").exists())
            self.assertIn("sqlite", (proj / ".mcp.json").read_text())

    def test_genie_code_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            run("init", tmp, "--name", "g", "--target", "genie-code")
            out = Path(tmp) / "genie-code"
            skills = {p.name for p in (out / ".assistant/skills").iterdir()}
            self.assertFalse(skills & {"orchestrate-team", "worker-protocol", "merge-train"})
            self.assertIn("verify-before-done", skills)
            for skill_md in (out / ".assistant/skills").glob("*/SKILL.md"):
                text = skill_md.read_text()
                self.assertTrue(text.startswith("---\nname: "), skill_md)  # frontmatter still first
                if "make " in text:
                    self.assertIn("On Databricks Genie Code", text, skill_md)
            self.assertIn("Genie Code note", (out / "AGENTS.md").read_text())
            self.assertTrue((out / "upload.sh").exists())
            self.assertFalse((Path(tmp) / ".claude").exists())  # repo setup not touched

    def test_run_wave_supports_ug_runners(self):
        text = (ROOT / "templates/agent-config/scripts/agent-team/run-wave.sh").read_text()
        self.assertIn('ug claude -p "$prompt"', text)
        self.assertIn('ug codex exec', text)

    def test_init_preserves_existing_files_and_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "AGENTS.md").write_text("# mine\n")
            (repo / ".claude").mkdir()
            (repo / ".claude/settings.json").write_text('{"model": "opus", "permissions": {"allow": ["Bash(x)"]}}')
            run("init", str(repo), "--name", "legacy")
            self.assertEqual((repo / "AGENTS.md").read_text(), "# mine\n")
            self.assertTrue((repo / "AGENTS.playbook.md").exists())
            settings = json.loads((repo / ".claude/settings.json").read_text())
            self.assertEqual(settings["model"], "opus")
            self.assertIn("Bash(x)", settings["permissions"]["allow"])
            self.assertNotIn("hooks", settings)  # guardrails are opt-in for existing repos
            self.assertNotIn("Bash(git -C:*)", settings["permissions"]["allow"])  # only safe with the guard
            self.assertFalse((repo / "CLAUDE.md").exists())  # never created or edited without --link
            self.assertFalse((repo / "configs").exists())  # ML extras only with --profile ml

    def test_init_opt_ins(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "CLAUDE.md").write_text("# my rules\n")
            run("init", str(repo), "--profile", "ml", "--guardrails", "--link")
            settings = json.loads((repo / ".claude/settings.json").read_text())
            self.assertIn("PreToolUse", settings["hooks"])
            self.assertIn("Bash(git -C:*)", settings["permissions"]["allow"])
            self.assertTrue((repo / "docs/pipeline-map/README.md").exists())
            claude = (repo / "CLAUDE.md").read_text()
            self.assertTrue(claude.startswith("# my rules\n") and claude.count("@AGENTS.playbook.md") == 1)
            run("init", str(repo), "--profile", "ml", "--guardrails", "--link")  # idempotent
            self.assertEqual((repo / "CLAUDE.md").read_text(), claude)

    def test_init_keeps_existing_claude_skills_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".claude/skills/mine").mkdir(parents=True)
            (repo / ".claude/skills/mine/SKILL.md").write_text("---\nname: mine\ndescription: x\n---\n")
            run("init", str(repo))
            self.assertFalse((repo / ".claude/skills").is_symlink())
            self.assertTrue((repo / ".claude/skills/mine/SKILL.md").exists())
            self.assertTrue((repo / ".claude/skills/tdd-loop/SKILL.md").exists())

    def test_plugin_mode_enables_plugin_instead_of_vendoring_agents(self):
        with tempfile.TemporaryDirectory() as tmp:
            run("init", tmp, "--mode", "plugin")
            settings = json.loads((Path(tmp) / ".claude/settings.json").read_text())
            self.assertTrue(settings["enabledPlugins"]["agent-playbook@mj2tang"])
            self.assertFalse((Path(tmp) / ".claude/agents").exists())
            self.assertTrue((Path(tmp) / ".agents/skills/tdd-loop/SKILL.md").exists())  # Codex still gets skills

    def test_sync_is_idempotent_and_keeps_local_edits(self):
        with tempfile.TemporaryDirectory() as tmp:
            run("init", tmp)
            self.assertIn("0 created, 0 updated, 0 skipped", run("sync", tmp))
            skill = Path(tmp) / ".agents/skills/tdd-loop/SKILL.md"
            skill.write_text(skill.read_text() + "\nlocal rule\n")
            out = run("sync", tmp)
            self.assertIn("1 skipped", out)
            self.assertIn("local rule", skill.read_text())


if __name__ == "__main__":
    unittest.main()
