import base64
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from imago.api.dependencies import get_ingestion_service
from imago.config.settings import get_settings
from imago.main import create_app


@pytest.mark.integration
def test_ingest_endpoint_returns_created_with_classification(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("IMAGO_STORAGE_BACKEND", "filesystem")
    monkeypatch.setenv("IMAGO_STORAGE_ROOT", str(tmp_path))
    get_settings.cache_clear()
    get_ingestion_service.cache_clear()

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
