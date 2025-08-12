# Introduction

## Goal

Enrich a digital twin with external data (e.g., weather information based on location). This typically involves an external service fetching data and Ditto pushing it into the twin.

### Flow

1. Create a policy and thing with location attributes.
2. Simulate an external service (e.g., a simple curl call) that fetches weather data and then updates the digital twin's "weather" feature.
3. Retrieve the enriched twin state.

#### Create Policy

This policy requires basic authentication.
```bash
curl -X PUT -i -u ditto:ditto -H 'Content-Type: application/json' \
  http://localhost:8080/api/2/policies/org.eclipse.ditto:vehicle-001-policy \
  -d @policy.json
```

#### Create Things

Create a Thing description in eclipse-ditto for sensor and sensor 02.
```bash
curl -X PUT -i -u ditto:ditto -H 'Content-Type: application/json' \
  http://localhost:8080/api/2/things/org.eclipse.ditto:vehicle-001 \
  -d @thing.json
```

## Test Example

### Simulate External Service (Update with Weather Data):

Imagine an external microservice that, upon detecting a location change or on a schedule, calls a weather API (e.g., OpenWeatherMap) and then pushes that data to Ditto.

```bash
WEATHER_DATA='{
  "temperature": 18.2,
  "conditions": "Cloudy",
  "windSpeed": 15,
  "lastUpdated": "2025-07-22T09:15:00Z"
}'

curl -X PUT -i -u ditto:ditto -H 'Content-Type: application/json' \
  http://localhost:8080/api/2/things/org.eclipse.ditto:vehicle-001/features/weather/properties \
  -d "$WEATHER_DATA"
```

### Retrieve Digital Twin State:

```bash
curl -s -X GET -u ditto:ditto \
  http://localhost:8080/api/2/things/org.eclipse.ditto:vehicle-001 | jq .
```
You should now see a weather feature within the features section of the twin.
