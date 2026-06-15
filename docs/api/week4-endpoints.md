# Week 4 API Endpoints Usage Guide

This guide documents the two Week 4 policy grant-management endpoints:

- `POST /api/v1/policy/grants`
- `POST /api/v1/policy/grants/{grant_id}/revoke`

Both endpoints are visible in Swagger/OpenAPI and now include concrete request/response examples.

## Base URL

- Local default: `http://localhost:8000`

## Required auth headers

These endpoints require the lightweight auth context headers:

- `X-Imago-Principal-Id`
- `X-Imago-Org-Id`
- `X-Imago-Role` (`admin` or `super_admin` required)

Optional:

- `X-Imago-Principal-Type` (`user` by default)

If required headers are missing, the API returns `401 Unauthorized`.

## 1) Create access grant

`POST /api/v1/policy/grants`

Creates a policy grant that allows a principal to perform an action (for example `read`) on an image.

### Example request body

```json
{
  "grant_id": "grant-ct-001",
  "image_id": "img-ct-20260614-0001",
  "principal_id": "clinician-42",
  "action": "read",
  "expires_at": "2026-07-15T00:00:00Z",
  "idempotency_key": "idem-grant-ct-001"
}
```

### Example success response (`201 Created`)

```json
{
  "grant_id": "grant-ct-001"
}
```

### Common error (`403 Forbidden`)

```json
{
  "detail": "access denied: grant_management_requires_admin"
}
```

## 2) Revoke access grant

`POST /api/v1/policy/grants/{grant_id}/revoke`

Revokes an existing policy grant.

### Path parameter

- `grant_id` (string): identifier of the grant to revoke.

### Example request body

```json
{
  "idempotency_key": "idem-revoke-grant-ct-001"
}
```

### Example success response (`204 No Content`)

No response body.

### Common errors

`403 Forbidden`

```json
{
  "detail": "access denied: grant_management_requires_admin"
}
```

`404 Not Found`

```json
{
  "detail": "grant not found"
}
```

## Quick verification in Swagger

1. Start the service.
2. Open `/docs`.
3. Expand each Week 4 endpoint.
4. Confirm request/response examples appear under each operation.
