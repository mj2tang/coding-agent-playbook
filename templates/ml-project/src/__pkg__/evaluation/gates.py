"""Metric gate: compare candidate metrics to a reference (baseline or champion) with per-metric rules."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GateRow:
    metric: str
    reference: float | None
    candidate: float | None
    delta: float | None
    status: str  # ok | REGRESSION | SUSPICIOUS GAIN | MISSING


def compare_metrics(candidate: dict, reference: dict, rules: dict) -> tuple[bool, list[GateRow]]:
    rows, passed = [], True
    for name, rule in rules.items():
        if name not in candidate or name not in reference:
            rows.append(GateRow(name, reference.get(name), candidate.get(name), None, "MISSING"))
            passed = False
            continue
        delta = candidate[name] - reference[name]
        worse = -delta if rule["direction"] == "higher" else delta
        status = "ok"
        if worse > rule["tolerance"]:
            status, passed = "REGRESSION", False
        elif "suspicious_gain" in rule and -worse > rule["suspicious_gain"]:
            status = "SUSPICIOUS GAIN"
        rows.append(GateRow(name, reference[name], candidate[name], delta, status))
    return passed, rows


def format_table(rows: list[GateRow], ref_label: str = "baseline") -> str:
    lines = [f"{'metric':<12} {ref_label:>10} {'candidate':>10} {'delta':>9}  status"]
    for r in rows:
        if r.delta is None:
            lines.append(f"{r.metric:<12} {'—':>10} {'—':>10} {'—':>9}  {r.status}")
        else:
            lines.append(
                f"{r.metric:<12} {r.reference:>10.4f} {r.candidate:>10.4f} {r.delta:>+9.4f}  {r.status}"
            )
    return "\n".join(lines)
