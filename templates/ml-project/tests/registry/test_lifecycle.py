"""End-to-end MLflow lifecycle on a temporary tracking store: train -> register -> promote -> rollback."""

import sys

import pytest
from mlflow import MlflowClient

from {{pkg}}.models.train import train_and_register
from {{pkg}}.registry import promote

pytestmark = pytest.mark.mlflow


@pytest.fixture
def mlflow_cfg(cfg, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg["mlflow"] = {
        "tracking_uri": f"sqlite:///{tmp_path}/mlflow.db",
        "experiment": "test",
        "registered_model": "m",
    }
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs/gates.json").write_text(
        '{"metrics": {"roc_auc": {"direction": "higher", "tolerance": 0.002}}}'
    )
    monkeypatch.setattr(promote, "load_config", lambda _: cfg)
    return cfg


def run_promote(monkeypatch, *args):
    monkeypatch.setattr(sys, "argv", ["promote", "--config", "x", *args])
    return promote.main()


def test_train_register_promote_and_rollback(mlflow_cfg, monkeypatch):
    client = MlflowClient()
    v1 = train_and_register(mlflow_cfg, "x")
    assert run_promote(monkeypatch, "--approve") == 0
    assert str(client.get_model_version_by_alias("m", "champion").version) == v1

    mlflow_cfg["model"]["C"] = 0.0005  # a much weaker challenger
    train_and_register(mlflow_cfg, "x")
    assert run_promote(monkeypatch, "--approve") == 1  # blocked by the gate
    assert str(client.get_model_version_by_alias("m", "champion").version) == v1

    mlflow_cfg["model"]["C"] = 1.0
    v3 = train_and_register(mlflow_cfg, "x")
    assert run_promote(monkeypatch, "--approve") == 0
    assert str(client.get_model_version_by_alias("m", "champion").version) == v3
    assert run_promote(monkeypatch, "--rollback") == 0
    assert str(client.get_model_version_by_alias("m", "champion").version) == v1
