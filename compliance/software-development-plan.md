# Software Development Plan

## 1. Document control

- **Project**: Imago
- **Version**: 1.0 (Draft baseline)
- **Date**: 2026-06-10
- **Owner**: Imago Engineering
- **Related documents**:
	- `DevPlan.md`
	- `compliance/software-requirements-specification.md`
	- `compliance/software-architecture-and-detailed-design.md`
	- `compliance/threat-model.md`
	- `compliance/risk-traceability-matrix.md`
	- `compliance/secure-coding-standard.md`
	- `compliance/release-gate-checklist.md`
	- `docs/operations/runbook.md`

## 2. Purpose

This Software Development Plan (SDP) defines how Imago is designed, implemented, verified, released, and maintained with compliance-first engineering practices.

The SDP ensures:

1. Development is traceable from requirements to code and tests.
2. Security controls are integrated throughout the lifecycle.
3. Release approvals are evidence-based rather than ad hoc.

## 3. Product scope summary

Imago is a permissioned medical image-access ledger that:

- stores immutable integrity and governance events in-ledger
- stores image binaries off-ledger in controlled storage
- supports clinical DICOM and research/derived imaging workflows with classification-aware policy controls

The detailed scope is defined in `DevPlan.md` and SRS requirement IDs in `compliance/software-requirements-specification.md`.

## 4. Lifecycle model

Imago uses an incremental, evidence-driven lifecycle with gated phases:

1. **Foundation reset** (project structure/tooling baseline)
2. **Requirements, risk, architecture baseline**
3. **Core ledger and policy engine**
4. **API and storage integration**
5. **Security and operational controls**
6. **Validation and release readiness**

Each phase closes only when documented exit criteria and verification evidence are complete.

## 5. Roles and responsibilities

### 5.1 Engineering owner

- Maintains roadmap execution and technical decisions.
- Ensures architecture and implementation align with SRS and threat model.

### 5.2 Security/compliance owner

- Maintains threat model, risk traceability matrix, and secure coding baseline.
- Reviews deviations/waivers and tracks remediation deadlines.

### 5.3 Reviewer/approver

- Performs code review and compliance artifact review.
- Verifies evidence quality for release gates.

### 5.4 Release owner

- Confirms all gate criteria are satisfied.
- Approves tagged releases and deployment records.

In small-team operation, one person may hold multiple roles, but responsibilities remain distinct and auditable.

## 6. Development practices

### 6.1 Branching and change control

- Primary integration branch: `master` (repository current state).
- Every change must be linked to a task/requirement/risk reference where applicable.
- Protected-branch controls and required reviews should be enabled at repository settings level.

### 6.2 Code standards

- Secure coding requirements are defined in `compliance/secure-coding-standard.md`.
- Python/FastAPI code must use strict input models and deny-by-default security posture.
- Secrets in code are prohibited.

### 6.3 Configuration management

- Environment-driven configuration via settings modules and template files.
- Local secret files remain untracked; template files are tracked.
- Security-relevant configuration changes require review and traceability.

## 7. Verification strategy

Verification must map to requirement IDs and risk controls.

### 7.1 Test levels

- **Unit**: module-level behavior and invariants (fast feedback).
- **Integration**: cross-module interactions and end-to-end flow segments.
- **System**: externally observable behavior against major use cases.

### 7.2 Security verification

- Negative authorization tests
- Tamper/integrity tests (hash and chain behavior)
- Input/path safety tests
- CI security scanning (dependency, secrets, SAST)

### 7.3 Evidence retention

Verification evidence includes:

- CI run records
- test outputs
- traceability matrix updates
- release gate decisions

Evidence should be retained with links in compliance documents and release records.

## 8. CI/CD and quality gates

GitHub Actions is the primary CI mechanism.

### 8.1 Required CI gates

1. Lint (`ruff`)
2. Type checks (`mypy`)
3. Unit/integration/system tests (`pytest`)
4. Dependency vulnerability scan
5. Secret scan
6. SAST scan and report upload

Any failed gate blocks merge/release unless a documented, time-bound waiver is approved.

### 8.2 Release gates

Release gates require:

- all CI gates green
- updated risk traceability status
- no unresolved critical security findings without approved waiver
- release checklist approval

## 9. Requirements and risk traceability

Imago maintains bidirectional traceability:

- SRS requirement ID -> implementation/test evidence
- Risk ID -> controls -> implementation/test evidence

Primary traceability artifacts:

- `compliance/software-requirements-specification.md`
- `compliance/threat-model.md`
- `compliance/risk-traceability-matrix.md`

## 10. Defect and vulnerability management

### 10.1 Defect handling

- Defects are logged with severity, scope, and affected requirement/risk links.
- Critical/high defects require expedited remediation and validation.

### 10.2 Vulnerability handling

- Vulnerabilities from CI scans are triaged by severity and exploitability.
- Secret exposures trigger immediate containment and credential rotation.
- Closure requires code/config fix and verification evidence.

## 11. Security and privacy controls in development

Development activities must enforce:

1. Least privilege and role separation where possible.
2. Encryption and secure channels in deployment contexts.
3. Minimal PHI handling in logs and test data.
4. Explicit auditability for privileged and security-sensitive actions.

## 12. Documentation deliverables and maintenance

The following compliance artifacts are maintained in-repo and updated as the system evolves:

- Software Development Plan (this document)
- SRS
- Architecture and Detailed Design
- Threat Model
- Risk Traceability Matrix
- Secure Coding Standard
- SBOM and Dependency Register
- Release Gate Checklist

Placeholder documents must be completed before their corresponding release gate is approved.

## 13. Milestone plan alignment

This SDP aligns with the roadmap in `DevPlan.md`:

- **Week 1**: package/tooling and storage strategy baseline
- **Week 2**: SRS/threat model/domain schema/CI security gates
- **Week 3**: ledger and policy engine hardening + focused unit tests
- **Week 4**: API expansion, integration tests, release checklist publication

Progress and closure records should be captured in `docs/architecture/week*-closure.md` artifacts.

Current closure state (2026-06-13):

- Week 1: Closed (`docs/architecture/week1-closure.md`)
- Week 2: Closed (`docs/architecture/week2-closure.md`)
- Week 3: Closed for current implementation slice (`docs/architecture/week3-closure.md`)

## 14. Entry and exit criteria summary

### 14.1 Development entry criteria

- Requirement/risk context identified.
- Design impact assessed.
- Security implications identified.

### 14.2 Development exit criteria

- Code merged with required review.
- Relevant tests added/updated and passing.
- CI security gates passed.
- Traceability artifacts updated as needed.

### 14.3 Release exit criteria

- Release checklist approved.
- Residual risks documented and accepted by owner.
- Deployment evidence and version record archived.

## 15. Metrics and reporting

Track at minimum:

- CI pass/fail rate
- open critical/high vulnerabilities
- requirements with linked tests (% coverage by traceability)
- unresolved release-gate blockers

Metrics are reviewed during release readiness and periodic compliance reviews.

## 16. Exceptions and waivers

Exceptions are allowed only when:

1. risk is documented with owner and expiry,
2. compensating controls are defined,
3. remediation issue is scheduled,
4. approval is recorded in release evidence.

Critical security waivers without expiry are prohibited.

## 17. Review cadence

- Review this SDP at least quarterly.
- Trigger immediate review after major incident, architectural shift, or regulatory requirement change.
