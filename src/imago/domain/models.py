from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from imago.storage.policy import DataClassification, FormatFamily


class PrincipalType(StrEnum):
    USER = "user"
    SERVICE = "service"


class AccessAction(StrEnum):
    READ = "read"
    VERIFY = "verify"
    ADMIN = "admin"


class AuditOutcome(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    ERROR = "error"


@dataclass(frozen=True)
class Organization:
    organization_id: str
    name: str


@dataclass(frozen=True)
class Principal:
    principal_id: str
    organization_id: str
    principal_type: PrincipalType
    role: str


@dataclass(frozen=True)
class ImageAsset:
    image_id: str
    object_key: str
    content_hash: str
    format_family: FormatFamily
    classification: DataClassification
    owner_organization_id: str


@dataclass(frozen=True)
class AccessGrant:
    grant_id: str
    image_id: str
    principal_id: str
    action: AccessAction
    granted_by: str
    granted_at: datetime
    expires_at: datetime | None = None
    revoked_at: datetime | None = None

    def is_active(self, at: datetime | None = None) -> bool:
        check_at = at or datetime.now(UTC)
        if self.revoked_at is not None and self.revoked_at <= check_at:
            return False
        if self.expires_at is not None and self.expires_at <= check_at:
            return False
        return True


@dataclass(frozen=True)
class AuditRecord:
    audit_id: str
    principal_id: str
    action: AccessAction
    resource_id: str
    outcome: AuditOutcome
    correlation_id: str
    occurred_at: datetime

    @classmethod
    def new(
        cls,
        audit_id: str,
        principal_id: str,
        action: AccessAction,
        resource_id: str,
        outcome: AuditOutcome,
        correlation_id: str,
    ) -> "AuditRecord":
        return cls(
            audit_id=audit_id,
            principal_id=principal_id,
            action=action,
            resource_id=resource_id,
            outcome=outcome,
            correlation_id=correlation_id,
            occurred_at=datetime.now(UTC),
        )
