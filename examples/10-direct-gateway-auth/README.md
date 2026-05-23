# Direct Gateway Access (Example 10)

A minimal Ditto deployment that drops the reverse proxy, the UI, and the
swagger console, so a client can hit `ditto-gateway` **directly** and
authenticate two ways on the same policy:

## Run it

```bash
# 1. Start the minimal stack
uv run poe start-ditto-minimal

# 2. (in another terminal) Run the example
uv run poe e10

# 3. Tear down
uv run poe stop-ditto-minimal
```
