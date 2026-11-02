#!/usr/bin/env bash
# Upload this bundle's skills to Databricks Genie Code.
#   ./upload.sh user        -> /Users/<you>/.assistant/skills   (personal skills)
#   ./upload.sh workspace   -> Workspace/.assistant/skills       (shared; workspace admins)
#   DEST=/Users/me/my-skills ./upload.sh   (custom folder; register it in Genie Code settings)
# Requires the Databricks CLI, authenticated (databricks auth login).
set -euo pipefail
cd "$(dirname "$0")"
SCOPE=${1:-user}
if [ -z "${DEST:-}" ]; then
  case "$SCOPE" in
    user)
      ME=$(databricks current-user me --output json | python3 -c 'import json,sys; print(json.load(sys.stdin)["userName"])')
      DEST="/Users/$ME/.assistant/skills" ;;
    workspace) DEST="/Workspace/.assistant/skills" ;;
    *) echo "usage: $0 [user|workspace]"; exit 1 ;;
  esac
fi
echo "Uploading .assistant/skills -> $DEST"
databricks workspace mkdirs "$DEST"
databricks workspace import-dir .assistant/skills "$DEST" --overwrite
echo "Done. Start a new Genie Code chat (Agent mode); skills load by description or with @<skill-name>."
