#!/usr/bin/env bash
# Connect this project's coding agents to Databricks through Unity Gateway (`ug`).
#   scripts/databricks/setup-agents.sh                 # interactive pickers
#   CATALOG=main SCHEMA=ml scripts/databricks/setup-agents.sh
# Databricks-managed MCP servers and Unity Catalog skills are governed by UC permissions.
# Several of these features are in beta and need an admin to enable them (see docs/databricks.md).
set -euo pipefail
command -v ug >/dev/null || { echo "Install ug: uv tool install git+https://github.com/databricks/unity-gateway"; exit 1; }
CATALOG=${CATALOG:-{{catalog}}}
SCHEMA=${SCHEMA:-{{schema}}}

echo "1/3 Official Databricks platform skills (bundles, jobs, UC, MLflow, serving)"
if command -v databricks >/dev/null; then
  databricks aitools install --agents claude-code || echo "  (skipped: run 'databricks aitools install' manually)"
else
  echo "  databricks CLI not found; install it, then run: databricks aitools install"
fi

echo "2/3 Databricks-managed MCP servers (SQL + this schema's UC functions)"
ug mcp add --names "system.ai.dbsql,uc-functions:${CATALOG}.${SCHEMA}" || ug mcp add

echo "3/3 Team skills published to Unity Catalog in ${CATALOG}.${SCHEMA} (if any), into this project"
ug skills add --location "${CATALOG}.${SCHEMA}" --path "$PWD" || echo "  (no published skills found; see docs/databricks.md to publish)"

echo "Done. Start the team through the gateway with: ug claude --agent orchestrator"
