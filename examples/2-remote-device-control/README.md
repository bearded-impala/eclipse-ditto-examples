# Introduction

## Goal

Send a command to a digital twin to change a desired state (e.g., turn a light on), and then verify the desired state is updated. For a real device, this would also involve the device receiving and acting on the command.

### Flow

1. Create a policy and thing for a light bulb.
2. Define a connection to simulate the "device" receiving commands (though for curl testing, we'll directly set the desired state). In a real scenario, this would be an MQTT or AMQP connection with a mapping.
3. Send a command to update the "desired state" of the light bulb.
4. Retrieve the twin state to see the updated desired state.

#### Create Policy

This policy requires basic authentication.
```bash
curl -X PUT -i -u ditto:ditto -H 'Content-Type: application/json' \
  http://localhost:8080/api/2/policies/org.eclipse.ditto:light-001-policy \
  -d @policy.json
```

#### Create Things

Create a Thing description in eclipse-ditto for sensor and sensor 02.
```bash
curl -X PUT -i -u ditto:ditto -H 'Content-Type: application/json' \
  http://localhost:8080/api/2/things/org.eclipse.ditto:light-001 \
  -d @thing.json
```

## Test Example

### Update Desired State:

This sets the desired state of the onOff feature to true.

```bash
curl -X PUT -i -u ditto:ditto -H 'Content-Type: application/json' \
  http://localhost:8080/api/2/things/org.eclipse.ditto:light-001/features/onOff/properties/status/desired \
  -d 'true'
```

### Retrieve Digital Twin State:

```bash
curl -s -X GET -u ditto:ditto \
  http://localhost:8080/api/2/things/org.eclipse.ditto:light-001 | jq .
```
You should see status: { "desired": true, "value": false } (or just desired: true if no reported value is set yet). In a real implementation, the physical device would receive this desired state change and, after acting on it, would report its value as true back to Ditto.
