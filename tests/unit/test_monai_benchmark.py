from __future__ import annotations

import pytest

from imago.application.monai_benchmark import compare_scratchpad_under_ledger_churn


@pytest.mark.unit
def test_compare_scratchpad_under_ledger_churn_returns_reports() -> None:
    comparison = compare_scratchpad_under_ledger_churn(
        iterations=10,
        baseline_ledger_updates_per_cycle=0,
        stressed_ledger_updates_per_cycle=5,
        emit_lineage_records=False,
    )

    assert comparison.baseline.iterations == 10
    assert comparison.stressed.iterations == 10
    assert comparison.baseline.ledger_updates_per_cycle == 0
    assert comparison.stressed.ledger_updates_per_cycle == 5
    assert comparison.mean_latency_ratio > 0
    assert comparison.p95_latency_ratio > 0
    assert comparison.mean_latency_delta_ms >= 0
    assert comparison.p95_latency_delta_ms >= 0


@pytest.mark.unit
def test_compare_scratchpad_under_ledger_churn_validates_inputs() -> None:
    with pytest.raises(ValueError, match="iterations"):
        compare_scratchpad_under_ledger_churn(
            iterations=0,
            baseline_ledger_updates_per_cycle=0,
            stressed_ledger_updates_per_cycle=1,
            emit_lineage_records=True,
        )


@pytest.mark.unit
def test_within_threshold_allows_small_absolute_delta_when_ratio_is_high() -> None:
    comparison = compare_scratchpad_under_ledger_churn(
        iterations=8,
        baseline_ledger_updates_per_cycle=0,
        stressed_ledger_updates_per_cycle=4,
        emit_lineage_records=True,
    )

    assert comparison.within_threshold(max_ratio=0.01, max_delta_ms=1.0)
