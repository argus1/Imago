import base64
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from imago.api.dependencies import get_ingestion_service, get_policy_engine
from imago.config.settings import get_settings
from imago.main import create_app


def _auth_headers(
    *,
    principal_id: str = "user-1",
    org_id: str = "org-1",
    role: str = "radiologist",
    principal_type: str = "user",
) -> dict[str, str]:
    return {
        "X-Imago-Principal-Id": principal_id,
        "X-Imago-Org-Id": org_id,
        "X-Imago-Role": role,
        "X-Imago-Principal-Type": principal_type,
    }


@pytest.mark.integration
def test_ingest_endpoint_returns_created_with_classification(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("IMAGO_STORAGE_BACKEND", "filesystem")
    monkeypatch.setenv("IMAGO_STORAGE_ROOT", str(tmp_path))
    get_settings.cache_clear()
    get_ingestion_service.cache_clear()
    get_policy_engine.cache_clear()

    app = create_app()
    client = TestClient(app)

    payload = base64.b64encode(b"mock-dicom-payload").decode("ascii")
    response = client.post(
        "/api/v1/images/ingest",
        json={
            "object_key": "study-1/series-1/image-1.dcm",
            "content_type": "application/dicom",
            "uploaded_by": "integration-user",
            "format_name": ".dcm",
            "payload_b64": payload,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["object_key"] == "study-1/series-1/image-1.dcm"
    assert data["classification"] == "restricted_clinical"
    assert data["format_family"] == "dicom"
    assert data["metadata_id"].startswith("meta-")
    assert data["ledger_event_id"].startswith("evt-")
    assert len(data["object_hash"]) == 64

    saved = tmp_path / "study-1" / "series-1" / "image-1.dcm"
    assert saved.read_bytes() == b"mock-dicom-payload"


@pytest.mark.integration
def test_policy_evaluate_allows_after_grant(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("IMAGO_STORAGE_BACKEND", "memory")
    get_settings.cache_clear()
    get_ingestion_service.cache_clear()
    get_policy_engine.cache_clear()

    app = create_app()
    client = TestClient(app)

    grant_response = client.post(
        "/api/v1/policy/grants",
        headers=_auth_headers(principal_id="admin-1", role="admin"),
        json={
            "grant_id": "grant-1",
            "image_id": "img-1",
            "principal_id": "user-1",
            "action": "read",
            "idempotency_key": "grant-key-1",
        },
    )
    assert grant_response.status_code == 201
    assert grant_response.json()["grant_id"] == "grant-1"

    eval_response = client.post(
        "/api/v1/policy/evaluate",
        headers=_auth_headers(principal_id="user-1", role="radiologist"),
        json={
            "image_id": "img-1",
            "image_object_key": "study-1/series-1/image-1.dcm",
            "image_content_hash": "hash-1",
            "image_owner_organization_id": "org-1",
            "image_format_family": "dicom",
            "image_classification": "restricted_clinical",
            "action": "read",
        },
    )

    assert eval_response.status_code == 200
    data = eval_response.json()
    assert data["allowed"] is True
    assert data["reason"] == "allowed"


@pytest.mark.integration
def test_policy_evaluate_denies_without_grant(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("IMAGO_STORAGE_BACKEND", "memory")
    get_settings.cache_clear()
    get_ingestion_service.cache_clear()
    get_policy_engine.cache_clear()

    app = create_app()
    client = TestClient(app)

    eval_response = client.post(
        "/api/v1/policy/evaluate",
        headers=_auth_headers(principal_id="user-1", role="radiologist"),
        json={
            "image_id": "img-1",
            "image_object_key": "study-1/series-1/image-1.dcm",
            "image_content_hash": "hash-1",
            "image_owner_organization_id": "org-1",
            "image_format_family": "dicom",
            "image_classification": "restricted_clinical",
            "action": "read",
        },
    )

    assert eval_response.status_code == 403
    assert "access denied: no_active_grant" in eval_response.json()["detail"]


@pytest.mark.integration
def test_policy_endpoints_require_auth_headers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("IMAGO_STORAGE_BACKEND", "memory")
    get_settings.cache_clear()
    get_ingestion_service.cache_clear()
    get_policy_engine.cache_clear()

    app = create_app()
    client = TestClient(app)

    response = client.post(
        "/api/v1/policy/evaluate",
        json={
            "image_id": "img-1",
            "image_object_key": "study-1/series-1/image-1.dcm",
            "image_content_hash": "hash-1",
            "image_owner_organization_id": "org-1",
            "image_format_family": "dicom",
            "image_classification": "restricted_clinical",
            "action": "read",
        },
    )

    assert response.status_code == 401
    assert "missing required auth headers" in response.json()["detail"]


@pytest.mark.integration
def test_verify_endpoint_reports_hash_match_and_mismatch(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("IMAGO_STORAGE_BACKEND", "filesystem")
    monkeypatch.setenv("IMAGO_STORAGE_ROOT", str(tmp_path))
    get_settings.cache_clear()
    get_ingestion_service.cache_clear()
    get_policy_engine.cache_clear()

    app = create_app()
    client = TestClient(app)

    payload_bytes = b"dicom-payload-week4"
    payload = base64.b64encode(payload_bytes).decode("ascii")
    ingest_response = client.post(
        "/api/v1/images/ingest",
        json={
            "object_key": "study-2/series-2/image-2.dcm",
            "content_type": "application/dicom",
            "uploaded_by": "integration-user",
            "format_name": ".dcm",
            "payload_b64": payload,
        },
    )
    assert ingest_response.status_code == 201
    object_hash = ingest_response.json()["object_hash"]

    verify_ok = client.post(
        "/api/v1/images/verify",
        json={
            "object_key": "study-2/series-2/image-2.dcm",
            "expected_hash": object_hash,
        },
    )
    assert verify_ok.status_code == 200
    assert verify_ok.json()["verified"] is True
    assert verify_ok.json()["computed_hash"] == object_hash

    verify_bad = client.post(
        "/api/v1/images/verify",
        json={
            "object_key": "study-2/series-2/image-2.dcm",
            "expected_hash": "0" * 64,
        },
    )
    assert verify_bad.status_code == 200
    assert verify_bad.json()["verified"] is False


@pytest.mark.integration
def test_audit_policy_decisions_endpoint_returns_evaluation_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("IMAGO_STORAGE_BACKEND", "memory")
    get_settings.cache_clear()
    get_ingestion_service.cache_clear()
    get_policy_engine.cache_clear()

    app = create_app()
    client = TestClient(app)

    denied_eval = client.post(
        "/api/v1/policy/evaluate",
        headers=_auth_headers(principal_id="user-1", role="radiologist"),
        json={
            "image_id": "img-1",
            "image_object_key": "study-1/series-1/image-1.dcm",
            "image_content_hash": "hash-1",
            "image_owner_organization_id": "org-1",
            "image_format_family": "dicom",
            "image_classification": "restricted_clinical",
            "action": "read",
        },
    )
    assert denied_eval.status_code == 403

    grant_response = client.post(
        "/api/v1/policy/grants",
        headers=_auth_headers(principal_id="admin-1", role="admin"),
        json={
            "grant_id": "grant-audit-1",
            "image_id": "img-1",
            "principal_id": "user-1",
            "action": "read",
            "idempotency_key": "grant-audit-key-1",
        },
    )
    assert grant_response.status_code == 201

    allowed_eval = client.post(
        "/api/v1/policy/evaluate",
        headers=_auth_headers(principal_id="user-1", role="radiologist"),
        json={
            "image_id": "img-1",
            "image_object_key": "study-1/series-1/image-1.dcm",
            "image_content_hash": "hash-1",
            "image_owner_organization_id": "org-1",
            "image_format_family": "dicom",
            "image_classification": "restricted_clinical",
            "action": "read",
        },
    )
    assert allowed_eval.status_code == 200

    audit_response = client.get(
        "/api/v1/audit/policy-decisions",
        headers=_auth_headers(principal_id="aud-1", role="auditor"),
        params={"principal_id": "user-1", "image_id": "img-1", "limit": 10},
    )

    assert audit_response.status_code == 200
    body = audit_response.json()
    assert body["total"] >= 2
    outcomes = {item["outcome"] for item in body["items"]}
    assert "allow" in outcomes
    assert "deny" in outcomes


@pytest.mark.integration
def test_audit_policy_decisions_endpoint_requires_audit_role(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("IMAGO_STORAGE_BACKEND", "memory")
    get_settings.cache_clear()
    get_ingestion_service.cache_clear()
    get_policy_engine.cache_clear()

    app = create_app()
    client = TestClient(app)

    response = client.get(
        "/api/v1/audit/policy-decisions",
        headers=_auth_headers(principal_id="user-2", role="radiologist"),
    )

    assert response.status_code == 403
    assert "audit_read_requires_admin_or_auditor" in response.json()["detail"]
