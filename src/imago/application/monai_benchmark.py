from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from statistics import mean
from time import perf_counter_ns

from imago.application.monai_scratchpad import MonaiScratchpadUsageService
from imago.config.settings import Settings
from imago.domain.events import LedgerEvent
from imago.ledger.chain import LedgerChain
from imago.ledger.service import IdempotentLedgerService
from imago.storage.monai_cache import InMemoryMonaiCacheLineageStore, MonaiCacheConfig, MonaiCacheCoordinator
from imago.storage.policy import DataClassification


@dataclass(frozen=True)
class ScratchpadBenchmarkReport:
    iterations: int
    ledger_updates_per_cycle: int
    emit_lineage_records: bool
    mean_latency_ms: float
    p95_latency_ms: float

    def to_dict(self) -> dict[str, int | float | bool]:
        return asdict(self)


@dataclass(frozen=True)
class ScratchpadBenchmarkComparison:
    baseline: ScratchpadBenchmarkReport
    stressed: ScratchpadBenchmarkReport
    mean_latency_ratio: float
    p95_latency_ratio: float
    mean_latency_delta_ms: float
    p95_latency_delta_ms: float

    def within_threshold(self, *, max_ratio: float, max_delta_ms: float) -> bool:
        ratio_ok = self.mean_latency_ratio <= max_ratio and self.p95_latency_ratio <= max_ratio
        delta_ok = self.mean_latency_delta_ms <= max_delta_ms and self.p95_latency_delta_ms <= max_delta_ms
        return ratio_ok or delta_ok

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["baseline"] = self.baseline.to_dict()
        payload["stressed"] = self.stressed.to_dict()
        return payload


def run_scratchpad_benchmark(
    *,
    iterations: int,
    ledger_updates_per_cycle: int,
    emit_lineage_records: bool,
    operations_per_iteration: int = 8,
    warmup_iterations: int = 20,
) -> ScratchpadBenchmarkReport:
    if iterations <= 0:
        raise ValueError("iterations must be > 0")
    if ledger_updates_per_cycle < 0:
        raise ValueError("ledger_updates_per_cycle must be >= 0")
    if operations_per_iteration <= 0:
        raise ValueError("operations_per_iteration must be > 0")
    if warmup_iterations < 0:
        raise ValueError("warmup_iterations must be >= 0")

    settings = Settings(
        storage_backend="memory",
        monai_cache_mode="cache_dataset",
        monai_transform_version="benchmark",
        monai_emit_lineage_records=emit_lineage_records,
    )

    cache_config = MonaiCacheConfig.from_settings(settings)
    lineage_store = InMemoryMonaiCacheLineageStore()
    cache_coordinator = MonaiCacheCoordinator(cache_config, lineage_store)
    scratchpad_service = MonaiScratchpadUsageService.from_settings(
        coordinator=cache_coordinator,
        settings=settings,
    )

    ledger_service = IdempotentLedgerService(LedgerChain())
    latencies_ms: list[float] = []

    for idx in range(warmup_iterations + iterations):
        _simulate_ledger_churn(ledger_service, ledger_updates_per_cycle, idx)

        source_object_key = f"study-{idx % 7}/image-{idx}.dcm"
        source_hash = hashlib.sha256(source_object_key.encode("utf-8")).hexdigest()

        started = perf_counter_ns()
        for op in range(operations_per_iteration):
            scratchpad_service.process_cache_artifact(
                source_object_key=source_object_key,
                source_object_hash=source_hash,
                classification=DataClassification.RESTRICTED_CLINICAL,
                cache_artifact_ref=f"ram://cache/item-{idx}-{op}",
            )
        elapsed_ms = (perf_counter_ns() - started) / 1_000_000

        if idx >= warmup_iterations:
            latencies_ms.append(elapsed_ms / operations_per_iteration)

    sorted_latencies = sorted(latencies_ms)
    p95_index = max(0, int(len(sorted_latencies) * 0.95) - 1)

    return ScratchpadBenchmarkReport(
        iterations=iterations,
        ledger_updates_per_cycle=ledger_updates_per_cycle,
        emit_lineage_records=emit_lineage_records,
        mean_latency_ms=mean(latencies_ms),
        p95_latency_ms=sorted_latencies[p95_index],
    )


def compare_scratchpad_under_ledger_churn(
    *,
    iterations: int,
    baseline_ledger_updates_per_cycle: int,
    stressed_ledger_updates_per_cycle: int,
    emit_lineage_records: bool,
    operations_per_iteration: int = 8,
    warmup_iterations: int = 20,
) -> ScratchpadBenchmarkComparison:
    baseline = run_scratchpad_benchmark(
        iterations=iterations,
        ledger_updates_per_cycle=baseline_ledger_updates_per_cycle,
        emit_lineage_records=emit_lineage_records,
        operations_per_iteration=operations_per_iteration,
        warmup_iterations=warmup_iterations,
    )
    stressed = run_scratchpad_benchmark(
        iterations=iterations,
        ledger_updates_per_cycle=stressed_ledger_updates_per_cycle,
        emit_lineage_records=emit_lineage_records,
        operations_per_iteration=operations_per_iteration,
        warmup_iterations=warmup_iterations,
    )

    mean_ratio = _safe_ratio(stressed.mean_latency_ms, baseline.mean_latency_ms)
    p95_ratio = _safe_ratio(stressed.p95_latency_ms, baseline.p95_latency_ms)
    mean_delta = stressed.mean_latency_ms - baseline.mean_latency_ms
    p95_delta = stressed.p95_latency_ms - baseline.p95_latency_ms

    return ScratchpadBenchmarkComparison(
        baseline=baseline,
        stressed=stressed,
        mean_latency_ratio=mean_ratio,
        p95_latency_ratio=p95_ratio,
        mean_latency_delta_ms=mean_delta,
        p95_latency_delta_ms=p95_delta,
    )


def _simulate_ledger_churn(
    ledger_service: IdempotentLedgerService,
    updates_per_cycle: int,
    cycle: int,
) -> None:
    for offset in range(updates_per_cycle):
        serial = (cycle * max(1, updates_per_cycle)) + offset
        event = LedgerEvent.new(
            event_id=f"bench-evt-{serial}",
            event_type="benchmark.noop",
            principal_id="bench",
            image_id=f"bench-img-{serial}",
        )
        ledger_service.submit_events(
            idempotency_key=f"bench-ik-{serial}",
            events=[event],
        )


def _safe_ratio(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 1.0
    return numerator / denominator
