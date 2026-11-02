# Batch scoring

## What it is
Downstream consumers load `models:/{{pkg}}@champion` and score a batch. Replace this file with your real consumer (job, table, API) when you have one.

## How to reach it
- `uv run python -c "import mlflow; m = mlflow.sklearn.load_model('models:/{{pkg}}@champion'); print(m)"` with the project's tracking URI, then score a sample batch.

## Evidence that counts
- Predictions on a known batch: row count in = row count out, score range sane, and the same features the training path used (no train/serve skew).

## What usually lies
- Scoring with features computed by different code than training — compare a few feature rows from both paths.
- Loading a version number instead of the alias — after promotion, consumers silently stay on the old model.
