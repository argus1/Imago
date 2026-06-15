# Imago
Tamper-proof storage of Medical Images enabled with Blockchain

![MRI Image](/MRI.webp)

## API auth headers (lightweight baseline)

Policy endpoints currently use a lightweight header-based identity context.

Required headers:

- `X-Imago-Principal-Id`
- `X-Imago-Org-Id`
- `X-Imago-Role`

Optional header:

- `X-Imago-Principal-Type` (`user` by default, `service` supported)

Behavior notes:

- Missing required auth headers return `401 Unauthorized`.
- `POST /api/v1/policy/grants` and `POST /api/v1/policy/grants/{grant_id}/revoke`
	require `admin` or `super_admin` role.
- `POST /api/v1/policy/evaluate` derives principal identity from headers (not from body fields).

## MONAI scratchpad controls (Week 5)

MONAI cache usage is treated as a scratchpad layer, separate from canonical image storage.

- `IMAGO_MONAI_CACHE_MODE` controls whether MONAI-style caching is disabled, RAM-style (`cache_dataset`), or disk-style (`persistent_dataset`).
- `IMAGO_MONAI_EMIT_LINEAGE_RECORDS` optionally toggles cache lineage emission during scratchpad usage.
	- `true`: emit lineage records for reproducibility/audit.
	- `false`: skip lineage writes for performance-sensitive runs.

### Scratchpad-vs-ledger churn benchmark

A benchmark harness is available to compare scratchpad latency with low vs high ledger update churn:

- `scripts/test/benchmark_monai_scratchpad.py`

It prints JSON with baseline/stressed latency metrics and exits non-zero if both ratio and absolute-delta thresholds indicate adverse impact.
