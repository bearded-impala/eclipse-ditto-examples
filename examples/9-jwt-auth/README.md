# JWT Authentication (Example 9)

This example shows how Ditto's gateway validates an external JWT so a client can
authenticate using a Bearer token instead of HTTP Basic Auth. Two variants are
covered: a local mock OAuth server (zero external dependencies) and AWS Cognito
(a real production IdP).

## How it works

The standard Ditto stack has nginx in front of the gateway. For Basic Auth,
nginx verifies the password and injects `x-ditto-pre-authenticated: nginx:ditto`
into the forwarded request. For JWT, nginx passes the `Authorization: Bearer`
header through untouched and the gateway validates the token itself by:

1. Fetching the issuer's JWKS endpoint to verify the signature.
2. Extracting the `sub` claim and mapping it to a Ditto subject (e.g. `ditto:ditto`).
3. Checking that subject against the policy for the requested thing/policy.

The gateway must be configured with the issuer URL upfront (via `JAVA_TOOL_OPTIONS`).

## Variant A — Mock OAuth (quick start)

Uses `ghcr.io/navikt/mock-oauth2-server` which is already included in the main
`docker/docker-compose.yml` stack. The gateway is pre-configured to trust it as
issuer `oauth:9900/ditto`. The token's `sub` claim is `ditto`, so the matching
policy subject is `ditto:ditto`.

**Flow (`jwt_api_example.py`):**

1. `utils` fetches a JWT from `oauth:9900/ditto/token` using `client_credentials`.
2. Creates policy `sensor-policy-jwt` (subjects: `nginx:ditto` and `ditto:ditto`).
3. Creates thing `sensor-jwt-001` with the Bearer token.
4. Reads the thing back with the same token.

```bash
uv run poe start-ditto
uv run poe e9-mock
```

> `e9-mock` runs inside the docker network so `oauth:9900` resolves correctly
> and `AUTH_TYPE=BEARER` / `JWT_ISSUER=oauth:9900` are set automatically.

## Variant B — AWS Cognito

Uses a real Cognito User Pool. The gateway is configured with the Cognito issuer
URL (`cognito-idp.<region>.amazonaws.com/<pool-id>`). The Cognito ID token's
`sub` claim is a UUID; the script decodes it, builds the subject string
`cognito:<uuid>`, and injects it into the policy before creating anything.

**Flow (`jwt_cognito_example.py`):**

1. Calls `AWSCognitoIdentityProviderService.InitiateAuth` with username + password.
2. Decodes the `sub` claim from the returned ID token.
3. Creates policy `sensor-policy-cognito` with `cognito:<sub>` as the subject.
4. Creates thing `sensor-cognito-001` using the Cognito ID token as Bearer.
5. Reads the thing back with the same token.

Add the following to the root `.env` then run:

```env
DITTO_OAUTH_PROTOCOL=https
COGNITO_USER_POOL_ID=<User Pool ID — AWS Console → Cognito → User Pools>
COGNITO_REGION=us-east-1
COGNITO_USERNAME=<user — AWS Console → Cognito → User Pools → Users>
COGNITO_PASSWORD=<password for that user>
COGNITO_APP_CLIENT_ID=<App client ID — AWS Console → Cognito → App clients>
```

```bash
uv run poe start-ditto
uv run poe e9-cognito
```
