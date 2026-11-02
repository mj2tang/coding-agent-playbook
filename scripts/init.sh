#!/usr/bin/env bash
# One-line installer:
#   curl -fsSL https://raw.githubusercontent.com/mj2tang/coding-agent-playbook/main/scripts/init.sh | bash -s -- new my-ml-project --name my-ml-project --bootstrap
#   curl -fsSL .../init.sh | bash -s -- init .            # add the agent team to an existing repo
# Arguments are passed straight to scripts/playbook.py (new | init | sync).
set -euo pipefail
REPO=${PLAYBOOK_REPO:-https://github.com/mj2tang/coding-agent-playbook.git}
REF=${PLAYBOOK_REF:-main}
command -v python3 >/dev/null || { echo "python3 is required"; exit 1; }
command -v git >/dev/null || { echo "git is required"; exit 1; }
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
git clone -q --depth 1 --branch "$REF" "$REPO" "$TMP/playbook"
python3 "$TMP/playbook/scripts/playbook.py" "$@"
