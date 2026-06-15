# Operations Runbook

## 1. Purpose

This runbook defines the minimum operational procedures for the Week 1 storage baseline and early-stage Imago environments.

## 2. Storage baseline (dormant until necessary)

### Active AWS baseline

- Region: `us-west-2`
- Bucket: `imago-dormant-archive-20260610-013300`
- Controls enabled:
	- Block Public Access (all four settings)
	- Server-side encryption (SSE-S3 / AES256)
	- Bucket versioning
	- Lifecycle transitions:
		- current objects: 30 days -> `GLACIER`, 180 days -> `DEEP_ARCHIVE`
		- noncurrent versions: 30 days -> `GLACIER`, 180 days -> `DEEP_ARCHIVE`
	- Abort incomplete multipart upload after 7 days

### Credentials model

- Commit-safe template: `aws-credentials.env.example`
- Local secret file (ignored): `aws-credentials.env.local`
- Never commit real credentials.

## 3. Routine verification checks

At least weekly (or after policy changes), verify:

1. Bucket exists and resolves in the expected region.
2. Public-access block remains fully enabled.
3. Encryption remains enabled.
4. Versioning remains enabled.
5. Lifecycle policy remains present and unchanged.

Record check date and operator in change history/issue notes.

## 4. Ingestion safety expectations

The ingestion path is expected to be all-or-nothing:

- object persisted
- metadata indexed
- ledger event written

On failure, compensation logic must remove partial artifacts where possible.

Code reference: `src/imago/storage/ingestion.py`.

## 5. Incident response (storage-focused)

If suspicious changes are detected:

1. Freeze write activity to affected path (application-level maintenance mode).
2. Export latest bucket configuration evidence and compare with baseline.
3. Verify recent ingest/ledger consistency from application logs.
4. Open security incident ticket with timestamp and affected assets.
5. Rotate IAM credentials/tokens if misuse is suspected.

## 6. Backup and restore guidance (baseline)

- Keep object versioning enabled for rollback support.
- Prefer immutable backup/export patterns for metadata + ledger stores (when durable stores are enabled).
- After restore, run chain verification and targeted hash re-checks.

## 7. Change management

Any change to lifecycle, encryption, versioning, or public-access posture must include:

- linked issue/ticket
- reviewer sign-off
- before/after evidence
- rollback notes

## 8. MONAI cache operations (Week 5 baseline)

These procedures apply when `IMAGO_MONAI_CACHE_MODE` is set to `cache_dataset` or
`persistent_dataset`.

### 8.1 Configuration baseline

- `IMAGO_MONAI_CACHE_MODE`: `disabled` | `cache_dataset` | `persistent_dataset`
- `IMAGO_MONAI_PERSISTENT_CACHE_DIR`: required for `persistent_dataset`; must be outside immutable archive storage roots.
- `IMAGO_MONAI_TRANSFORM_VERSION`: required transform pipeline identifier for lineage/reproducibility.
- `IMAGO_MONAI_CACHE_RETENTION_HOURS`: default cache retention window.
- `IMAGO_MONAI_CACHE_MAX_ITEMS`: soft cap for cache entries.

### 8.2 Sizing and retention guardrails

1. Place persistent caches on scratch volumes (local SSD or ephemeral worker volume), never in canonical archive paths.
2. Size cache volumes so planned peak cache occupancy remains below 80% of allocated storage.
3. Use retention-based cleanup at least daily, and after each major model/transform version rollover.
4. Treat cache artifacts as volatile derivatives; do not include cache files in source-of-truth integrity checks.

### 8.3 Purge/rebuild procedure

Use this when cache corruption, drift, or transform-version changes are detected.

1. Pause training/inference jobs using the affected cache path.
2. Capture evidence (timestamp, host, transform version, cache path).
3. Remove cache directory contents (or rotate to a new cache path).
4. Restart workloads to repopulate cache from canonical source images.
5. Verify canonical source hash checks still pass against immutable storage.
6. Record closure evidence in change/incident notes.
