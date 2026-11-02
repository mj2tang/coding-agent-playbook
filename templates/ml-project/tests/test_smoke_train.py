from {{pkg}}.data.load import load_dataset, split
from {{pkg}}.models.train import features_and_target, fit


def test_train_end_to_end_is_deterministic(cfg):
    train, valid = split(load_dataset(cfg), cfg)
    X, _ = features_and_target(valid, cfg)
    p1 = fit(train, cfg).predict_proba(X)[:, 1]
    p2 = fit(train, cfg).predict_proba(X)[:, 1]
    assert (p1 == p2).all()
    assert ((p1 >= 0) & (p1 <= 1)).all()
