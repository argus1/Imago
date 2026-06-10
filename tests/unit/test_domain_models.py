from datetime import UTC, datetime, timedelta

import pytest

from imago.domain.models import (
    AccessAction,
    AccessGrant,
    AuditOutcome,
    AuditRecord,
    ImageAsset,
    Organization,
    Principal,
    PrincipalType,
)
from imago.storage.policy import DataClassification, FormatFamily


@pytest.mark.unit
def test_domain_entities_can_be_constructed() -> None:
    org = Organization(organization_id="org-1", name="Imago Health")
    principal = Principal(
        principal_id="user-1",
        organization_id=org.organization_id,
        principal_type=PrincipalType.USER,
        role="radiologist",
    )
    asset = ImageAsset(
        image_id="img-1",
        object_key="images/series/img-1.dcm",
        content_hash="abc123",
        format_family=FormatFamily.DICOM,
        classification=DataClassification.RESTRICTED_CLINICAL,
        owner_organization_id=org.organization_id,
    )

    assert principal.organization_id == org.organization_id
    assert asset.owner_organization_id == org.organization_id


@pytest.mark.unit
def test_access_grant_active_state() -> None:
    now = datetime.now(UTC)
    grant = AccessGrant(
        grant_id="grant-1",
        image_id="img-1",
        principal_id="user-1",
        action=AccessAction.READ,
        granted_by="admin-1",
        granted_at=now,
        expires_at=now + timedelta(hours=1),
    )

    assert grant.is_active(now) is True
    assert grant.is_active(now + timedelta(hours=2)) is False


@pytest.mark.unit
def test_access_grant_revoked_is_inactive() -> None:
    now = datetime.now(UTC)
    grant = AccessGrant(
        grant_id="grant-1",
        image_id="img-1",
        principal_id="user-1",
        action=AccessAction.VERIFY,
        granted_by="admin-1",
        granted_at=now,
        revoked_at=now,
    )

    assert grant.is_active(now) is False


@pytest.mark.unit
def test_audit_record_factory_sets_timestamp() -> None:
    record = AuditRecord.new(
        audit_id="aud-1",
        principal_id="user-1",
        action=AccessAction.ADMIN,
        resource_id="policy-1",
        outcome=AuditOutcome.ALLOW,
        correlation_id="corr-1",
    )

    assert record.occurred_at.tzinfo is not None
    assert record.audit_id == "aud-1"
