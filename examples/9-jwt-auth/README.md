# JWT Authentication (Example 9)

## Mock OAuth (quick start)

```bash
uv run poe start-ditto
uv run poe e9-mock
```

## AWS Cognito

1. Add to the **root** `.env`:

```env
DITTO_OAUTH_PROTOCOL=https
COGNITO_USER_POOL_ID=<User Pool ID — AWS Console → Cognito → User Pools>
COGNITO_REGION=us-east-1
COGNITO_USERNAME=<user — AWS Console → Cognito → User Pools → Users>
COGNITO_PASSWORD=<password for that user>
COGNITO_APP_CLIENT_ID=<App client ID — AWS Console → Cognito → App clients>
```

2. Run:

```bash
uv run poe start-ditto
uv run poe e9-cognito
```
