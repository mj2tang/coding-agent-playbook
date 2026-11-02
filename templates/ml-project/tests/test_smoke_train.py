from {{pkg}}.data.load import TARGET, load_dataset, split
from {{pkg}}.features.build import build_features
from {{pkg}}.models.train import fit


def test_train_end_to_end_is_deterministic(cfg):
    train, valid = split(load_dataset(cfg), cfg)
    X = build_features(valid, cfg).drop(columns=[TARGET])
    p1 = fit(train, cfg).predict_proba(X)[:, 1]
    p2 = fit(train, cfg).predict_proba(X)[:, 1]
    assert (p1 == p2).all()
    assert ((p1 >= 0) & (p1 <= 1)).all()
