# Threat Model

## 1. Document control

- **Project**: Imago
- **Version**: 1.0 (Draft baseline)
- **Date**: 2026-06-01
- **Method**: STRIDE-informed analysis + abuse-case modeling + control mapping
- **Related docs**:
	- `DevPlan.md`
	- `compliance/software-requirements-specification.md`
	- `compliance/risk-traceability-matrix.md`

## 2. Objectives

1. Identify credible threats to confidentiality, integrity, and availability of imaging-related workflows.
2. Prioritize threats that can lead to clinical harm, fraud, legal exposure, or operational disruption.
3. Define preventive, detective, and recovery controls.
4. Ensure traceability to SRS requirements and verification activities.

## 3. Scope and architecture context

### 3.1 In-scope components

- Imago API boundary (registration, authorization, verification, audit)
- Ledger/event subsystem
- Policy engine
- Metadata store and projection/query layer
- Storage adapters (filesystem dev, object storage, PACS integration boundary)
- Monitoring/audit telemetry pipeline
- Admin/security operations interfaces

### 3.2 Out-of-scope components (still considered as external dependencies)

- External PACS/VNA internals
- External IdP internals
- Cloud provider control planes
- Hospital enterprise network controls not owned by Imago team

### 3.3 Data classification in scope

- **Restricted clinical imaging data** (high impact)
- **Confidential research imaging data** (medium-high impact)
- **Internal derived artifacts** (medium impact)

## 4. Trust boundaries

1. **Client ↔ Imago API**: untrusted network boundary.
2. **Imago service ↔ external storage/PACS**: integration boundary with variable trust posture.
3. **Imago service ↔ identity provider**: authentication boundary.
4. **Imago internal services ↔ ledger/metadata stores**: privileged internal boundary.
5. **Operations plane ↔ production runtime**: administrative boundary.
6. **Audit export ↔ downstream SIEM/compliance tooling**: evidence-transfer boundary.

## 5. Assets and security properties

### 5.1 Critical assets

- Integrity anchors (hashes/signature status bindings)
- Access policy state and grant/revoke history
- Audit ledger and event-chain continuity
- Principal identities and authorization decisions
- Lineage/provenance records
- Configuration/secrets

### 5.2 Security properties

- **Confidentiality**: unauthorized disclosure of PHI/ePHI is prevented.
- **Integrity**: tampering is prevented or detected with high confidence.
- **Availability**: critical workflows remain recoverable and safe under incident conditions.
- **Accountability**: who-did-what evidence is complete, ordered, and tamper-evident.

## 6. Threat actors

1. **External adversary**: seeks data theft, extortion, disruption, or targeted manipulation.
2. **Insider (malicious or negligent)**: abuses privileged access or mishandles data.
3. **Supply-chain actor**: compromises dependency, package, or integration endpoint.
4. **Opportunistic attacker**: exploits weak configuration, outdated systems, or unencrypted paths.
5. **Fraud actor**: manipulates data for insurance/research/identity fraud.

## 7. Primary attack surfaces

- API endpoints and authn/authz workflows
- Imaging metadata ingestion and parsing paths
- Storage adapter interfaces and object references
- Admin/policy-change endpoints
- Audit export and telemetry channels
- CI/CD and dependency update path

## 8. STRIDE threat analysis (summary)

### 8.1 Spoofing

- **Threat**: Impersonation of valid user/service identities.
- **Impact**: Unauthorized access, policy manipulation, data exfiltration.
- **Controls**:
	- Strong authentication at all API boundaries.
	- MFA-capable federation through trusted IdP.
	- Short-lived credentials/tokens and audience checks.
	- Signed service-to-service identity where applicable.

### 8.2 Tampering

- **Threat**: Modification of metadata, image content references, audit events, or lineage.
- **Impact**: Clinical misdiagnosis, fraud, legal exposure.
- **Controls**:
	- Cryptographic integrity anchors and verification workflows.
	- Append-only ledger semantics with chain verification.
	- Immutable audit trail for sensitive actions.
	- Import validation policies (including DICOM preamble hygiene status capture).

### 8.3 Repudiation

- **Threat**: Actor denies having performed sensitive operations.
- **Impact**: Failed investigations, compliance failure.
- **Controls**:
	- Signed/immutable event records with correlation IDs.
	- Time-synchronized audit logging.
	- Administrative action logging and approval trails.

### 8.4 Information disclosure

- **Threat**: Unauthorized exposure of PHI/ePHI or sensitive operational data.
- **Impact**: Privacy breaches, penalties, loss of trust.
- **Controls**:
	- Encryption in transit and at rest.
	- Classification-aware access controls.
	- Minimum necessary data principle for APIs/logs.
	- Secure secret handling; no secrets in code/logs.

### 8.5 Denial of service

- **Threat**: Service disruption (e.g., resource exhaustion, ransomware, dependency outage).
- **Impact**: Delayed care workflows, operational downtime.
- **Controls**:
	- Rate limiting and backpressure.
	- Health checks, graceful degradation.
	- Tested backup/restore and incident response plans.
	- Segmented architecture limiting blast radius.

### 8.6 Elevation of privilege

- **Threat**: User/service gains unauthorized higher privileges.
- **Impact**: Global policy compromise and broad data impact.
- **Controls**:
	- Least privilege, deny-by-default.
	- Separation of duties for admin/security actions.
	- Privileged action monitoring and anomaly alerts.

## 9. Abuse-case catalog

### AC-01: CT/MRI pixel tampering in transit or processing path

- **Scenario**: Adversary modifies image content (e.g., lesion injection/removal).
- **Consequence**: Misdiagnosis, harmful treatment decisions.
- **Prevent/Detect/Respond**:
	- Encrypted/authenticated transport.
	- Mandatory integrity verification before trust-sensitive downstream use.
	- Verification mismatch alerts and incident workflow.

### AC-02: DICOM metadata manipulation

- **Scenario**: Tags altered (patient identity/study context/time fields).
- **Consequence**: Wrong-patient association, fraud, record contamination.
- **Prevent/Detect/Respond**:
	- Metadata capture in integrity anchor.
	- Anomaly checks and consistency validation.
	- Forensic audit correlation with access/policy events.

### AC-03: PACS trust abuse / identity spoof-like behavior at integration boundaries

- **Scenario**: Actor exploits weak trust assumptions in adjacent systems.
- **Consequence**: Unauthorized data access and event injection.
- **Prevent/Detect/Respond**:
	- Explicit identity validation at Imago API boundary.
	- Do not rely on network location as trust signal.
	- Least-privilege adapter credentials and segmentation.

### AC-04: Malware-laced DICOM file ingestion (e.g., preamble abuse class)

- **Scenario**: File crafted to carry executable payload traits.
- **Consequence**: Endpoint/server compromise, lateral movement.
- **Prevent/Detect/Respond**:
	- Import-policy checks including preamble-hygiene outcome recording.
	- Malware scanning controls in ingestion path.
	- Endpoint hardening and restricted execution policies.

### AC-05: Ransomware on metadata/ledger infrastructure

- **Scenario**: Critical stores become encrypted/unavailable.
- **Consequence**: Access/verification/audit outage.
- **Prevent/Detect/Respond**:
	- Immutable/remote backups and tested restore.
	- Segmentation and least privilege for service accounts.
	- Incident command process and post-event chain integrity verification.

### AC-06: Insider abuse of grants/revokes and audit suppression attempts

- **Scenario**: Privileged user modifies policy improperly or attempts concealment.
- **Consequence**: Unauthorized disclosure, forensic blind spots.
- **Prevent/Detect/Respond**:
	- Dual-control/approval for high-risk admin actions.
	- Immutable logging and privileged activity alerts.
	- Regular audit reviews and access recertification.

## 10. Risk register (initial)

| Risk ID | Threat | Likelihood | Impact | Initial Risk | Key Controls | Residual Target |
|---|---|---:|---:|---:|---|---:|
| R-01 | Pixel tampering/misdiagnosis | Medium | Critical | High | Encrypted transport, hash verification, anomaly alerting | Medium |
| R-02 | Metadata tampering | High | High | High | Metadata anchoring, consistency checks, immutable audit | Medium |
| R-03 | Unauthorized access via identity abuse | Medium | High | High | Strong authn/authz, least privilege, MFA, logging | Medium |
| R-04 | DICOM file malware vector | Medium | High | High | Import hygiene checks, scanning, endpoint hardening | Medium |
| R-05 | Ransomware disruption | Medium | Critical | High | Backups, restore drills, segmentation, incident response | Medium |
| R-06 | Insider misuse | Medium | High | High | SoD, privileged monitoring, immutable evidence | Medium |
| R-07 | Supply-chain dependency compromise | Medium | High | High | SBOM, dependency scanning, controlled updates | Medium |

> Quantitative scoring is finalized in `compliance/risk-traceability-matrix.md`.

## 11. Control strategy (defense-in-depth)

### 11.1 Preventive controls

- Strong identity and access control.
- Transport and storage encryption.
- Secure configuration baselines and patching.
- Network segmentation and restricted trust zones.
- Input validation and ingestion policy enforcement.

### 11.2 Detective controls

- Structured, immutable audit logging.
- SIEM-ready telemetry and anomaly rules.
- Verification mismatch events.
- Privileged action alerting and unusual pattern detection.

### 11.3 Corrective/recovery controls

- Incident response runbooks.
- Backup/restore with integrity verification.
- Post-incident reconciliation for audit and lineage continuity.
- Lessons-learned cycle feeding standards and tests.

## 12. Security requirements traceability

Threat-driven requirements map to SRS IDs:

- AC-01/AC-02 → FR-INT-001..007, FR-AUD-001..006, ABR-001..003
- AC-03 → FR-AUTH-001..006, NFR-SEC-003/006, ABR-005
- AC-04 → FR-INT-007, NFR-SEC-001, ABR-004
- AC-05 → FR-SECOPS-004..005, NFR-REL-003, ABR-006
- AC-06 → FR-AUD-006, NFR-SEC-003, ABR-007

## 13. Verification and assurance activities

1. **Security testing**: authz negative tests, tamper simulation, replay and malformed input tests.
2. **Operational drills**: incident tabletop + recovery drills for prolonged outage scenarios.
3. **Audit validation**: verify end-to-end event chain completeness and queryability.
4. **Dependency governance**: recurring vulnerability and SBOM checks.

## 14. Residual risk and assumptions

1. Legacy integration environments may not support all preferred controls natively.
2. Some external references/systems can be partially opaque due to vendor boundaries.
3. Human-factor risk persists; periodic training and drills are required.

Residual risks are accepted only with documented owner, mitigation plan, and review cadence.

## 15. Review cadence

- Quarterly threat model review.
- Immediate review after any major architecture/security incident.
- Annual full refresh aligned with release-gate evidence.

## 16. Informative references used in this model

- `docs/imgkb/gnrl_img_cybersecurity.pdf` (ACR/SIIM white paper)
- `docs/imgkb/tampering_medical_images.md`
- DICOM security guidance and current standard references
- CT-GAN and related medical image tampering literature
- PACS-focused cybersecurity and forensic tampering analyses
