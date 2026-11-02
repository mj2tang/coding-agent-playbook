# Training and registration

## What it is
`make train` fits on the train split and registers a new MLflow model version.

## How to reach it
- `make train CONFIG=configs/base.yaml` (local); bundle job `train` on Databricks.
- `make tune` writes a tuned config that later feeds `make train`.

## Evidence that counts
- The MLflow run ID and registered version printed by `make train`, with params matching the config.
- Valid-split metrics logged on that run.

## What usually lies
- A model trained in a notebook or an earlier session — check the run's `git_sha` tag equals HEAD.
- "Training finished" while the registered version is an older one — read the printed version number.
