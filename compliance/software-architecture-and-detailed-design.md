# Software Architecture and Detailed Design

## 1. Document control

- **Project**: Imago
- **Version**: 1.0 (Draft baseline)
- **Date**: 2026-06-02
- **Owner**: Imago Engineering
- **Related documents**:
	- `compliance/software-requirements-specification.md`
	- `compliance/threat-model.md`
	- `compliance/risk-traceability-matrix.md`
	- `docs/architecture/context.md`

## 2. Architectural intent and system role

Imago is designed as a **third-party verification and anti-tampering layer** for radiology image archives (PACS/VNA/object storage). It is intentionally **not** the primary diagnostic archive. Instead, it:

1. Anchors object integrity and key metadata using cryptographic hashes.
2. Writes immutable, append-only events to a ledger model.
3. Supports independent verification and forensic auditability.

This role aligns with the SRS scope: off-chain image storage with on-chain/ledger integrity anchoring and governance events.

## 3. Context and boundaries

### 3.1 External ecosystem context

Typical radiology workflows follow: acquisition → QC → routing to PACS/VNA → interpretation/reporting → archival/distribution. Imago sits beside archive/storage and verifies integrity/provenance without replacing radiology systems.

### 3.2 Trust boundaries

1. **Client/integrator → Imago API** (`/api/v1/*`) over untrusted network.
2. **Imago → image storage backend** (filesystem now; S3/PACS adapters planned).
3. **Imago internal ingestion transaction** across object write, metadata index write, and ledger event write.
4. **Compliance/audit consumers → Imago evidence APIs/exports** (future expansion).

### 3.3 Out-of-scope for this baseline

- PACS internals and diagnostic viewer behavior.
- Full distributed BFT consensus cluster deployment.
- Clinical workflow orchestration (RIS/EHR workflows).

## 4. Design principles

1. **Tamper evidence first**: every protected action produces immutable evidence.
2. **Separation of concerns**: binaries off-ledger; integrity/governance on ledger.
3. **Atomic ingest semantics**: no partial success across object/metadata/ledger.
4. **Policy-aware data handling**: classification derived from format profile.
5. **Upgrade path to replicated ordering**: current interfaces preserve ledger abstraction for future permissioned consensus.

## 5. Logical architecture

Imago follows a layered architecture:

1. **API Layer** (`src/imago/api/*`)
	 - Request validation, payload decoding, route contracts.
2. **Application/Orchestration Layer** (`src/imago/storage/ingestion.py`)
	 - Atomic ingestion coordinator and compensation logic.
3. **Domain Layer** (`src/imago/domain/events.py`, `src/imago/storage/policy.py`)
	 - Event structures, format families, data classification policy.
4. **Ledger Layer** (`src/imago/ledger/chain.py`)
	 - Hash-linked block/event model and chain verification.
5. **Storage/Adapter Layer** (`src/imago/storage/filesystem.py`, dependency adapters)
	 - Object persistence backend and metadata/ledger writer interfaces.
6. **Configuration Layer** (`src/imago/config/settings.py`)
	 - Environment-driven runtime configuration.

## 6. Component design and responsibilities

### 6.1 API service

- **Entry point**: `src/imago/main.py`
	- Creates FastAPI app and includes router.
- **Routes**: `src/imago/api/routes.py`
	- `GET /api/v1/healthz`: liveness.
	- `GET /api/v1/version`: build/version visibility.
	- `POST /api/v1/images/ingest`: validated ingest path.
- **Data contracts**: `src/imago/api/models.py`
	- `ImageIngestRequest` and `ImageIngestResponse` with strict validation (`extra="forbid"`).

Design notes:
- Validates base64 payload and non-empty decode.
- Enforces format/object-key consistency.
- Converts extension/profile to classification and family for deterministic policy behavior.

### 6.2 Ingestion orchestration (atomic transaction coordinator)

- **Component**: `AtomicIngestionCoordinator` in `src/imago/storage/ingestion.py`.
- **Operation order**:
	1. Hash object bytes (`SHA-256`).
	2. Write object to object storage.
	3. Upsert metadata index record.
	4. Write immutable ledger ingestion event.
- **Failure model**:
	- On downstream error, executes compensating actions:
		- delete metadata (if supported)
		- delete object (if supported)
	- Raises `IngestionError` to preserve all-or-nothing semantics.

### 6.3 Policy and data classification

- **Component**: `src/imago/storage/policy.py`
- Maps format extensions to:
	- `FormatFamily` (`dicom`, `neuro_research`, `standard_derived`, `unknown`)
	- `DataClassification` (`restricted_clinical`, `confidential_research`, `internal_derived`, `unclassified`)
	- flags: diagnostic/source-of-truth semantics.

Design intent:
- Distinguish clinical diagnostics from research/derived artifacts.
- Encode governance controls early in ingestion lifecycle.

### 6.4 Ledger subsystem (current baseline)

- **Domain event**: `LedgerEvent` (`src/imago/domain/events.py`).
- **Chain implementation**: `LedgerChain` (`src/imago/ledger/chain.py`).
	- Genesis block bootstrap.
	- Canonical JSON serialization + `SHA-256` block hash.
	- Hash linkage via `previous_hash`.
	- `verify()` checks linkage + recomputed hash integrity.

Security property:
- Any post-facto mutation in block contents or links invalidates chain verification.

### 6.5 Storage and dependency adapters

- **Protocol contracts** (`src/imago/storage/contracts.py`):
	- `ObjectStorage`, `MetadataIndex`, `LedgerWriter`, `AtomicIngestionService`
	- optional compensators (`DeletableObjectStorage`, `CompensatingMetadataIndex`)
- **Filesystem adapter**: `FilesystemObjectStorage`
	- Safe path normalization, traversal prevention (`..` / absolute path reject), write/delete support.
- **Dependency provider**: `src/imago/api/dependencies.py`
	- Backend selection from settings (`filesystem`, `memory`).
	- In-memory metadata and ledger writer implementations for baseline/dev/test.

### 6.6 Configuration and runtime behavior

- **Settings**: `src/imago/config/settings.py`
	- `.env` support via `pydantic-settings`.
	- `IMAGO_` prefix for deployment-safe config separation.
	- Key parameters: host/port, environment, storage backend/root.

## 7. Detailed runtime flows

### 7.1 Ingestion flow (implemented)

1. Client submits `ImageIngestRequest`.
2. API validates schema, base64 payload, and format/key consistency.
3. API builds `IngestionPayload` with UTC timestamp and policy profile.
4. Coordinator computes object hash.
5. Object written to backend.
6. Metadata index updated.
7. Ledger event written.
8. Response returns `object_hash`, `metadata_id`, `ledger_event_id`, `classification`, `format_family`.

### 7.2 Failure and compensation flow (implemented)

1. If metadata write fails: object write is compensated (deleted).
2. If ledger write fails: metadata and object are compensated.
3. API returns controlled failure (`ingestion failed`) without leaking sensitive internals.

### 7.3 Chain verification flow (implemented)

1. Iterate blocks from index 1.
2. Validate `previous_hash` pointer integrity.
3. Recompute canonical hash payload.
4. Return pass/fail as tamper-evidence signal.

## 8. Data model and interface contracts

### 8.1 Ingestion request contract

- `object_key`, `content_type`, `uploaded_by`, `format_name`, `payload_b64`

### 8.2 Ingestion result contract

- `object_key`, `object_hash`, `metadata_id`, `ledger_event_id`, `classification`, `format_family`

### 8.3 Ledger block structure

- `index`, `timestamp`, `events[]`, `previous_hash`, `block_hash`

### 8.4 Ledger event structure

- `event_id`, `event_type`, `principal_id`, `image_id`, `occurred_at`

## 9. Security architecture

### 9.1 Integrity controls

- Cryptographic hashing (`SHA-256`) of ingested binary.
- Hash-linked block integrity in ledger chain.
- Explicit chain verification method for anti-tampering checks.

### 9.2 Input and boundary protection

- Strict API model validation and unknown field rejection.
- Base64 strict decoding and empty payload rejection.
- Filesystem path traversal protections in object storage adapter.

### 9.3 Governance and audit posture

- Immutable-event pattern for ingestion events.
- Classification-aware ingest decisions.
- Separation of binary storage from verification ledger.

### 9.4 Future hardening roadmap (architecture-preserving)

1. Replace in-memory metadata/ledger writers with durable stores.
2. Introduce authenticated API boundary (OIDC/JWT).
3. Add mTLS/service identity for adapter calls.
4. Add signed event envelopes and key rotation.
5. Add verification APIs and audit export APIs from SRS.

## 10. ResilientDB-inspired evolution path

Imago’s current ledger is single-process and hash-linked; target evolution follows a **permissioned replicated ordering architecture** inspired by ResilientDB principles:

1. Separate **transaction ordering** from **execution/application handling**.
2. Replicate ledger writers over a BFT set (e.g., $3f+1$ replicas for $f$ Byzantine faults).
3. Maintain immutable event semantics with durable storage/checkpointing.
4. Preserve API and application contracts so migration to replicated consensus is adapter-level, not API-breaking.

This allows Imago to start lean while keeping an architectural runway toward resilient, verifiable, multi-node anti-tamper operation.

## 11. Deployment architecture (baseline and target)

### 11.1 Baseline (current)

- Single FastAPI process.
- Local filesystem object storage (or in-memory for tests/dev).
- In-memory metadata index and ledger writer.

### 11.2 Target (compliance-aligned)

- API service tier (horizontally scalable).
- Durable metadata/index store.
- Permissioned replicated ledger service tier.
- Object storage/PACS integration adapters.
- Monitoring, SIEM export, and backup/restore channels.

## 12. Requirement-to-design mapping (summary)

- **FR-REG-001..006**: API ingest + `AtomicIngestionCoordinator` all-or-nothing behavior.
- **FR-INT-001/004**: object hash anchoring + immutable event write.
- **FR-AUD-001/005**: chain-linked event model + `verify()` capability.
- **FR-API-001/002**: versioned REST endpoints + structured errors.
- **NFR-SEC-003 / NFR-REL-002**: deny-by-default policy direction + transactional compensation semantics.

Additional SRS requirements (authz workflows, full audit query/export, resilient multi-node consensus) are intentionally staged for subsequent increments.

## 13. Verification evidence in repository

- `tests/unit/test_ingestion_service.py`
	- validates successful ingest and compensation rollback paths.
- `tests/unit/test_chain.py`
	- validates append/verify and tamper detection.
- `tests/unit/test_storage_policy.py`
	- validates format-to-classification policy behavior.
- `tests/unit/test_filesystem_storage.py`
	- validates write/delete and traversal protection.
- `tests/unit/test_settings.py`
	- validates environment-driven config behavior.

## 14. Known gaps and planned increments

1. Durable metadata and ledger persistence beyond process memory.
2. Authn/authz and role/tenant/classification-aware policy engine enforcement on all routes.
3. Verification/query/export APIs for auditors and responders.
4. SIEM-ready security event streaming and anomaly detection.
5. Multi-node replicated permissioned ledger implementation.

## 15. References

### 15.1 Project knowledge base inputs

1. `~/Documents/imgkb/radiology_pipeline.md`
2. `~/Documents/imgkb/components_pacs.md`

### 15.2 External architecture and blockchain references

3. Apache ResilientDB repository: https://github.com/apache/incubator-resilientdb
4. ResilientDB Beacon overview: https://beacon.resilientdb.com/docs/resilientdb
5. ResilientDB installation and deployment topology: https://beacon.resilientdb.com/docs/installation
6. NexRes architecture article: https://blog.resilientdb.com/2022/09/27/What_Is_NexRes.html

### 15.3 External workflow/PACS references embedded in KB

7. Radiology workflow and PACS references cited in `radiology_pipeline.md`.
8. PACS component and integration references cited in `components_pacs.md`.

### 15.4 Internal code and design references

9. `src/imago/main.py`
10. `src/imago/api/models.py`
11. `src/imago/api/routes.py`
12. `src/imago/api/dependencies.py`
13. `src/imago/storage/contracts.py`
14. `src/imago/storage/ingestion.py`
15. `src/imago/storage/filesystem.py`
16. `src/imago/storage/policy.py`
17. `src/imago/domain/events.py`
18. `src/imago/ledger/chain.py`
19. `src/imago/config/settings.py`
20. `tests/unit/test_chain.py`
21. `tests/unit/test_ingestion_service.py`
22. `tests/unit/test_storage_policy.py`
23. `tests/unit/test_filesystem_storage.py`
24. `tests/unit/test_settings.py`
