# SBOM and Dependency Register

## 1. Document control

- **Project**: Imago
- **Version**: 1.0 (Week 5 implementation baseline)
- **Date**: 2026-06-15
- **Owner**: Imago Engineering / Security & Compliance
- **Related documents**:
	- `docs/imgkb/SBOM_guidance_document.md`
	- `docs/imgkb/2025_CISA_SBOM_Minimum_Elements.pdf`
	- `compliance/software-development-plan.md`
	- `compliance/risk-traceability-matrix.md`
	- `.github/workflows/ci.yml`
	- `pyproject.toml`

## 2. Purpose and scope

This document defines how Imago satisfies SBOM and dependency-governance expectations and records the current dependency baseline for the repository.

Scope includes:

1. SBOM minimum-element compliance posture aligned to CISA 2025 draft guidance.
2. SBOM generation, update, and delivery process.
3. Dependency inventory for runtime, optional feature, and development/security tooling.
4. Risk-oriented tracking fields for dependency review and release gating.

## 3. Guidance corpus used

The following internal references were reviewed to produce this compliance artifact:

1. `docs/imgkb/SBOM_guidance_document.md` (project guidance summary and terminology)
2. `docs/imgkb/2025_CISA_SBOM_Minimum_Elements.pdf` (authoritative 2025 minimum-elements draft)

Key points adopted from the 2025 CISA guidance:

- Minimum elements are grouped into **Data Fields**, **Automation Support**, and **Practices/Processes**.
- New/updated data expectations include **Component Hash**, **License**, **Tool Name**, and **Generation Context**.
- Coverage should include transitive dependencies where available.
- Known Unknowns must be explicit and distinguish unknown from intentionally redacted content.
- SBOMs should be issued per release/update and corrected when errors are found.

## 4. Imago SBOM compliance profile (CISA 2025 crosswalk)

| CISA minimum element | Imago implementation requirement | Current implementation / evidence | Status |
|---|---|---|---|
| SBOM Author | Identify entity generating SBOM | SBOM producer set to Imago Engineering in generated artifact metadata (process-defined) | Planned/Process-defined |
| Software Producer | Identify software producer per component | Project producer is `Imago Team` (`pyproject.toml`) | Implemented |
| Component Name | Human-readable package/component names | Derived from package manifest and SBOM tool output | Implemented |
| Component Version | Version per component | Versions resolved by SBOM tooling from environment/lock context | Implemented (at generation time) |
| Software Identifiers | Include at least one identifier (prefer purl/CPE) | CycloneDX/SPDX tooling used to emit package identifiers (purl expected) | Planned/Process-defined |
| Component Hash | Cryptographic hash when artifact available | File/package hash support required in generated SBOM when available | Planned |
| License | License per component or unknown | Captured from package metadata; unknown explicitly marked | Planned |
| Dependency Relationship | Express inclusion/dependency graph | SBOM output must preserve direct and transitive relationships | Planned |
| Tool Name | Record SBOM tool(s) used | Tool name/version recorded in SBOM metadata | Planned |
| Timestamp | ISO 8601 timestamp for latest update | Generation timestamp required in output artifact | Planned |
| Generation Context | Before-build / during-build / after-build | Imago baseline target: **after-build** (environment-resolved) | Planned |
| Automation Support | Use machine-processable interoperable formats | CycloneDX JSON (primary) and SPDX JSON (secondary/accepted) | Process-defined |
| Frequency | Regenerate for each release/update | Required at each tagged release and dependency change | Process-defined |
| Coverage | Include all components incl. transitive dependencies | Direct dependencies are enumerated in this register; transitive coverage delegated to generation tool output | Partially implemented |
| Known Unknowns | Explicitly mark incomplete or redacted data | Section 6 defines Known Unknowns policy and current gaps | Implemented |
| Distribution and Delivery | Make SBOM available to authorized stakeholders promptly | SBOM artifact to be stored with release artifacts / CI evidence bundle | Planned |
| Accommodation of Updates | Correct SBOM errors and republish | Release process requires SBOM refresh on dependency/security updates | Process-defined |

## 5. Dependency register (current baseline)

Source of truth for declared dependencies is `pyproject.toml`. The table below records currently declared top-level dependencies and governance status.

### 5.1 Runtime dependencies (core)

| Package | Declared constraint | Role in Imago | Criticality | Review status |
|---|---|---|---|---|
| fastapi | `>=0.116.0` | API framework for service endpoints | High | Approved baseline |
| pydantic-settings | `>=2.4.0` | Configuration and environment parsing | Medium | Approved baseline |
| uvicorn[standard] | `>=0.30.0` | ASGI runtime/server | High | Approved baseline |

### 5.2 Optional runtime dependencies (feature groups)

#### imaging extra

| Package | Declared constraint | Role in Imago | Criticality | Review status |
|---|---|---|---|---|
| nibabel | `>=5.2.0` | Neuroimaging/NIfTI support for imaging workflows | Medium | Approved baseline |
| numpy | `>=1.26.0` | Numerical processing dependency | High | Approved baseline |
| pydicom | `>=3.0.0` | DICOM parsing and handling | High | Approved baseline |
| zarr | `>=2.18.0` | Chunked array storage access | Medium | Approved baseline |

#### storage extra

| Package | Declared constraint | Role in Imago | Criticality | Review status |
|---|---|---|---|---|
| boto3 | `>=1.35.0` | AWS object storage integration | High | Approved baseline |
| google-cloud-storage | `>=2.18.0` | GCS storage integration | High | Approved baseline |
| minio | `>=7.2.0` | S3-compatible storage integration | Medium | Approved baseline |
| psycopg[binary] | `>=3.2.0` | PostgreSQL integration capability | High | Approved baseline |

### 5.3 Development and quality dependencies

| Package | Declared constraint | Role in lifecycle | Review status |
|---|---|---|---|
| httpx | `>=0.28.1` | HTTP client for tests/tooling | Approved baseline |
| mypy | `>=1.11.0` | Static typing checks | Approved baseline |
| pre-commit | `>=3.8.0` | Local policy/quality hooks | Approved baseline |
| pytest | `>=8.3.0` | Unit/integration/system tests | Approved baseline |
| ruff | `>=0.6.0` | Lint/format policy checks | Approved baseline |

### 5.4 Security scanning tools used in CI

Installed in CI security job (`.github/workflows/ci.yml`):

- `pip-audit` (dependency vulnerability scanning)
- `bandit` (SAST for Python)
- `detect-secrets` (secret detection)

These tools are part of the dependency-governance control plane and are required release-gate evidence inputs.

## 6. Known unknowns and assumptions

In alignment with CISA 2025 Known Unknowns guidance:

1. **Transitive dependency inventory** is not fully enumerated in this static register; it is expected from generated CycloneDX/SPDX artifacts at build/release time.
2. **Per-component license values** are not embedded in this static table; licenses must be captured by SBOM tooling and reviewed during release.
3. **Component hashes** are generated where artifact-level hashes are available through tooling; missing hashes must be reported as unknown rather than omitted silently.
4. **Redaction policy**: no dependency metadata should be intentionally redacted for internal compliance review. If any external distribution requires redaction, rationale and owner approval must be documented.

## 7. SBOM generation and delivery process

### 7.1 Generation triggers

Generate/refresh SBOM when any of the following occurs:

1. Tagged release or deployment candidate.
2. Any change to dependency declarations in `pyproject.toml`.
3. Security patching of direct/transitive dependencies.
4. Material correction to previously published SBOM data.

### 7.2 Required output characteristics

Generated SBOM artifacts must:

- be machine-processable (CycloneDX JSON minimum; SPDX JSON accepted)
- include timestamp in ISO 8601 format
- include direct and transitive dependency relationships (where tool support exists)
- include tool metadata (name/version)
- include explicit unknown markers for missing required values

### 7.3 Distribution and retention

- Store SBOM artifacts with CI/release evidence bundles.
- Link SBOM artifact location from release records and compliance review notes.
- Retain SBOMs for each released version to support vulnerability back-tracing.

## 8. Verification and release-gate checks

The following checks are mandatory before release approval:

1. CI security job passes (`pip-audit`, `bandit`, `detect-secrets`).
2. SBOM artifact generated for release candidate.
3. No unresolved critical/high dependency vulnerabilities without approved waiver.
4. Known Unknowns section reviewed and accepted by compliance owner.
5. Dependency register updated if top-level dependency set changed.

## 9. Open actions

1. Add explicit SBOM artifact generation step in CI pipeline and publish as build artifact.
2. Add automated validation for required CISA data fields (schema + custom policy checks).
3. Add release checklist item linking each release tag to its SBOM artifact URI.

## 10. Review cadence

- Review this document at least once per sprint, and always before release.
- Update immediately after dependency changes, new security findings, or SBOM process/tooling changes.
