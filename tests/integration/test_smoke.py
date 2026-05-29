import base64

import pytest
from fastapi.testclient import TestClient

from imago.main import create_app


@pytest.mark.integration
def test_ingest_endpoint_returns_created_with_classification() -> None:
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
