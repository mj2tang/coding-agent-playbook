from datetime import datetime, timedelta, timezone

from {{pkg}}.monitoring.retrain import RetrainPolicy, decide_retrain

NOW = datetime(2026, 1, 31, tzinfo=timezone.utc)


def test_no_trigger():
    d = decide_retrain(
        RetrainPolicy(), dataset_drift=False, model_trained_at=NOW - timedelta(days=1), now=NOW
    )
    assert not d.retrain and d.reasons == []


def test_each_trigger_reports_a_reason():
    p = RetrainPolicy(max_model_age_days=30, max_metric_drop=0.02)
    assert decide_retrain(p, dataset_drift=True, model_trained_at=NOW, now=NOW).reasons == [
        "dataset drift detected"
    ]
    old = decide_retrain(p, dataset_drift=False, model_trained_at=NOW - timedelta(days=45), now=NOW)
    assert old.retrain and "age" in old.reasons[0]
    perf = decide_retrain(
        p,
        dataset_drift=False,
        model_trained_at=NOW,
        now=NOW,
        champion_metric=0.90,
        current_metric=0.85,
    )
    assert perf.retrain and "dropped" in perf.reasons[0]


def test_lower_is_better_metrics():
    p = RetrainPolicy(max_metric_drop=0.01)
    d = decide_retrain(
        p,
        dataset_drift=False,
        model_trained_at=NOW,
        now=NOW,
        champion_metric=0.30,
        current_metric=0.35,
        higher_is_better=False,
    )
    assert d.retrain
