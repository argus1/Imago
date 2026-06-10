# Risk Traceability Matrix

## 1. Document control

- **Project**: Imago
- **Version**: 1.0 (Week 2 baseline)
- **Date**: 2026-06-10
- **Owner**: Imago Engineering
- **Related documents**:
	- `compliance/software-requirements-specification.md`
	- `compliance/threat-model.md`
	- `compliance/software-architecture-and-detailed-design.md`
	- `docs/architecture/context.md`

## 2. Source corpus used for risk prediction

The following project knowledge-base documents were used to derive and prioritize risks:

- `/docs/imgkb/gnrl_img_cybersecurity.pdf`
- `/docs/imgkb/healthcare-technology-security.pdf`
- `/docs/imgkb/IEC 81001-5-1-2021.pdf`
- `/docs/imgkb/Risks/1-s2.0-S1877705812023120-main.pdf`
- `/docs/imgkb/Risks/10278_2010_Article_9311.pdf`
- `/docs/imgkb/Risks/Improving_the_Security_of_Cloud_based_Me.pdf`
- `/docs/imgkb/Risks/Secure_Medical_Image_Sharing_Technologies_Watermarking_Insights_and_Open_Issues.pdf`
- `/docs/imgkb/Risks/Security-Challenges-in-Storing-and-Exchanging-Medical-Information.pdf`
- `/docs/imgkb/tampering_medical_images.md`

Observed dominant themes across this corpus:

1. Medical image tampering (pixel and metadata integrity compromise)
2. Unauthorized access / weak trust boundaries in PACS and exchange paths
3. Cloud storage misconfiguration and insecure data-sharing patterns
4. Malware/ransomware disruption of imaging workflows
5. Auditability gaps reducing forensic confidence
6. Need for robust authenticity evidence (hashes, signatures/watermarking, provenance)

## 3. Scoring model

- **Likelihood**: 1 (rare) to 5 (very likely)
- **Impact**: 1 (low) to 5 (critical)
- **Initial score**: $Likelihood \times Impact$
- **Residual target**: expected risk score after planned controls mature

## 4. Traceability matrix

| Risk ID | Predicted risk statement | Source alignment | L | I | Initial | SRS / Abuse IDs | Controls (implemented / planned) | Implementation evidence | Verification evidence | Residual target | Status / phase |
|---|---|---|---:|---:|---:|---|---|---|---|---:|---|
| R-01 | Adversary tampers with image pixels or object payload (e.g., lesion injection/removal) causing unsafe clinical decisions. | Tampering-focused findings in `tampering_medical_images.md`; imaging integrity concerns in `gnrl_img_cybersecurity.pdf` and Risks folder papers. | 3 | 5 | 15 | FR-INT-001..004, FR-AUD-001..005, ABR-003 | **Implemented:** SHA-256 ingest hashing, append-only hash-linked chain verification. **Planned:** external scanner signature validation and pre-use verify gates. | `src/imago/storage/ingestion.py`, `src/imago/ledger/chain.py` | `tests/unit/test_chain.py`, `tests/unit/test_ingestion_service.py` | 8 | Active; Week 3-4 hardening |
| R-02 | DICOM metadata tampering (patient ID, study context, timestamps) causes wrong-patient attribution and fraud. | Metadata manipulation emphasis in `tampering_medical_images.md`; storage/exchange security literature in Risks subfolder. | 4 | 5 | 20 | FR-REG-002, FR-INT-006, FR-AUD-002..006, ABR-002 | **Implemented:** metadata/object hash anchoring path and immutable event writes. **Planned:** metadata anomaly checks and stricter DICOM semantic validation. | `src/imago/storage/contracts.py`, `src/imago/storage/ingestion.py`, `src/imago/domain/events.py` | `tests/unit/test_ingestion_service.py` | 10 | Active; Week 3+ |
| R-03 | Unauthorized access from weak boundary trust (implicit PACS/network trust, weak authz) exposes restricted clinical data. | Access-control themes in Risks papers; trust-boundary issues in `tampering_medical_images.md` and healthcare security PDFs. | 4 | 5 | 20 | FR-AUTH-001..006, NFR-SEC-003..004, ABR-005 | **Implemented:** classification model and strict request contracts. **Planned:** full authn/authz policy engine enforcement and IdP integration. | `src/imago/storage/policy.py`, `src/imago/api/models.py`, `src/imago/domain/models.py` | `tests/unit/test_storage_policy.py`, `tests/unit/test_domain_models.py` | 9 | Open; Week 3-4 |
| R-04 | Cloud object storage misconfiguration (public exposure, weak lifecycle, missing encryption/versioning) leaks or corrupts image evidence. | Strong cloud-storage focus in `Improving_the_Security_of_Cloud_based_Me.pdf` and `1-s2.0-S1877705812023120-main.pdf`. | 4 | 4 | 16 | NFR-SEC-002, NFR-SEC-005, NFR-COMP-003, FR-SECOPS-004 | **Implemented:** dormant AWS baseline with public access block, SSE, versioning, archival lifecycle. **Planned:** policy-as-code drift detection and periodic compliance checks in CI/ops. | `docs/operations/runbook.md`, `docs/architecture/context.md` | Manual AWS verification evidence captured in terminal session and runbook controls | 7 | Mitigated baseline; ongoing ops |
| R-05 | Ransomware/malware disrupts metadata or ledger infrastructure, reducing availability and trust in records. | Resilience/ransomware emphasis in `gnrl_img_cybersecurity.pdf` and `healthcare-technology-security.pdf`. | 3 | 5 | 15 | FR-SECOPS-004..005, NFR-REL-001..003, ABR-006 | **Implemented:** append-only ledger verification and operational runbook baselines. **Planned:** restore drills, immutable backups, incident tabletop exercises. | `src/imago/ledger/chain.py`, `docs/operations/runbook.md` | `tests/unit/test_chain.py` | 8 | Open; Week 4+ |
| R-06 | Incomplete audit trails or weak event correlation prevent forensic reconstruction and non-repudiation. | Audit/forensics importance across healthcare cybersecurity papers and threat literature. | 3 | 4 | 12 | FR-AUD-001..006, NFR-COMP-002, ABR-007 | **Implemented:** immutable event model and chain verification hooks. **Planned:** full audit query/export APIs and SIEM streaming with correlation IDs. | `src/imago/domain/events.py`, `src/imago/ledger/chain.py` | `tests/unit/test_chain.py` | 6 | Open; Week 4 |
| R-07 | Ingestion partial failure causes inconsistent state (binary written without metadata or ledger event), weakening integrity claims. | Data-consistency and secure-exchange concerns in Risks corpus; high relevance to healthcare evidence integrity. | 3 | 4 | 12 | FR-REG-006, NFR-REL-002 | **Implemented:** atomic coordinator with compensation rollback. **Planned:** durable transaction boundaries once persistent stores replace in-memory adapters. | `src/imago/storage/ingestion.py`, `src/imago/storage/contracts.py` | `tests/unit/test_ingestion_service.py` | 5 | Mitigated baseline |
| R-08 | Path traversal or unsafe storage key handling enables unauthorized filesystem/object access. | Storage/exchange security challenges in Risks papers; common exploit class in healthcare integrations. | 3 | 4 | 12 | FR-REG-003, NFR-SEC-003 | **Implemented:** filesystem adapter traversal prevention. **Planned:** equivalent safeguards in all cloud/PACS adapters. | `src/imago/storage/filesystem.py` | `tests/unit/test_filesystem_storage.py` | 5 | Mitigated baseline |
| R-09 | Secrets exposure in source control/CI logs enables account takeover and data compromise. | Healthcare technology security guidance and cloud-risk papers consistently emphasize credential hygiene. | 4 | 4 | 16 | NFR-SEC-002, NFR-QUAL-002, NFR-COMP-003 | **Implemented:** local secret file ignored, template-only credentials committed, CI secret scan in GitHub Actions. **Planned:** key rotation policy enforcement and vault integration. | `.gitignore`, `aws-devicefarm-credentials.env.example`, `.github/workflows/ci.yml` | CI security job (`detect-secrets`) | 6 | Partially mitigated; key rotation pending |
| R-10 | Dependency or supply-chain compromise introduces vulnerable code paths into production artifacts. | Security governance themes in healthcare cybersecurity papers; explicit dependency-governance need in project docs. | 3 | 4 | 12 | NFR-QUAL-002, FR-SECOPS-003, ABR-006 | **Implemented:** CI dependency vulnerability scan and SAST/security gates in GitHub Actions. **Planned:** SBOM publishing and signed artifact attestations. | `.github/workflows/ci.yml` | CI security job (`pip-audit`, `bandit`, SARIF upload) | 5 | Mitigated baseline |
| R-11 | Authenticity proof gap for externally sourced images (no signature/watermark verification) leaves blind spot against high-fidelity forgery. | Watermarking/authenticity emphasis in `Secure_Medical_Image_Sharing_Technologies_Watermarking_Insights_and_Open_Issues.pdf`. | 3 | 4 | 12 | FR-INT-005, FR-LIN-001..004 | **Implemented:** hash anchoring and lineage model direction. **Planned:** signature-validation metadata capture and watermark-verification pipeline integration. | `compliance/software-requirements-specification.md`, `src/imago/domain/models.py` | Planned integration/system tests (not yet present) | 7 | Open; Week 4+ |
| R-12 | Legacy interoperability assumptions (DICOM/PACS integration variance) create inconsistent control enforcement across sites. | Interoperability and legacy-stack issues in Risks PDFs (`10278_2010_Article_9311.pdf`, cloud/exchange papers). | 3 | 3 | 9 | FR-API-003, NFR-SEC-006, NFR-COMP-001 | **Implemented:** adapter abstraction and classification policy boundaries. **Planned:** adapter conformance tests and deployment security profiles per integration mode. | `src/imago/storage/contracts.py`, `src/imago/api/dependencies.py`, `src/imago/storage/policy.py` | Existing unit tests around adapters/policy; integration conformance tests pending | 5 | Open; Week 4+ |

## 5. Week 1-3 compliance overlay summary

This matrix overlays predicted external risks onto current implementation maturity:

- **Week 1 posture** improved storage misconfiguration risk (R-04) via dormant S3 controls.
- **Week 2 posture** improved supply-chain and secret exposure controls (R-09, R-10) via GitHub Actions security gates.
- **Week 3 focus recommendation** should prioritize R-01/R-02/R-03 (tampering + metadata integrity + authz) because they retain highest residual risk and strongest patient-safety impact.

## 6. Verification backlog derived from matrix

1. Add negative tests for authorization denial paths (R-03).
2. Add metadata anomaly detection test vectors (R-02).
3. Add integration-level backup/restore drill evidence (R-05).
4. Add signature/watermark authenticity checks in verification flow (R-11).
5. Generate and store SBOM evidence linked to CI runs (R-10).

## 7. Review cadence

- Update this matrix at least once per sprint (or weekly during accelerated catch-up).
- Re-score risks after major architecture/security changes.
- Require release-gate sign-off that residual high risks have explicit owners and mitigation plans.
