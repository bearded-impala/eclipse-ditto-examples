# Direct Gateway Access (Example 10)

Most Ditto deployments sit behind an nginx reverse proxy that handles two jobs:
terminating HTTP Basic Auth and injecting a `x-ditto-pre-authenticated` header
before forwarding requests to the gateway. This example removes nginx entirely
and shows what happens at the gateway level directly.

## What this example demonstrates

**Two authentication methods against the same gateway, with no nginx:**

1. **Pre-authenticated header** — the client sends
   `x-ditto-pre-authenticated: nginx:ditto` straight to the gateway.
   This is exactly what nginx would inject after verifying a Basic Auth
   credential. With `ENABLE_PRE_AUTHENTICATION=true` set on the gateway, it
   trusts this header and maps it to the subject `nginx:ditto` in policy
   lookups.

2. **External JWT (Bearer token)** — the client fetches a signed token from
   the mock OAuth server (`oauth:9900/ditto`) and sends it as
   `Authorization: Bearer <token>`. The gateway validates the token against
   the issuer's JWKS endpoint and maps the `sub` claim to the subject
   `ditto:ditto`.

Both subjects are granted `READ/WRITE` on the same policy, so both methods
work against the same thing.

## Flow

1. Create a policy (`sensor-direct-policy`) with two subjects:
   `nginx:ditto` and `ditto:ditto`.
2. Create a thing (`sensor-direct-001`) using the pre-authenticated header.
3. Fetch a JWT from the mock OAuth server.
4. Read the same thing back using the JWT as a Bearer token.

## Run it

```bash
# 1. Start the minimal stack
uv run poe start-ditto-minimal

# 2. (in another terminal) Run the example
uv run poe e10

# 3. Tear down
uv run poe stop-ditto-minimal
```

The `e10` poe task sets these environment variables automatically:

| Variable           | Value                       | Purpose                                          |
| ------------------ | --------------------------- | ------------------------------------------------ |
| `AUTH_TYPE`        | `PRE_AUTH`                  | Send the `x-ditto-pre-authenticated` header      |
| `PRE_AUTH_SUBJECT` | `nginx:ditto`               | `<issuer>:<subject>` value placed in the header  |
| `JWT_ISSUER`       | `oauth:9900`                | Mock OAuth server (resolved inside docker network) |
| `JWT_SUBJECT`      | `ditto`                     | Subject used when requesting the JWT             |
| `DITTO_API_BASE`   | `http://gateway:8080/api/2` | Direct URL to the gateway — no nginx hop         |
