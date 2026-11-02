---
name: decision-log
description: Keep a reviewable decision trail for team, long-running, or unattended work - one TSV row per decision point (dispatch, verdict, merge, revert, pivot, blocker) with why, an evidence pointer, and a result, written with scripts/agent-team/audit.py. The trail also drives the trust ladder that sets how many workers may run in parallel. Use during any orchestrated run, overnight run, or work a human reviews later. Not for one-off interactive edits.
---

# Decision log

A human reviewing after the fact should be able to reconstruct what was decided, why, and on what evidence - without rereading the transcript or rerunning the work.

## Write a row
```
python3 scripts/agent-team/audit.py log <phase> <task> <actor> <decision> <why> <evidence> <result>
```
- **phase**: plan, dispatch, verify, review, merge, monitor, pause, ...
- **evidence**: a pointer - commit SHA, `file:line`, artifact path, MLflow run ID. Never a paragraph.
- **result**: use these words exactly when they apply, because the trust ladder reads them:
  `approved` (supervisor approved on the first round, no human rework) · `approved_after_rework` (approved in a later round; neutral for trust) · `changes_requested` · `merged` · `reverted` · `human_rework` (a human had to fix or redo agent work) · `blocked` · `progress` / `no_progress` (autonomous-run iterations) · or a short predicate state (`GATE: PASS`, `pixel-diff 0`).

Run it from the project root with the relative path `python3 scripts/agent-team/audit.py ...` (absolute paths don't match the permission rules). Plain words, as you'd tell a teammate. One row per decision point, not per command.

## Who logs what
| Actor | Rows |
|---|---|
| orchestrator | plan, dispatch, wave summary, escalations, `human_rework` when the user corrects merged work |
| worker | verify rows (one per pipeline-map entry point), blockers |
| supervisor | `approved` or `changes_requested` per review |
| merge train | `merged` or `reverted` per branch |

## Read it
`python3 scripts/agent-team/audit.py show --last 30` · `python3 scripts/agent-team/audit.py trust --explain`

## Where it lives
`.audit/decisions.tsv`, git-ignored by default. Commit a copy (e.g. `docs/runs/<epic>.tsv`) when the run is large or unattended enough that reviewers need the trail to trust it.

Adapted from the show-me-your-work skill in Lauren Tan's pstack.
