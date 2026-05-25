# Example 10 — Direct Gateway Access

Minimal stacks that talk to `ditto-gateway` **directly** (no nginx, no UI,
no swagger) and demonstrate which authentication methods are accepted on
which endpoints.

Two important nuances:

- For `/api/2` and `/ws`, pre-auth and JWT are **additive** — both providers can be active at once.
- For `/devops` and `/api/2/connections`, JWT and Basic Auth are **mutually exclusive**, picked by the single switch `DEVOPS_AUTHENTICATION_METHOD` (default `basic`). The pre-auth header is never honored.

The example has two variants. Each one is a single docker-compose file with
all values hardcoded:

- **Variant A** leaves `/devops` in its default `basic` mode → demonstrates the
  pre-auth header on `/api/2` and HTTP Basic Auth on `/devops`.
- **Variant B** flips `/devops` to `oauth2` mode → demonstrates JWT end-to-end
  on both `/api/2` and `/devops`, and proves Basic Auth on `/devops` is
  rejected once you switch to `oauth2`.

## Variant A: Pre-authenticated header

File: `docker/docker-compose-e10-preauth.yml`

Key config in the gateway service:

```yaml
ENABLE_PRE_AUTHENTICATION: "true"   # enables `x-ditto-pre-authenticated` on /api/2
DEVOPS_PASSWORD: foobar             # basic-auth password for /devops/*
```

```bash
# 1. Start the stack
uv run poe start-ditto-e10-preauth

# 2. Run the client (in another terminal)
uv run poe e10-preauth

# 3. Tear down
uv run poe stop-ditto-e10-preauth
```

## Variant B: External JWT (end-to-end on both `/api/2` and `/devops`)

File: `docker/docker-compose-e10-jwt.yml`

Key config in the gateway service:

```yaml
JAVA_TOOL_OPTIONS: >-
  # /api/2 + /ws issuer registration
  -Dditto.gateway.authentication.oauth.protocol=http
  -Dditto.gateway.authentication.oauth.openid-connect-issuers.ditto.issuer=oauth:9900/ditto
  -Dditto.gateway.authentication.oauth.openid-connect-issuers.ditto.auth-subjects.0="{{ jwt:sub }}"
  # /devops issuer registration (lives in a separate config block)
  -Dditto.gateway.authentication.devops.oauth.protocol=http
  -Dditto.gateway.authentication.devops.oauth.openid-connect-issuers.ditto.issuer=oauth:9900/ditto
  -Dditto.gateway.authentication.devops.oauth.openid-connect-issuers.ditto.auth-subjects.0="{{ jwt:sub }}"
  # allow-list of Ditto subjects permitted on /devops in oauth2 mode
  -Dditto.gateway.authentication.devops.devops-oauth2-subjects.0=ditto:ditto
DEVOPS_AUTHENTICATION_METHOD: oauth2     # flips /devops from basic to oauth2
DEVOPS_PASSWORD: foobar                  # kept on purpose to prove it's ignored in oauth2 mode
```

> Why `devops-oauth2-subjects.0=...` instead of the env-var `DEVOPS_OAUTH2_SUBJECTS`?
> The config field is a HOCON list; the env-var override expects a string and
> crashes the gateway with `has type STRING rather than LIST`. The `.0=` form
> sets index 0 of the list (same pattern as `auth-subjects.0` above). Add
> `.1=...` for a second subject.

```bash
# 1. Start the stack (includes the mock OAuth server)
uv run poe start-ditto-e10-jwt

# 2. Run the client
uv run poe e10-jwt

# 3. Tear down
uv run poe stop-ditto-e10-jwt
```
