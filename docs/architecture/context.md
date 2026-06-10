# Architecture Context

## 1. System mission

Imago is a permissioned integrity and access-governance layer for medical imaging.
It stores immutable events, hashes, and policy decisions in a ledger model while
keeping image binaries off-ledger in controlled object storage.

## 2. Actors and external systems

### Primary actors

- Imaging uploader (technician/system integration account)
- Clinician or analyst requesting access
- Compliance/audit reviewer
- Security operations responder
- Platform operator

### External systems

- S3-compatible object storage (AWS S3 baseline, MinIO-compatible path for local/hybrid)
- Metadata index (PostgreSQL target)
- Identity provider (future OIDC/JWT integration)
- SIEM/log aggregation (future structured export)

## 3. Week 1 approval baseline (Objective 2)

### Scope approval status

- **Status:** Approved in repository baseline
- **Date:** 2026-06-10
- **Decision owner:** Repository maintainer (engineering)
- **Source:** `DevPlan.md` section "Product scope by medical image format"

### Approved scope

- Clinical primary: DICOM (`.dcm`, DICOM Part 10 without extension)
- Research/ML: NIfTI (`.nii`, `.nii.gz`), NRRD (`.nrrd`, `.nhdr`), MINC (`.mnc`), Analyze (`.hdr` + `.img`)
- Derived presentation artifacts (non-diagnostic): JPEG, PNG, TIFF

### Approved data classification baseline

- `restricted_clinical` for DICOM clinical sources
- `confidential_research` for de-identified/pseudonymized research formats
- `internal_derived` for non-diagnostic derivatives

Implementation evidence: `src/imago/storage/policy.py`, `src/imago/storage/contracts.py`, `src/imago/storage/ingestion.py`

## 4. Finalized storage strategy (Objective 3)

### Architecture decision

- **Binary tier (authoritative):** S3-compatible object storage
- **Metadata tier:** decoupled metadata index (PostgreSQL target; in-memory baseline for current stage)
- **Analytics tier:** Zarr/OME-Zarr derivatives for partial reads and ML parallelization (planned)

### Dormant-by-default storage controls

Baseline bucket controls were applied and validated in AWS (`us-west-2`) on 2026-06-10:

- Block all public access
- Server-side encryption at rest (SSE-S3)
- Object versioning enabled
- Lifecycle transitions: 30 days to Glacier, 180 days to Deep Archive
- Abort incomplete multipart uploads after 7 days

### Lifecycle and lineage control commitments

- Ingest must remain atomic across object write + metadata index + ledger event
- Each conversion must emit lineage details (source hash/key, tool version, output hash/key)
- Access decisions must remain classification-aware

Implementation evidence (atomicity path): `src/imago/storage/ingestion.py`

## 5. Constraints and non-goals

- Imago is not a PACS replacement and does not perform diagnostic rendering.
- Clinical data handling assumes least privilege and encryption in transit/at rest.
- Multi-node consensus is an evolution target, not a Week 1 deliverable.

## 6. Traceability pointers

- Plan and scope: `DevPlan.md`
- Requirements and controls: `compliance/software-requirements-specification.md`
- Threat posture: `compliance/threat-model.md`
- Design detail: `compliance/software-architecture-and-detailed-design.md`
