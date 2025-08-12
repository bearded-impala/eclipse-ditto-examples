# Introduction

## Goal

Search for devices based on their attributes and reported states.

This example reuses sensor-001 and light-001 from previous scenarios.

### Flow

1. Create multiple "things" with different attributes and reported states (reusing previous things is fine).
2. Perform various search queries using Ditto's HTTP search API.

#### Create Policy

This policy requires basic authentication.
```bash
curl -X PUT -i -u ditto:ditto -H 'Content-Type: application/json' \
  http://localhost:8080/api/2/policies/org.eclipse.ditto:sensor-policy \
  -d @policy.json
```

#### Create Things

Create a Thing description in eclipse-ditto for sensor and sensor 02.
```bash
chmod +x bulk-create-things.sh

./bulk-create-things.sh
```

## Test Example

### Update sensor-002 reported state:

```bash
curl -X PUT -i -u ditto:ditto -H 'Content-Type: application/json' \
  http://localhost:8080/api/2/things/org.eclipse.ditto:sensor-002/features/humidity/properties/value \
  -d '70.1'
```

### Search Queries:

#### Find all things:

```bash
curl -s -X GET -u ditto:ditto \
  "http://localhost:8080/api/2/search/things" | jq .
```

#### Find all things with manufacturer: "ABC":

```bash
curl -s -X GET -u ditto:ditto \
  "http://localhost:8080/api/2/search/things?filter=eq(attributes/manufacturer,'ABC')" | jq .
```

#### Find all things where temperature is greater than 20 Celsius:

```bash
curl -s -X GET -u ditto:ditto \
  "http://localhost:8080/api/2/search/things?filter=gt(features/temperature/properties/value,20)" | jq .
```

#### Find all things in the "Living Room":

```bash
curl -s -X GET -u ditto:ditto \
  "http://localhost:8080/api/2/search/things?filter=eq(attributes/location,'Living%20Room')" | jq .
```

#### Combine queries (e.g., temperature > 20 AND location = 'Living Room'):

```bash
curl -s -X GET -u ditto:ditto \
  "http://localhost:8080/api/2/search/things?filter=and(gt(features/temperature/properties/value,20),eq(attributes/location,'Living%20Room'))" | jq .
```


---
