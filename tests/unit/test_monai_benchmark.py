from __future__ import annotations

import pytest

from imago.application import monai_benchmark
from imago.application.monai_benchmark import (
    ScratchpadBenchmarkReport,
    compare_scratchpad_under_ledger_churn,
)


@pytest.mark.unit
def test_compare_scratchpad_under_ledger_churn_returns_reports(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run_scratchpad_benchmark(
        *,
        iterations: int,
        ledger_updates_per_cycle: int,
        emit_lineage_records: bool,
        operations_per_iteration: int = 8,
        warmup_iterations: int = 20,
    ) -> ScratchpadBenchmarkReport:
        del operations_per_iteration, warmup_iterations
        if ledger_updates_per_cycle == 0:
            return ScratchpadBenchmarkReport(
                iterations=iterations,
                ledger_updates_per_cycle=ledger_updates_per_cycle,
                emit_lineage_records=emit_lineage_records,
                mean_latency_ms=1.0,
                p95_latency_ms=1.5,
            )

        return ScratchpadBenchmarkReport(
            iterations=iterations,
            ledger_updates_per_cycle=ledger_updates_per_cycle,
            emit_lineage_records=emit_lineage_records,
            mean_latency_ms=1.25,
            p95_latency_ms=1.8,
        )

    monkeypatch.setattr(
        monai_benchmark,
        "run_scratchpad_benchmark",
        fake_run_scratchpad_benchmark,
    )

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
    assert comparison.mean_latency_ratio == pytest.approx(1.25)
    assert comparison.p95_latency_ratio == pytest.approx(1.2)
    assert comparison.mean_latency_delta_ms == pytest.approx(0.25)
    assert comparison.p95_latency_delta_ms == pytest.approx(0.3)


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
