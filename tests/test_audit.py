"""Decision trail + trust ladder (templates/agent-config/scripts/agent-team/audit.py) and run-wave enforcement."""

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUDIT = ROOT / "templates/agent-config/scripts/agent-team/audit.py"
spec = importlib.util.spec_from_file_location("audit", AUDIT)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

SETTINGS = {"start_workers": 1, "max_workers": 3, "promote_after": 2}


def rows(*results):
    return [{"ts": f"t{i}", "task": f"T-{i}", "result": r} for i, r in enumerate(results)]


class TestTrustLadder(unittest.TestCase):
    def test_starts_low_and_is_earned(self):
        self.assertEqual(audit.trust_level([], SETTINGS)[0], 1)
        self.assertEqual(audit.trust_level(rows("approved"), SETTINGS)[0], 1)
        self.assertEqual(audit.trust_level(rows("approved", "approved"), SETTINGS)[0], 2)
        self.assertEqual(audit.trust_level(rows(*["approved"] * 10), SETTINGS)[0], 3)  # capped

    def test_changes_requested_resets_streak_and_failures_demote(self):
        self.assertEqual(audit.trust_level(rows("approved", "changes_requested", "approved"), SETTINGS)[0], 1)
        level, streak, why = audit.trust_level(rows("approved", "approved", "approved", "approved", "reverted"), SETTINGS)
        self.assertEqual((level, streak), (2, 0))
        self.assertIn("reverted", why[-1])
        self.assertEqual(audit.trust_level(rows("human_rework"), SETTINGS)[0], 1)  # never below start
        self.assertEqual(audit.trust_level(rows("merged", "GATE: PASS"), SETTINGS)[0], 1)  # neutral rows

    def test_settings_from_team_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "team.json"
            p.write_text(json.dumps({"max_parallel_workers": 4, "trust": {"start_workers": 2, "promote_after": 5, "_doc": "x"}}))
            self.assertEqual(audit.trust_settings(p), {"start_workers": 2, "max_workers": 4, "promote_after": 5})
            p.write_text(json.dumps({"max_parallel_workers": 1, "trust": {"start_workers": 2}}))
            with self.assertRaises(ValueError):
                audit.trust_settings(p)


class TestDecisionLog(unittest.TestCase):
    def test_append_read_and_sanitise(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / ".audit/decisions.tsv"
            audit.append({"ts": "t", "phase": "review", "task": "T-1", "actor": "supervisor",
                          "decision": "approve\twith\nnewline", "why": "=SUM(A1)", "evidence": "abc123",
                          "result": "approved"}, log)
            audit.append({"ts": "t2", "phase": "merge", "task": "T-1", "result": "merged"}, log)
            got = audit.read(log)
            self.assertEqual(len(got), 2)
            self.assertEqual(got[0]["decision"], "approve with newline")
            self.assertEqual(got[0]["why"], "'=SUM(A1)")  # formula neutralised
            self.assertEqual(log.read_text().splitlines()[0].split("\t"), audit.COLUMNS)

    def test_cli_log_and_trust(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = {**os.environ, "AUDIT_LOG": str(Path(tmp) / "d.tsv")}
            for _ in range(3):
                subprocess.run([sys.executable, str(AUDIT), "log", "review", "T-1", "supervisor", "ok", "fine", "sha", "approved"],
                               cwd=tmp, env=env, check=True)
            out = subprocess.run([sys.executable, str(AUDIT), "trust"], cwd=tmp, env=env, check=True,
                                 capture_output=True, text=True).stdout.strip()
            self.assertEqual(out, "2")  # defaults: start 1, +1 after 3 clean approvals


class TestSharedTrailAcrossWorktrees(unittest.TestCase):
    def test_rows_from_a_worktree_land_in_the_main_trail(self):
        with tempfile.TemporaryDirectory() as tmp:
            main = Path(tmp) / "main"
            main.mkdir()
            git = ["git", "-c", "user.name=t", "-c", "user.email=t@t"]
            subprocess.run([*git, "init", "-q", "-b", "main", str(main)], check=True)
            subprocess.run([*git, "-C", str(main), "commit", "-q", "--allow-empty", "-m", "i"], check=True)
            wt = Path(tmp) / "wt"
            subprocess.run([*git, "-C", str(main), "worktree", "add", "-q", str(wt), "-b", "task/x"], check=True)
            env = {k: v for k, v in os.environ.items() if k != "AUDIT_LOG"}
            for cwd in (wt, main):
                subprocess.run([sys.executable, str(AUDIT), "log", "verify", "T-1", "worker", "d", "w", "e",
                                "GATE: PASS"], cwd=cwd, env=env, check=True)
            self.assertEqual(len(audit.read(main / ".audit/decisions.tsv")), 2)
            self.assertFalse((wt / ".audit").exists())


class TestRunWaveEnforcement(unittest.TestCase):
    def test_refuses_wave_larger_than_trust(self):
        with tempfile.TemporaryDirectory() as tmp:
            proj = Path(tmp) / "p"
            subprocess.run([sys.executable, str(ROOT / "scripts/playbook.py"), "new", str(proj), "--name", "p"],
                           check=True, capture_output=True)
            for i in (1, 2):
                (proj / f"tasks/T-00{i}-x.md").write_text("---\nid: T-00%d\n---\n" % i)
            r = subprocess.run(["bash", "scripts/agent-team/run-wave.sh", "T-001", "T-002"], cwd=proj,
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 1)
            self.assertIn("Trust ladder allows 1", r.stdout)
            wt = proj.parent / "p-worktrees"
            self.assertFalse(wt.exists() and any(wt.iterdir()))  # nothing dispatched


if __name__ == "__main__":
    unittest.main()
