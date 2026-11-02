from {{pkg}}.config import deep_merge, load_config


def test_deep_merge_overrides_nested_keys_only():
    base = {"a": 1, "m": {"x": 1, "y": 2}}
    assert deep_merge(base, {"m": {"y": 3}}) == {"a": 1, "m": {"x": 1, "y": 3}}
    assert base["m"]["y"] == 2  # input not mutated


def test_extends_inherits_from_parent(tmp_path):
    (tmp_path / "base.yaml").write_text("seed: 1\ndata:\n  source: a\n  valid_size: 0.2\n")
    (tmp_path / "child.yaml").write_text("extends: base.yaml\ndata:\n  source: b\n")
    cfg = load_config(tmp_path / "child.yaml")
    assert cfg == {"seed": 1, "data": {"source": "b", "valid_size": 0.2}}


def test_set_overrides_parse_yaml_values(tmp_path):
    (tmp_path / "c.yaml").write_text("model:\n  C: 1.0\nmlflow:\n  registered_model: m\n")
    cfg = load_config(
        tmp_path / "c.yaml", ["model.C=0.5", "mlflow.registered_model=main.ml.m", "new.flag=true"]
    )
    assert (
        cfg["model"]["C"] == 0.5
        and cfg["mlflow"]["registered_model"] == "main.ml.m"
        and cfg["new"]["flag"] is True
    )
