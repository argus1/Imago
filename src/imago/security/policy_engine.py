from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime

from imago.domain.models import (
    AccessAction,
    AccessGrant,
    ImageAsset,
    Principal,
    PrincipalType,
)
from imago.storage.policy import DataClassification


@dataclass(frozen=True)
class PolicyDecision:
    principal_id: str
    image_id: str
    action: AccessAction
    classification: DataClassification
    allowed: bool
    reason: str
    occurred_at: datetime


class AuthorizationPolicyEngine:
    """Deny-by-default authorization with role, tenant, and classification checks."""

    _ROLE_ACTIONS: dict[str, set[AccessAction]] = {
        "technician": {AccessAction.READ},
        "radiologist": {AccessAction.READ, AccessAction.VERIFY},
        "researcher": {AccessAction.READ, AccessAction.VERIFY},
        "auditor": {AccessAction.READ, AccessAction.VERIFY},
        "service": {AccessAction.VERIFY},
        "admin": {AccessAction.READ, AccessAction.VERIFY, AccessAction.ADMIN},
        "super_admin": {AccessAction.READ, AccessAction.VERIFY, AccessAction.ADMIN},
    }

    _CLASSIFICATION_ROLE_ALLOWLIST: dict[DataClassification, set[str]] = {
        DataClassification.RESTRICTED_CLINICAL: {"radiologist", "admin", "super_admin"},
        DataClassification.CONFIDENTIAL_RESEARCH: {
            "researcher",
            "radiologist",
            "admin",
            "super_admin",
            "service",
        },
        DataClassification.INTERNAL_DERIVED: {
            "technician",
            "researcher",
            "radiologist",
            "auditor",
            "service",
            "admin",
            "super_admin",
        },
        DataClassification.UNCLASSIFIED: {
            "technician",
            "researcher",
            "radiologist",
            "auditor",
            "service",
            "admin",
            "super_admin",
        },
    }

    def __init__(self) -> None:
        self._grants_by_id: dict[str, AccessGrant] = {}
        self._idempotency_index: dict[str, str] = {}
        self._decisions: list[PolicyDecision] = []

    @property
    def decisions(self) -> list[PolicyDecision]:
        return self._decisions

    def record_grant(self, grant: AccessGrant, *, idempotency_key: str | None = None) -> str:
        if idempotency_key is not None:
            existing_grant_id = self._idempotency_index.get(idempotency_key)
            if existing_grant_id is not None:
                return existing_grant_id

        self._grants_by_id[grant.grant_id] = grant
        if idempotency_key is not None:
            self._idempotency_index[idempotency_key] = grant.grant_id
        return grant.grant_id

    def revoke_grant(
        self,
        grant_id: str,
        *,
        revoked_at: datetime | None = None,
        idempotency_key: str | None = None,
    ) -> None:
        if idempotency_key is not None and idempotency_key in self._idempotency_index:
            return

        if grant_id not in self._grants_by_id:
            raise KeyError(f"unknown grant_id: {grant_id}")

        mark = revoked_at or datetime.now(UTC)
        self._grants_by_id[grant_id] = replace(self._grants_by_id[grant_id], revoked_at=mark)

        if idempotency_key is not None:
            self._idempotency_index[idempotency_key] = grant_id

    def evaluate(
        self,
        *,
        principal: Principal,
        asset: ImageAsset,
        action: AccessAction,
        at: datetime | None = None,
    ) -> PolicyDecision:
        now = at or datetime.now(UTC)
        role = principal.role.lower()

        if role != "super_admin" and principal.organization_id != asset.owner_organization_id:
            return self._record_decision(
                principal=principal,
                asset=asset,
                action=action,
                allowed=False,
                reason="tenant_mismatch",
                occurred_at=now,
            )

        if action not in self._ROLE_ACTIONS.get(role, set()):
            return self._record_decision(
                principal=principal,
                asset=asset,
                action=action,
                allowed=False,
                reason="role_not_permitted",
                occurred_at=now,
            )

        if role not in self._CLASSIFICATION_ROLE_ALLOWLIST.get(asset.classification, set()):
            return self._record_decision(
                principal=principal,
                asset=asset,
                action=action,
                allowed=False,
                reason="classification_not_permitted",
                occurred_at=now,
            )

        if (
            asset.classification is DataClassification.RESTRICTED_CLINICAL
            and principal.principal_type is not PrincipalType.USER
            and role != "super_admin"
        ):
            return self._record_decision(
                principal=principal,
                asset=asset,
                action=action,
                allowed=False,
                reason="clinical_requires_human_principal",
                occurred_at=now,
            )

        if not self._has_active_grant(
            principal_id=principal.principal_id,
            image_id=asset.image_id,
            action=action,
            at=now,
        ):
            return self._record_decision(
                principal=principal,
                asset=asset,
                action=action,
                allowed=False,
                reason="no_active_grant",
                occurred_at=now,
            )

        return self._record_decision(
            principal=principal,
            asset=asset,
            action=action,
            allowed=True,
            reason="allowed",
            occurred_at=now,
        )

    def _has_active_grant(
        self,
        *,
        principal_id: str,
        image_id: str,
        action: AccessAction,
        at: datetime,
    ) -> bool:
        for grant in self._grants_by_id.values():
            if grant.principal_id != principal_id or grant.image_id != image_id:
                continue
            if grant.action not in {action, AccessAction.ADMIN}:
                continue
            if grant.is_active(at):
                return True
        return False

    def _record_decision(
        self,
        *,
        principal: Principal,
        asset: ImageAsset,
        action: AccessAction,
        allowed: bool,
        reason: str,
        occurred_at: datetime,
    ) -> PolicyDecision:
        decision = PolicyDecision(
            principal_id=principal.principal_id,
            image_id=asset.image_id,
            action=action,
            classification=asset.classification,
            allowed=allowed,
            reason=reason,
            occurred_at=occurred_at,
        )
        self._decisions.append(decision)
        return decision