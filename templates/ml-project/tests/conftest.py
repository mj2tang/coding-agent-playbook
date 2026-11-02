import pytest

from {{pkg}}.config import load_config


@pytest.fixture
def cfg():
    return load_config("configs/base.yaml")
