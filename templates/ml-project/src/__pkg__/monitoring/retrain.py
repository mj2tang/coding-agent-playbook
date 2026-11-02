"""Retraining policy: turn monitoring signals into an explicit, explainable decision.

Triggers (any one is enough), following common continuous-training practice:
data drift on the dataset, a performance drop versus the champion's offline metric
(when labels are available), or the model exceeding its maximum age.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class RetrainPolicy:
    max_model_age_days: int = 30
    max_metric_drop: float = 0.02  # absolute drop in the primary metric that triggers retraining
    retrain_on_dataset_drift: bool = True


@dataclass(frozen=True)
class RetrainDecision:
    retrain: bool
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def decide_retrain(
    policy: RetrainPolicy,
    *,
    dataset_drift: bool,
    model_trained_at: datetime,
    now: datetime | None = None,
    champion_metric: float | None = None,
    current_metric: float | None = None,
    higher_is_better: bool = True,
) -> RetrainDecision:
    now = now or datetime.now(timezone.utc)
    reasons: list[str] = []
    if policy.retrain_on_dataset_drift and dataset_drift:
        reasons.append("dataset drift detected")
    age_days = (now - model_trained_at).total_seconds() / 86400
    if age_days > policy.max_model_age_days:
        reasons.append(f"model age {age_days:.1f}d exceeds {policy.max_model_age_days}d")
    if champion_metric is not None and current_metric is not None:
        drop = (champion_metric - current_metric) if higher_is_better else (current_metric - champion_metric)
        if drop > policy.max_metric_drop:
            reasons.append(f"primary metric dropped by {drop:.4f} (> {policy.max_metric_drop})")
    return RetrainDecision(retrain=bool(reasons), reasons=reasons)
