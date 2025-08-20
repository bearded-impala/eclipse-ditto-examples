# Thing Search

This module provides simple utilities for creating things, running queries, and cleanup.

## Usage

1. **Start Ditto** (if not already running):
   ```bash
   uv run poe start-ditto
   ```

2. **Clean up existing things** (optional, to start fresh):
   ```bash
   uv run poe cleanup
   ```

3. **Create things** (automatically creates required policy):
   ```bash
   uv run poe create-things --count 20
   ```

4. **Run queries**:
   ```bash
   uv run poe test-queries
   ```

---

## Commands

### Create Things

Create things by randomizing values from a schema:

```bash
# Create 10 things using the default camera schema
uv run poe create-things --count 10

# Create 50 things using a custom schema
uv run poe create-things --count 50 --schema schema/my-schema.json
```

**Arguments:**
- `--count` (required): Number of things to create
- `--schema`: Path to schema file (default: `schema/camera.json`)
- `--ditto-url`: Ditto API URL (default: `http://localhost:8080/api/2`)
- `--auth-user`: Authentication username (default: `ditto`)
- `--auth-pass`: Authentication password (default: `ditto`)

### Test Queries

Execute RQL queries and see results:

```bash
# Run queries using the default camera queries
uv run poe test-queries

# Run queries from a custom file
uv run poe test-queries --queries queries/my-queries.json

# Use custom Ditto connection
uv run poe test-queries \
  --ditto-url http://my-ditto:8080/api/2 \
  --auth-user myuser \
  --auth-pass mypass
```

**Arguments:**
- `--queries`: Path to query file (default: `queries/camera.json`)
- `--ditto-url`: Ditto API URL (default: `http://localhost:8080/api/2`)
- `--auth-user`: Authentication username (default: `ditto`)
- `--auth-pass`: Authentication password (default: `ditto`)

### Cleanup

Remove all things from the system to start fresh:

```bash
uv run poe cleanup
```

---

## Schema Format

The schema should be a JSON file with a Ditto thing structure. Lists in the schema will be randomized by selecting random values.

Example schema structure:
```json
{
  "thingId": "org.eclipse.ditto:camera-a471",
  "policyId": "org.eclipse.ditto:read-write-policy",
  "attributes": {
    "type": "camera",
    "location": ["Kitchen", "Office", "Garage"],
    "manufacturer": ["Acme Corp", "HID"]
  },
  "features": {
    "video": {
      "properties": {
        "resolution": ["720p", "1080p", "4K"],
        "nightVision": [true, false]
      }
    }
  }
}
```

## Query Format

Queries should be in JSON format with an array of query objects:

```json
{
  "name": "Query Set Name",
  "description": "Description of the query set",
  "queries": [
    {
      "description": "Find cameras in Office",
      "rql": "eq(attributes/location,'Office')"
    },
    {
      "description": "Find cameras with night vision",
      "rql": "eq(features/video/properties/nightVision,true)"
    }
  ]
}
```
