from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from imago.domain.models import AccessAction, AccessGrant, ImageAsset, Principal, PrincipalType
from imago.security.policy_engine import AuthorizationPolicyEngine
from imago.storage.policy import DataClassification, FormatFamily


def _principal(*, organization_id: str = "org-1", role: str = "radiologist") -> Principal:
    return Principal(
        principal_id="user-1",
        organization_id=organization_id,
        principal_type=PrincipalType.USER,
        role=role,
    )


def _asset(*, organization_id: str = "org-1") -> ImageAsset:
    return ImageAsset(
        image_id="img-1",
        object_key="study/series/img-1.dcm",
        content_hash="abc123",
        format_family=FormatFamily.DICOM,
        classification=DataClassification.RESTRICTED_CLINICAL,
        owner_organization_id=organization_id,
    )


def _grant(*, action: AccessAction = AccessAction.READ) -> AccessGrant:
    now = datetime.now(UTC)
    return AccessGrant(
        grant_id="grant-1",
        image_id="img-1",
        principal_id="user-1",
        action=action,
        granted_by="admin-1",
        granted_at=now,
        expires_at=now + timedelta(hours=1),
    )


@pytest.mark.unit
def test_policy_engine_allows_with_active_grant() -> None:
    engine = AuthorizationPolicyEngine()
    engine.record_grant(_grant())

    decision = engine.evaluate(
        principal=_principal(),
        asset=_asset(),
        action=AccessAction.READ,
    )

    assert decision.allowed is True
    assert decision.reason == "allowed"


@pytest.mark.unit
def test_policy_engine_denies_tenant_mismatch() -> None:
    engine = AuthorizationPolicyEngine()
    engine.record_grant(_grant())

    decision = engine.evaluate(
        principal=_principal(organization_id="org-2"),
        asset=_asset(organization_id="org-1"),
        action=AccessAction.READ,
    )

    assert decision.allowed is False
    assert decision.reason == "tenant_mismatch"


@pytest.mark.unit
def test_policy_engine_denies_without_grant() -> None:
    engine = AuthorizationPolicyEngine()

    decision = engine.evaluate(
        principal=_principal(),
        asset=_asset(),
        action=AccessAction.READ,
    )

    assert decision.allowed is False
    assert decision.reason == "no_active_grant"


@pytest.mark.unit
def test_policy_engine_revoke_grant_enforced() -> None:
    engine = AuthorizationPolicyEngine()
    grant = _grant()
    engine.record_grant(grant)
    engine.revoke_grant(grant.grant_id)

    decision = engine.evaluate(
        principal=_principal(),
        asset=_asset(),
        action=AccessAction.READ,
    )

    assert decision.allowed is False
    assert decision.reason == "no_active_grant"


@pytest.mark.unit
def test_policy_engine_grant_idempotency_key_reuses_existing_grant() -> None:
    engine = AuthorizationPolicyEngine()

    first = engine.record_grant(_grant(), idempotency_key="grant-key-1")
    second = engine.record_grant(_grant(), idempotency_key="grant-key-1")

    assert first == second
    assert len(engine.decisions) == 0