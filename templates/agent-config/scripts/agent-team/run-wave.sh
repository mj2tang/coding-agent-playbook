#!/usr/bin/env bash
# Run several board tasks in parallel, headless, one git worktree per task.
#   scripts/agent-team/run-wave.sh T-001 T-002 T-003
# Runner: claude (default) or codex — set RUNNER=codex or configs/team.json "headless_runner".
# Each worker follows the worker-protocol skill; review with the supervisor before merging.
set -euo pipefail

ROOT=$(git rev-parse --show-toplevel)
cd "$ROOT"
RUNNER=${RUNNER:-$(python3 -c 'import json;print(json.load(open("configs/team.json")).get("headless_runner","claude"))' 2>/dev/null || echo claude)}
BASE=${BASE:-$(python3 -c 'import json;print(json.load(open("configs/team.json")).get("integration_branch","main"))' 2>/dev/null || echo main)}
WT_DIR=${WT_DIR:-"$ROOT/../$(basename "$ROOT")-worktrees"}
LOG_DIR="$ROOT/.agent-logs"
mkdir -p "$WT_DIR" "$LOG_DIR"

[ $# -gt 0 ] || { echo "usage: $0 T-001 [T-002 ...]"; exit 1; }

pids=()
for id in "$@"; do
  task=$(ls tasks/"$id"-*.md 2>/dev/null | head -1) || true
  [ -n "${task:-}" ] || { echo "no task file for $id"; exit 1; }
  slug=$(basename "$task" .md)
  branch="task/$slug"
  wt="$WT_DIR/$slug"
  if [ ! -d "$wt" ]; then
    git worktree add -q "$wt" -b "$branch" "$BASE" 2>/dev/null || git worktree add -q "$wt" "$branch"
  fi
  prompt="You are a worker on this ML project's agent team. Follow the worker-protocol skill exactly.
Task file: $task. Branch: $branch (already checked out in this worktree).
Gate: make check, plus make data-check / make gate if the task touches data or models.
Do not push. Finish with the worker-protocol summary block."
  echo "▶ $id → $wt ($RUNNER)"
  case "$RUNNER" in
    claude) (cd "$wt" && claude -p "$prompt" --permission-mode acceptEdits >"$LOG_DIR/$slug.log" 2>&1) & ;;
    codex)  (cd "$wt" && codex exec --sandbox workspace-write "$prompt" >"$LOG_DIR/$slug.log" 2>&1) & ;;
    *) echo "unknown RUNNER=$RUNNER"; exit 1 ;;
  esac
  pids+=($!)
done

fail=0
for pid in "${pids[@]}"; do wait "$pid" || fail=1; done
echo "Wave finished (logs in $LOG_DIR). Next: review each branch with the supervisor, then merge-train."
exit $fail
