# Secure Coding Standard

## 1. Document control

- **Project**: Imago
- **Version**: 1.0 (Draft baseline)
- **Date**: 2026-06-10
- **Owner**: Imago Engineering
- **Applies to**: all source code, infrastructure-as-code, CI workflows, and scripts in this repository.
- **Related documents**:
	- `compliance/software-requirements-specification.md`
	- `compliance/threat-model.md`
	- `compliance/risk-traceability-matrix.md`
	- `compliance/sbom-and-dependency-register.md`
	- `docs/operations/runbook.md`
	- `docs/imgkb/tampering_medical_images.md`
	- `docs/imgkb/gnrl_img_cybersecurity.pdf`

## 2. Purpose

This standard defines mandatory secure coding requirements for Imago, a permissioned medical image access ledger.

Primary goals:

1. Protect confidentiality, integrity, and availability of restricted clinical imaging data.
2. Prevent tampering, unauthorized access, and data leakage.
3. Provide reproducible evidence for healthcare cybersecurity audits and release gates.

## 3. Scope and technology baseline

The current implementation baseline is Python + FastAPI with:

- request models and validation
- storage adapters (filesystem now, cloud/PACS adapters planned)
- append-only hash-linked ledger logic
- CI security scanning in GitHub Actions

This standard is mandatory for:

- `src/imago/**`
- `tests/**` (excluding intentionally malicious test payload fixtures)
- `.github/workflows/**`
- `scripts/**`

## 4. Compliance alignment

This standard is aligned with:

- IEC 81001-5-1 style secure lifecycle expectations for health software
- HIPAA-aligned technical safeguards for confidentiality and access control
- SRS security requirements (`NFR-SEC-*`, `NFR-QUAL-002`, `FR-AUTH-*`, `FR-INT-*`, `FR-AUD-*`)

## 5. Severity model and policy language

- **MUST**: mandatory requirement; non-compliance blocks merge/release.
- **SHOULD**: expected default; deviations require documented rationale.
- **MAY**: optional enhancement.

Severity levels:

- **Critical**: immediate patient-safety or data-exposure risk.
- **High**: significant exploitability or control bypass risk.
- **Medium**: meaningful hardening or reliability risk.
- **Low**: hygiene/documentation/maintainability gap.

## 6. Mandatory secure coding requirements

### 6.1 Identity, authentication, and authorization

1. All externally reachable endpoints that modify or disclose protected data **MUST** enforce authenticated identity and explicit authorization checks.
2. Authorization decisions **MUST** be deny-by-default and classification-aware.
3. Privileged operations (policy updates, admin actions) **MUST** emit auditable events.
4. Hardcoded credentials, static API keys in code, and shared admin identities **MUST NOT** be used.

### 6.2 Input handling and data validation

1. All request payloads **MUST** be schema-validated.
2. Unknown/unexpected fields **MUST** be rejected for security-sensitive APIs.
3. File/object keys **MUST** be validated against traversal and unsafe path patterns.
4. Type coercions that can silently alter semantics **SHOULD** be avoided in security-critical flows.

### 6.3 Cryptography and integrity

1. Cryptographic primitives **MUST** come from approved modern libraries and algorithms.
2. Security decisions **MUST NOT** depend on non-cryptographic hashes or reversible obfuscation.
3. Medical image and metadata integrity controls **MUST** use deterministic cryptographic hashing.
4. Security-sensitive random values **MUST** use cryptographically secure randomness.

### 6.4 Secrets and key management

1. Secrets **MUST NOT** be committed to source control.
2. Local secret files **MUST** be ignored via `.gitignore` and replaced with tracked templates where needed.
3. Rotation procedures **MUST** exist for leaked or expiring credentials.
4. CI logs **MUST NOT** print secrets or full tokens.

### 6.5 Data protection (PHI/ePHI handling)

1. Sensitive data **MUST** be minimized in logs, errors, and telemetry.
2. In-transit communication **MUST** use encrypted channels in deployment environments.
3. At-rest storage for protected data **MUST** be encrypted using platform-supported controls.
4. Non-diagnostic derivatives **MUST** remain linked to source provenance.

### 6.6 Storage and file safety

1. Storage adapters **MUST** prevent directory traversal and unsafe object paths.
2. Ingestion operations **MUST** preserve atomicity guarantees or apply compensation to avoid partial security states.
3. Lifecycle and retention settings for archival tiers **SHOULD** be configured to reduce exposure and cost while preserving auditability.

### 6.7 Logging, auditability, and observability

1. Security-relevant events **MUST** be logged with actor, action, resource, timestamp, and outcome.
2. Logs **MUST** avoid PHI leakage and secret material.
3. Tamper-evident audit patterns **MUST** be preserved for critical actions.
4. Correlation identifiers **SHOULD** be used across API and background paths.

### 6.8 Dependency and supply chain security

1. Dependency vulnerability scanning **MUST** run in CI.
2. Static analysis for security findings **MUST** run in CI.
3. Secret scanning **MUST** run in CI.
4. Dependency updates for critical/high vulnerabilities **MUST** be prioritized.
5. SBOM/dependency register **SHOULD** be maintained and refreshed per release.

### 6.9 Safe error handling

1. Production responses **MUST** not disclose internal stack traces, secrets, or infrastructure details.
2. Exceptions in security-sensitive code paths **MUST** fail closed where practical.
3. Retry logic **SHOULD** avoid unbounded loops and unsafe duplicate side effects.

### 6.10 Testing and verification requirements

1. Unit tests **MUST** cover negative and unauthorized paths for critical security logic.
2. Integrity and tamper-detection tests **MUST** exist for ledger and ingestion invariants.
3. Filesystem/storage safety tests **MUST** include traversal and invalid key cases.
4. CI security gates **MUST** pass before merge.

## 7. Python and FastAPI secure coding profile

### 7.1 Python-specific bans

The following are disallowed for untrusted input handling:

- unsafe deserialization (`pickle`, `marshal`) for external data
- dynamic code execution from untrusted sources (`eval`, `exec`)
- shell command construction using string interpolation with user input

### 7.2 FastAPI-specific controls

1. Request/response models **MUST** enforce strict validation.
2. Production configuration **MUST** disable debug-like verbose error disclosure.
3. CORS policy **MUST** be explicit; wildcard origins in production are prohibited.
4. Auth and authorization dependencies **SHOULD** be centralized for consistency.

## 8. Code review checklist (mandatory)

Each pull request reviewer must verify:

1. No secrets or sensitive test data are introduced.
2. Input validation exists for all new external inputs.
3. Authorization checks are present where required.
4. Error handling does not leak internals.
5. New dependencies are justified and scanned.
6. Security-relevant changes include tests.
7. Changes maintain traceability to SRS/threat/risk artifacts where applicable.

## 9. CI enforcement baseline

The CI pipeline is expected to enforce:

- linting and type checks
- unit/integration/system tests
- dependency vulnerability scan
- secret scan
- SAST scan and report upload

Any failed security gate blocks merge until resolved or formally waived.

## 10. Exception and waiver process

Temporary exceptions are allowed only when:

1. business/clinical urgency is documented,
2. compensating controls are defined,
3. risk owner and expiration date are recorded,
4. follow-up remediation issue is linked.

Unbounded or permanent waivers for critical findings are prohibited.

## 11. Traceability map (standard -> SRS/threat)

- Input validation and path safety -> FR-REG-003, FR-REG-006, ABR-002
- Authz and least privilege -> FR-AUTH-001..006, NFR-SEC-003
- Integrity and tamper evidence -> FR-INT-001..007, FR-AUD-001..006, ABR-003
- Secrets management -> NFR-SEC-002, NFR-QUAL-002
- Logging and accountability -> FR-AUD-002, FR-AUD-006, NFR-COMP-002
- Resilience and recovery -> FR-SECOPS-004..005, NFR-REL-003, ABR-006

## 12. Review cadence

- Review this standard at least quarterly.
- Trigger immediate review after major incidents, architecture changes, or new regulatory constraints.
- Align updates with release-gate approvals.

## 13. References used for this baseline

Project-local sources:

- `docs/secure_coding_standard-medical.md`
- `docs/imgkb/tampering_medical_images.md`
- `docs/imgkb/radiology_pipeline.md`
- `docs/imgkb/components_pacs.md`
- `docs/imgkb/gnrl_img_cybersecurity.pdf`
- `compliance/software-requirements-specification.md`
- `compliance/threat-model.md`
- `compliance/risk-traceability-matrix.md`
