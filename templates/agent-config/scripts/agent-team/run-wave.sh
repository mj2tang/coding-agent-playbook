#!/usr/bin/env bash
# Run several board tasks in parallel, headless, one git worktree per task.
#   scripts/agent-team/run-wave.sh T-001 T-002 T-003
# Runner: claude (default), codex, ug-claude, or ug-codex — set RUNNER=... or configs/team.json "headless_runner".
# ug-* runners launch the agent through Databricks Unity AI Gateway (`ug`), which forwards the extra
# arguments to the agent, so model routing, rate limits, and usage tracking come from the gateway.
# Each worker follows the worker-protocol skill; review with the supervisor before merging.
set -euo pipefail
# Headless Claude ignores the project's permissions.allow rules until the folder has been trusted:
# run `claude` interactively in this project once and accept the trust dialog before using this script.

ROOT=$(git rev-parse --show-toplevel)
cd "$ROOT"
RUNNER=${RUNNER:-$(python3 -c 'import json;print(json.load(open("configs/team.json")).get("headless_runner","claude"))' 2>/dev/null || echo claude)}
BASE=${BASE:-$(python3 -c 'import json;print(json.load(open("configs/team.json")).get("integration_branch","main"))' 2>/dev/null || echo main)}
WT_DIR=${WT_DIR:-"$ROOT/../$(basename "$ROOT")-worktrees"}
LOG_DIR="$ROOT/.agent-logs"
mkdir -p "$WT_DIR" "$LOG_DIR"

[ $# -gt 0 ] || { echo "usage: $0 T-001 [T-002 ...]"; exit 1; }
# Trust ladder: parallelism is earned from the decision trail (scripts/agent-team/audit.py trust).
ALLOWED=$(python3 "$ROOT/scripts/agent-team/audit.py" trust 2>/dev/null || echo 1)
if [ "$#" -gt "$ALLOWED" ] && [ "${FORCE:-0}" = "1" ]; then
  python3 "$ROOT/scripts/agent-team/audit.py" log dispatch "$*" "run-wave" "forced wave of $# over trust limit $ALLOWED" \
    "FORCE=1 set by the operator" "run-wave.sh" forced || true
fi
if [ "$#" -gt "$ALLOWED" ] && [ "${FORCE:-0}" != "1" ]; then
  echo "Trust ladder allows $ALLOWED parallel worker(s); got $# tasks."
  echo "Run fewer tasks, see 'python3 scripts/agent-team/audit.py trust --explain', or override with FORCE=1."
  exit 1
fi
case "$RUNNER" in ug-*) command -v ug >/dev/null || { echo "RUNNER=$RUNNER needs the Unity Gateway CLI: uv tool install git+https://github.com/databricks/unity-gateway"; exit 1; } ;; esac

# Headless runs ignore the project's permissions.allow until the folder is trusted interactively.
# ALLOW_FROM_SETTINGS=1 passes that allow list to each claude worker instead - only for repos you trust.
ALLOW_ARGS=()
if [ "${ALLOW_FROM_SETTINGS:-0}" = "1" ] && [ -f "$ROOT/.claude/settings.json" ]; then
  while IFS= read -r rule; do ALLOW_ARGS+=("$rule"); done < <(python3 -c \
    "import json,sys; print('\\n'.join(json.load(open(sys.argv[1])).get('permissions', {}).get('allow', [])))" \
    "$ROOT/.claude/settings.json")
  ALLOW_ARGS=(--allowedTools Read Edit Write Glob Grep "${ALLOW_ARGS[@]}")
fi

# Codex's workspace-write sandbox keeps .git read-only (worktrees included), so codex workers can't commit:
# the runner commits each worker's owned files after it exits. CODEX_APPROVE_FOR_ME=1 instead lets Codex
# escalate blocked commands (git commit, ...) through its automatic reviewer - only for repos you trust.
CODEX_ARGS=(--sandbox workspace-write)
[ "${CODEX_APPROVE_FOR_ME:-0}" = "1" ] && CODEX_ARGS=(--approve-for-me)
# uv's cache lives outside the worktree; without write access `uv run` fails inside the sandbox.
if command -v uv >/dev/null; then CODEX_ARGS+=(--add-dir "$(uv cache dir)"); fi
CODEX_NOTE="Codex sandbox: .git is read-only, so don't commit. Leave your changes in the working tree; this runner
commits your owned files when you exit and the supervisor runs the proof on that commit."
[ "${CODEX_APPROVE_FOR_ME:-0}" = "1" ] && CODEX_NOTE=""

# Commit a codex worker's owned files (task front matter) plus its task file; report anything left outside scope.
commit_owned() {
  local wt=$1 task=$2 id=$3 paths
  paths=$(python3 - "$wt/$task" <<'PY'
import re, sys
text = open(sys.argv[1]).read()
fm = text.split("---", 2)[1] if text.startswith("---") else ""
m = re.search(r"^owned_files:[ \t]*\n((?:[ \t]+-[ \t].*\n?)*)", fm, re.M)
for line in m.group(1).splitlines() if m else []:
    print(line.split("-", 1)[1].split(" #")[0].strip())
PY
)
  while IFS= read -r p; do
    [ -n "$p" ] && git -C "$wt" add -A -- "$p" 2>/dev/null || true
  done <<<"$task"$'\n'"$paths"
  if git -C "$wt" diff --cached --quiet; then
    echo "run-wave: nothing to commit for $id"
  else
    git -C "$wt" commit -q -m "$id: worker changes (committed by run-wave for codex)" && \
      echo "run-wave: committed $(git -C "$wt" rev-parse --short HEAD) for $id"
  fi
  local rest
  rest=$(git -C "$wt" status --porcelain)
  [ -z "$rest" ] || printf 'run-wave: left uncommitted (outside owned_files):\n%s\n' "$rest"
}

# Logs stay local whether or not the repo's .gitignore knows about them.
[ -f "$LOG_DIR/.gitignore" ] || echo '*' >"$LOG_DIR/.gitignore"

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
  # Sync the worktree's env here: sandboxed workers (codex) have no network to build it themselves.
  if [ -f "$wt/uv.lock" ] && command -v uv >/dev/null; then
    (cd "$wt" && uv sync --frozen -q) || echo "warning: uv sync failed in $wt; the worker may not be able to run gates"
  fi
  prompt="You are a worker on this ML project's agent team. Follow the worker-protocol skill exactly.
Task file: $task. Branch: $branch (already checked out in this worktree).
Gate: make check, plus make data-check / make gate if the task touches data or models.
Do not push. Finish with the worker-protocol summary block."
  echo "▶ $id → $wt ($RUNNER)"
  python3 "$ROOT/scripts/agent-team/audit.py" log dispatch "$id" "run-wave:$RUNNER" "dispatched $branch" "wave of $# (trust limit $ALLOWED$([ "$#" -gt "$ALLOWED" ] && echo ", forced"))" "$wt" started || true
  case "$RUNNER" in
    claude) (cd "$wt" && claude -p "$prompt" --permission-mode acceptEdits ${ALLOW_ARGS[@]+"${ALLOW_ARGS[@]}"} >"$LOG_DIR/$slug.log" 2>&1) & ;;
    codex)  (cd "$wt"; rc=0; codex exec "${CODEX_ARGS[@]}" "$prompt
$CODEX_NOTE" >"$LOG_DIR/$slug.log" 2>&1 || rc=$?
             commit_owned "$wt" "$task" "$id" >>"$LOG_DIR/$slug.log" 2>&1; exit $rc) & ;;
    ug-claude) (cd "$wt" && ug claude -p "$prompt" --permission-mode acceptEdits ${ALLOW_ARGS[@]+"${ALLOW_ARGS[@]}"} >"$LOG_DIR/$slug.log" 2>&1) & ;;
    ug-codex)  (cd "$wt"; rc=0; ug codex exec "${CODEX_ARGS[@]}" "$prompt
$CODEX_NOTE" >"$LOG_DIR/$slug.log" 2>&1 || rc=$?
                commit_owned "$wt" "$task" "$id" >>"$LOG_DIR/$slug.log" 2>&1; exit $rc) & ;;
    *) echo "unknown RUNNER=$RUNNER"; exit 1 ;;
  esac
  pids+=($!)
done

fail=0
for pid in "${pids[@]}"; do wait "$pid" || fail=1; done
echo "Wave finished (logs in $LOG_DIR). Next: review each branch with the supervisor, then merge-train."
exit $fail
