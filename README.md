# Imago
Tamper-proof storage of Medical Images enabled with Blockchain

![MRI Image](/MRI.webp)

## API auth headers (lightweight baseline)

Policy endpoints currently use a lightweight header-based identity context.

Required headers:

- `X-Imago-Principal-Id`
- `X-Imago-Org-Id`
- `X-Imago-Role`

Optional header:

- `X-Imago-Principal-Type` (`user` by default, `service` supported)

Behavior notes:

- Missing required auth headers return `401 Unauthorized`.
- `POST /api/v1/policy/grants` and `POST /api/v1/policy/grants/{grant_id}/revoke`
	require `admin` or `super_admin` role.
- `POST /api/v1/policy/evaluate` derives principal identity from headers (not from body fields).
