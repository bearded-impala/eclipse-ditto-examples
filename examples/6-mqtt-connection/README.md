# Introduction

This example is for learning purposes purely to reproduce an issue in [mqtt-quick-introduction](https://github.com/eclipse-ditto/ditto-examples/blob/master/mqtt-quick-introduction/README.md) and understand the root cause.

Refer `docs/feedback-loop-RCA.md` for Root Cause Analysis.

The goal is to demonstrate connectivity between eclipse-ditto (backend) and a sensor (device).
- This sensor are MQTT capable device.
- It measures temperature and humidity and are installed at different locations.
- We will use eclipse-ditto's built-in MQTT's connectivity support to establish the connection.
- We will publish a message to a MQTT topic which will be consumed by Ditto to update the twin.

#### Create Policy

This policy requires basic authentication.
```bash
curl -X PUT 'http://localhost:8080/api/2/policies/my.test:policy' -u 'ditto:ditto' -H 'Content-Type: application/json' -d @policy.json
```

#### Create Things

Create a Thing description in eclipse-ditto for sensor and sensor 02.
```bash
curl -X PUT 'http://localhost:8080/api/2/things/my.sensors:sensor01' -u 'ditto:ditto' -H 'Content-Type: application/json' -d @sensor01.json

curl -X PUT 'http://localhost:8080/api/2/things/my.sensors:sensor02' -u 'ditto:ditto' -H 'Content-Type: application/json' -d @sensor02.json
```

#### Create an MQTT connection with JS mapping

The sensors spit out and process plain JSON. Therefore, we need a way to convert that JSON into ditto protocol and vice-versa.
Eclipse-ditto backend connectivity support provides a way to establish the above conversion using JS functions that are embedded in the connection descriptions. Refer the `connection_xx.json` files to see the JS functions that perform the conversion.
```bash
curl -s -X POST 'http://localhost:8080/devops/piggyback/connectivity?timeout=10' -u 'devops:foobar' -H 'Content-Type: application/json' -d @connection_source.json | jq .

curl -s -X POST 'http://localhost:8080/devops/piggyback/connectivity?timeout=10' -u 'devops:foobar' -H 'Content-Type: application/json' -d @connection_target.json | jq .
```

#### Setup an MQTT Broker

eclipse-mosquitto is an MQTT broker implementation.

#### Configure and run in a Docker container

- Pull Docker Image
```bash
uv run poe start-mqtt-broker
```

## Test the Example

### Publish to the topic

bash into the mosquitto container and publish an update to the topic:
```bash
docker exec -it mosquitto-broker /bin/sh

mosquitto_pub -h host.docker.internal -m '{"temperature": 56, "humidity": 86, "thingId": "my.sensors:sensor01"}' -t my.sensors/sensor01
```
You should be able to see the reflected changes now in the ditto explorer UI or using the below api call:
```bash
curl -s -X GET 'http://localhost:8080/api/2/things/my.sensors:sensor01' -u 'ditto:ditto' | jq .
```
