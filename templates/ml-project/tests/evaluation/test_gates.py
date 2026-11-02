from {{pkg}}.evaluation.gates import compare_metrics

RULES = {
    "auc": {"direction": "higher", "tolerance": 0.01, "suspicious_gain": 0.05},
    "loss": {"direction": "lower", "tolerance": 0.01},
}


def test_within_tolerance_passes():
    ok, rows = compare_metrics({"auc": 0.895, "loss": 0.305}, {"auc": 0.90, "loss": 0.30}, RULES)
    assert ok and all(r.status == "ok" for r in rows)


def test_regressions_in_either_direction_fail():
    assert not compare_metrics({"auc": 0.85, "loss": 0.30}, {"auc": 0.90, "loss": 0.30}, RULES)[0]
    assert not compare_metrics({"auc": 0.90, "loss": 0.40}, {"auc": 0.90, "loss": 0.30}, RULES)[0]


def test_suspicious_gain_warns_but_passes_and_missing_fails():
    ok, rows = compare_metrics({"auc": 0.99, "loss": 0.30}, {"auc": 0.90, "loss": 0.30}, RULES)
    assert ok and rows[0].status == "SUSPICIOUS GAIN"
    assert not compare_metrics({"auc": 0.9}, {"auc": 0.9, "loss": 0.3}, RULES)[0]
