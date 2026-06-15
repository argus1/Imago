#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from imago.application.monai_benchmark import compare_scratchpad_under_ledger_churn


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Benchmark MONAI scratchpad latency under low vs high ledger-update churn."
        ),
    )
    parser.add_argument("--iterations", type=int, default=500)
    parser.add_argument("--warmup-iterations", type=int, default=30)
    parser.add_argument("--operations-per-iteration", type=int, default=12)
    parser.add_argument("--baseline-ledger-updates", type=int, default=0)
    parser.add_argument("--stressed-ledger-updates", type=int, default=200)
    parser.add_argument(
        "--emit-lineage-records",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Toggle lineage emission during scratchpad usage.",
    )
    parser.add_argument(
        "--max-latency-ratio",
        type=float,
        default=1.25,
        help=(
            "Fail with non-zero exit code if mean or p95 stressed/baseline latency ratio "
            "exceeds this threshold."
        ),
    )
    parser.add_argument(
        "--max-latency-delta-ms",
        type=float,
        default=0.05,
        help=(
            "Alternative pass criterion: if absolute mean and p95 latency deltas stay below "
            "this value, run is considered non-adverse even when ratio is noisy."
        ),
    )
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    comparison = compare_scratchpad_under_ledger_churn(
        iterations=args.iterations,
        baseline_ledger_updates_per_cycle=args.baseline_ledger_updates,
        stressed_ledger_updates_per_cycle=args.stressed_ledger_updates,
        emit_lineage_records=args.emit_lineage_records,
        operations_per_iteration=args.operations_per_iteration,
        warmup_iterations=args.warmup_iterations,
    )

    payload = comparison.to_dict()
    payload["max_latency_ratio"] = args.max_latency_ratio
    payload["max_latency_delta_ms"] = args.max_latency_delta_ms
    payload["within_threshold"] = comparison.within_threshold(
        max_ratio=args.max_latency_ratio,
        max_delta_ms=args.max_latency_delta_ms,
    )

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["within_threshold"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
