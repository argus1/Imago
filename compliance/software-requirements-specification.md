# Software Requirements Specification (SRS)

## 1. Document control

- **Project**: Imago
- **Version**: 1.0 (Draft baseline)
- **Date**: 2026-06-01
- **Owner**: Imago Engineering
- **Related documents**:
	- `DevPlan.md`
	- `compliance/software-architecture-and-detailed-design.md`
	- `compliance/threat-model.md`
	- `compliance/risk-traceability-matrix.md`

## 2. Purpose and scope

Imago is a healthcare-oriented, permissioned image-access ledger service. It does **not** store diagnostic image binaries on-chain. It records immutable security and governance events (registration, access grants/revocations, verification, and audit), while image binaries remain off-chain in controlled storage (object storage/PACS-compatible systems).

This SRS defines functional and non-functional requirements for:

1. Image registration and integrity anchoring.
2. Access policy management and enforcement.
3. Tamper-evident verification and forensic-ready audit.
4. Security controls for medical-image tampering threats (pixel/data manipulation, metadata manipulation, transport interception, malware-laced DICOM files, ransomware, and insider abuse).

## 3. Context and references

Requirements are derived from:

- `DevPlan.md` architectural and compliance direction.
- `/docs/imgkb/tampering_medical_images.md` (Gemini summary with citations).
- `/docs/imgkb/gnrl_img_cybersecurity.pdf` (ACR/SIIM 2025 white paper: “Protecting Radiology Data and Devices Against Cybersecurity Threats”).
- Publicly accessible guidance/articles reviewed during drafting, including DICOM security guidance, PACS cybersecurity overviews, CT-GAN attack publication, and forensic PACS/DICOM tamper analysis.

## 4. Definitions

- **DICOM**: Digital Imaging and Communications in Medicine standard.
- **PACS**: Picture Archiving and Communication System.
- **VNA**: Vendor Neutral Archive.
- **Ledger event**: Immutable, hash-linked record in Imago.
- **Integrity anchor**: Cryptographic hash and metadata binding between off-chain object and ledger record.
- **Lineage event**: Event recording derivation/conversion from source image to output image.
- **Principal**: Authenticated user/service acting on data.
- **Classification**:
	- Restricted clinical imaging (typically DICOM with PHI risk)
	- Confidential research imaging (NIfTI/NRRD/MINC/Analyze, de-identified/pseudonymized contexts)
	- Internal derived artifacts (JPEG/PNG/TIFF non-diagnostic derivatives)

## 5. Product constraints and assumptions

1. Imago is a permissioned system with authenticated principals only.
2. Diagnostic originals remain off-chain; the ledger stores references/hashes/signatures/events.
3. The first release may be single-node but must preserve interfaces for future replicated ordering.
4. Clinical and research contexts must be policy-distinguishable.
5. Security controls must be operable in mixed legacy environments (including systems that may not fully implement all DICOM security features).

## 6. System actors

- **Radiology technician / uploader**: registers images and metadata.
- **Radiologist / clinician**: requests/uses access and initiates verification.
- **Compliance officer / auditor**: queries audit trails and evidence.
- **Security analyst / incident responder**: investigates suspicious events.
- **System administrator**: manages policy, configuration, and operations.
- **External integrated systems**: PACS/VNA/object storage, IdP, SIEM.

## 7. High-level workflows

1. Register image and metadata, persist integrity anchor.
2. Grant, revoke, and evaluate access with least privilege.
3. Verify image integrity against anchor.
4. Record and query immutable audit history.
5. Record lineage for conversions/derivatives.
6. Detect/respond to tampering and operational anomalies.

## 8. Functional requirements

### 8.1 Image registration and ingestion

- **FR-REG-001**: The system shall register an image asset with globally unique asset ID.
- **FR-REG-002**: The system shall store at minimum: object key/reference, cryptographic content hash, format, source context, classification, timestamp, and registering principal.
- **FR-REG-003**: The system shall reject registration when required fields are missing or malformed.
- **FR-REG-004**: The system shall support formats in project scope: DICOM, NIfTI, NRRD, MINC, Analyze, JPEG, PNG, TIFF.
- **FR-REG-005**: The system shall enforce source-context rules (clinical/research/derived) at registration time.
- **FR-REG-006**: The system shall ensure ingest atomicity across binary reference write confirmation, metadata persistence, and ledger-event creation.
- **FR-REG-007**: The system shall provide idempotent registration semantics using client-supplied idempotency key or deterministic deduplication key.

### 8.2 Access policy and authorization

- **FR-AUTH-001**: The system shall authenticate every API request.
- **FR-AUTH-002**: The system shall authorize requests using least-privilege, deny-by-default policy.
- **FR-AUTH-003**: The system shall support role-, tenant-, and classification-aware authorization.
- **FR-AUTH-004**: The system shall support explicit grant and revoke events per principal/role with effective timestamps.
- **FR-AUTH-005**: The system shall evaluate request context (principal, action, resource, classification, environment constraints) before permitting access.
- **FR-AUTH-006**: The system shall record every policy decision (allow/deny) as an auditable event.

### 8.3 Integrity verification and anti-tamper controls

- **FR-INT-001**: The system shall verify image integrity by recomputing and comparing cryptographic hash values.
- **FR-INT-002**: The system shall return verification outcome states: `verified`, `mismatch`, `not-found`, `insufficient-evidence`.
- **FR-INT-003**: The system shall support verification of both original assets and derived assets via lineage links.
- **FR-INT-004**: The system shall record each verification operation as an immutable audit event.
- **FR-INT-005**: The system shall support optional external digital-signature validation status capture (e.g., scanner-side signatures) as metadata/evidence fields.
- **FR-INT-006**: The system shall detect and flag metadata anomalies relevant to tampering (e.g., inconsistent timestamp/tag patterns when available).
- **FR-INT-007**: The system shall support import-time DICOM preamble hygiene validation status (including preamble-cleansing policy result) for files ingested via media/file channels.

### 8.4 Audit, forensics, and evidence

- **FR-AUD-001**: The system shall create tamper-evident, append-only audit events for security-relevant actions.
- **FR-AUD-002**: Audit events shall include actor, action, resource, decision/outcome, timestamp, and correlation ID.
- **FR-AUD-003**: The system shall allow querying audit trails by asset, principal, organization, date range, and event type.
- **FR-AUD-004**: The system shall support export of audit evidence in machine-readable format for incident response/compliance review.
- **FR-AUD-005**: The system shall preserve event ordering and chain integrity verification capability.
- **FR-AUD-006**: The system shall log policy/permission changes and administrative actions with immutable records.

### 8.5 Lineage and conversion governance

- **FR-LIN-001**: The system shall record lineage events for any conversion/transformation.
- **FR-LIN-002**: Lineage records shall include source hash/key, conversion tool/version, output hash/key, and principal/process identity.
- **FR-LIN-003**: The system shall tag JPEG/PNG/TIFF outputs as non-diagnostic derivatives by default unless explicitly configured otherwise.
- **FR-LIN-004**: The system shall prevent deletion of lineage links that would break provenance continuity; redaction must be represented as a new immutable event.

### 8.6 Security operations and resilience

- **FR-SECOPS-001**: The system shall emit structured security and audit logs suitable for SIEM ingestion.
- **FR-SECOPS-002**: The system shall expose health and readiness endpoints for operational monitoring.
- **FR-SECOPS-003**: The system shall support detection signal generation for high-risk events (e.g., repeated verification mismatch, unusual access bursts, privileged policy edits).
- **FR-SECOPS-004**: The system shall support secure backup/restore procedures for ledger and metadata stores with integrity checks.
- **FR-SECOPS-005**: The system shall provide recovery procedures that preserve audit chain continuity after restoration.

### 8.7 API and integration

- **FR-API-001**: The system shall provide versioned REST APIs for registration, grants/revokes, verification, and audit queries.
- **FR-API-002**: APIs shall return structured errors without exposing sensitive internal details.
- **FR-API-003**: The system shall support integration adapters for local filesystem dev storage and S3-compatible object storage; PACS integration shall be extensible via adapter interfaces.
- **FR-API-004**: API authentication and authorization mechanisms shall be centrally enforceable for service and user identities.

## 9. Non-functional requirements

### 9.1 Security requirements

- **NFR-SEC-001**: All external and internal service communications shall use encrypted transport (TLS 1.2+ minimum; TLS 1.3 preferred).
- **NFR-SEC-002**: Secrets shall not be hardcoded and shall be managed through environment/vault mechanisms.
- **NFR-SEC-003**: Access control shall be deny-by-default and least-privilege.
- **NFR-SEC-004**: The system shall support MFA-capable identity federation at the access boundary (via IdP integration).
- **NFR-SEC-005**: Data at rest shall be encrypted in storage systems supporting encryption controls.
- **NFR-SEC-006**: The system shall support network segmentation-friendly deployment (separate API, storage, and admin/security planes).
- **NFR-SEC-007**: Security-relevant logs shall be immutable or write-once protected by downstream logging architecture.

### 9.2 Reliability and availability

- **NFR-REL-001**: The system shall degrade safely on dependency failures (fail closed for authorization paths).
- **NFR-REL-002**: Critical operations (registration, policy changes, verification result persistence) shall be transactional and recoverable.
- **NFR-REL-003**: Backup and restore procedures shall be tested at defined intervals.

### 9.3 Performance and scalability

- **NFR-PERF-001**: API response latency targets shall be defined and monitored for core endpoints.
- **NFR-PERF-002**: The architecture shall support scaling read-heavy audit/query workloads independently of write path.
- **NFR-PERF-003**: Integrity verification workflows shall support asynchronous processing for large-volume checks.

### 9.4 Maintainability and quality

- **NFR-QUAL-001**: Code shall pass lint, unit tests, and type checks in CI.
- **NFR-QUAL-002**: Security scanning (dependency and static analysis) shall run in CI.
- **NFR-QUAL-003**: Public interfaces and event schemas shall be versioned and backward-compatibility managed.

### 9.5 Compliance and governance

- **NFR-COMP-001**: System behavior shall support HIPAA-aligned confidentiality, integrity, and audit accountability objectives.
- **NFR-COMP-002**: Audit evidence shall be retained according to policy and retrievable for compliance investigations.
- **NFR-COMP-003**: Configuration changes affecting security posture shall be traceable and approval-controlled.

## 10. Misuse and abuse-case-driven requirements

The following requirements are explicitly threat-derived:

- **ABR-001 (Transport interception/MITM)**: Enforce encrypted and authenticated channels for all imaging metadata/event transfer paths.
- **ABR-002 (Metadata tampering)**: Preserve and verify metadata integrity anchors, record discrepancies, and alert on anomalous modifications.
- **ABR-003 (Pixel tampering / CT-GAN-style manipulation)**: Require integrity re-verification against registered source before trust-sensitive downstream use, and log mismatches as security events.
- **ABR-004 (DICOM preamble malware)**: Validate/cleanse import artifacts and record validation outcome.
- **ABR-005 (PACS trust abuse / identity spoofing patterns)**: Require strong principal identity and authorization context at API layer; do not trust implicit network presence.
- **ABR-006 (Ransomware/disruption)**: Maintain tested backup/restore and incident evidence continuity.
- **ABR-007 (Insider misuse)**: Enforce least privilege, full auditability, and policy decision logging.

## 11. Verification approach

Each requirement shall map to one or more verification methods:

- **T**: automated test (unit/integration/system)
- **I**: inspection/review (code/config/document)
- **A**: analysis (threat/risk/log review)
- **D**: demonstration/tabletop/operational drill

Example baseline mappings:

- FR-REG-* → T/I
- FR-AUTH-* → T/A
- FR-INT-* → T/A/D
- FR-AUD-* → T/I/A
- NFR-SEC-* → I/A/D
- ABR-* → T/A/D

Detailed matrix linkage is maintained in `compliance/risk-traceability-matrix.md`.

## 12. Out-of-scope (this release)

1. Full multi-node consensus implementation (interface readiness required, full deployment optional).
2. Native diagnostic viewer implementation.
3. Comprehensive PACS replacement.

## 13. Acceptance criteria for SRS baseline

The SRS baseline is accepted when:

1. All requirements are uniquely identified and testable.
2. Threat-derived requirements are explicitly represented.
3. Requirement IDs are traceable to threat model and test artifacts.
4. Stakeholders approve scope, priorities, and out-of-scope declarations.

## 14. Reference notes (informative)

- ACR/SIIM 2025 white paper emphasizes layered safeguards, inventory-driven hardening, incident response, and routine downtime/cyber drills.
- DICOM security guidance emphasizes implementation/deployment responsibility, TLS/HTTPS usage, and mitigation of preamble-related risk.
- PACS cybersecurity literature highlights defense-in-depth, segmentation, access control, and robust auditability as practical controls.
- Published tampering research demonstrates both pixel and metadata manipulation feasibility and supports requirements for integrity verification plus forensic-grade logging.
