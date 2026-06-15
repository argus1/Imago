# Medical Software Release Gate Checklist (Go/No-Go)

Date: ____________________  
Release ID/Tag: ____________________  
Target Environment: ____________________  
Release Owner: ____________________

## Purpose

This checklist is the formal release gate record for Imago. A release is approved only when all mandatory gates are **Pass** or have an approved, time-bounded waiver with explicit residual-risk acceptance.

## Gate decision rules

- **PASS**: Required evidence exists, is current for this release, and is approved.
- **CONDITIONAL PASS**: Non-critical gap accepted with waiver, owner, expiration, and remediation due date.
- **FAIL**: Missing/invalid evidence, unresolved critical issue, or unapproved high residual risk.
- **NO-GO** triggers:
  - Any gate in **FAIL** status.
  - Any unresolved critical security finding without approved waiver.
  - Missing required sign-offs.

## Release candidate metadata

- Change summary / release scope: __________________________________________
- Linked ticket(s): ______________________________________________________
- Build artifact identifier(s): ____________________________________________
- Deployment window: _____________________________________________________

## Mandatory release gates

| Gate ID | Gate | Required evidence (repository artifacts) | Owner | Status (Pass / Conditional / Fail) | Notes / Waiver ID |
|---|---|---|---|---|---|
| RG-001 | Requirements baseline current | `compliance/software-requirements-specification.md` updated for release scope; requirement IDs remain testable and unique | Product + Engineering |  |  |
| RG-002 | Architecture/design baseline current | `compliance/software-architecture-and-detailed-design.md` reflects implemented behavior and known limits | Engineering |  |  |
| RG-003 | Threat model current | `compliance/threat-model.md` reviewed/updated for new attack surfaces and trust-boundary changes | Security |  |  |
| RG-004 | Risk traceability complete | `compliance/risk-traceability-matrix.md` maps top risks to controls, implementation evidence, and verification evidence | Security + Compliance |  |  |
| RG-005 | SBOM/dependency governance complete | `compliance/sbom-and-dependency-register.md` updated; CI dependency/security evidence attached (`pip-audit`, `bandit`, secret scan) | Security + DevOps |  |  |
| RG-006 | Secure coding/process conformance | `compliance/secure-coding-standard.md` and `docs/secure_coding_standard-medical.md` reviewed for release-impacting changes | Engineering Lead |  |  |
| RG-007 | Test evidence sufficient | Latest automated evidence for unit/integration/system tests with no unresolved critical failures | QA + Engineering |  |  |
| RG-008 | Verification/validation evidence complete | V&V results confirm intended use and safety-relevant behavior for release scope | QA + Compliance |  |  |
| RG-009 | Defect/anomaly review completed | Open defects are triaged; safety/critical defects are closed or explicitly waived with rationale | Engineering + Safety/Compliance |  |  |
| RG-010 | Security controls effective | Authentication/authorization, integrity checks, and audit-event integrity controls validated for release scope | Security |  |  |
| RG-011 | Documentation & operations readiness | `docs/operations/runbook.md`, API docs (`docs/api/*`), and release notes/deployment procedures are current | Operations + Engineering |  |  |
| RG-012 | Residual risk acceptance signed | Any remaining high risks have named owner, mitigation plan, due date, and approver sign-off | Compliance + Release Approver |  |  |

## Evidence checklist (attach or link)

- [ ] CI run URL(s) and commit SHA(s): ______________________________________
- [ ] Unit/integration/system test reports: __________________________________
- [ ] Security scan reports (SAST/dependency/secrets): ________________________
- [ ] SBOM artifact and dependency review notes: ______________________________
- [ ] Threat/risk review record and approvals: ________________________________
- [ ] Defect/anomaly report with disposition: _________________________________
- [ ] Release notes and deployment plan: _____________________________________
- [ ] Rollback plan validated: _______________________________________________

## Known gaps and waivers

Record every gate that is not full PASS.

| Waiver ID | Related Gate | Description of gap | Risk level | Owner | Mitigation due date | Expiration date | Approver |
|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |

## Final decision and sign-off

- Final decision: **GO / NO-GO**
- Decision date/time: __________________________________________
- Release Owner sign-off: ______________________________________
- Engineering Approver sign-off: ________________________________
- Security/Compliance Approver sign-off: ________________________
- QA/Validation Approver sign-off: ______________________________

## Post-release verification (complete within agreed window)

- [ ] Deployment completed as planned.
- [ ] Smoke checks and health endpoints verified.
- [ ] No critical post-release incidents in monitoring window.
- [ ] Audit trail and evidence package archived for compliance review.
