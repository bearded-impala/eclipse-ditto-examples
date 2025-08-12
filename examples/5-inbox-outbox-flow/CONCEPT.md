# Understanding Inbox/Outbox in Eclipse Ditto: The Oscillation Problem

This document explains the **Inbox/Outbox design pattern** within the context of Eclipse Ditto, using an Actor Model perspective. It specifically highlights how the absence of a proper device acknowledgment can lead to an infinite loop of updates oscillating between "desired" and "actual" states.

## 1. Inbox and Outbox: The Design Pattern

The "Inbox" and "Outbox" are not explicit Ditto APIs but rather an **architectural pattern** achieved using Ditto's core capabilities (Things, Features, Messages, Connections) to ensure reliable, exactly-once message delivery in distributed systems.

**Why this pattern?**

Distributed systems face challenges like atomicity, idempotency, and handling offline components. The Inbox/Outbox pattern uses Ditto's persistent digital twin state as a reliable intermediary.

### 1.1. The Outbox Pattern (Commands from Ditto/Applications to Devices)

* **Concept:** An application or Ditto records the intention to send a message (a "command") as a "pending" or "desired" state within a digital twin's "outbox" (a specific feature/property).
* **Ditto Implementation:**
    * Application sets a `desired` state on a feature (e.g., `features/light/properties/status/desired = true`). This marks the "outbox."
    * Ditto's internal event bus detects this `desired` state change.
    * A configured **Ditto Connection** (e.g., MQTT, Hono) monitors these `desired` state changes and translates them into external commands sent to the physical device.
    * The crucial step: The physical device, upon executing the command, reports its actual `value` (actual state) back to the twin. This synchronizes `desired` and `value`, "clearing" the outbox.
* **Benefits:** Reliable delivery, atomicity, visibility of pending commands.

### 1.2. The Inbox Pattern (Telemetry/Events from Devices into Ditto/Applications)

* **Concept:** Incoming data from a device is initially placed into an "inbox" (a specific twin feature), which is then consumed by a separate process.
* **Ditto Implementation:**
    * A **Ditto Connection** receives telemetry from a device.
    * This connection (with payload mapping) updates the `value` of a feature (e.g., `features/temperature/properties/value`). This `value` effectively acts as the "inbox" for reported data.
    * Applications then monitor changes to this `value` (via WebSockets, SSE, Kafka events) to process incoming data.
* **Benefits:** Decoupling, buffering, auditing.

## 2. The Door Lock Scenario with Actor Model

Let's model a Smart Door Lock using an Actor Model:

* **Application Actor:** Initiates commands (e.g., Lock/Unlock).
* **Ditto Twin Actor:** The digital representation of the lock, managing `desired` and `value` states.
* **Ditto Connectivity Actor:** Bridges communication between the Twin Actor and the Physical Device Actor.
* **Physical Door Lock Device Actor:** The actual hardware, executes commands and reports its state.

### 2.1. The Desired Flow (No Infinite Loop)

Assumes lock is initially **UNLOCKED**.

1.  **App Actor sets `desired` state:** App `PUT`s `desired.status = "LOCKED"` on the Twin.
    * **Twin State:** `status: { "value": "UNLOCKED", "desired": "LOCKED" }` (Outbox: Pending)
2.  **Twin Actor emits internal event:** Signals `desired` change.
3.  **Connectivity Actor sends MQTT Command:** Translates event to MQTT `Lock Door` command to broker.
    * (Outbox: Externalized)
4.  **Device Actor receives & acts:** Receives command, physically locks door.
5.  **Device Actor reports `value`:** Publishes MQTT telemetry `status = "LOCKED"`.
    * (Inbox: Device sending data)
6.  **Connectivity Actor updates `value`:** Receives telemetry, `PUT`s `value.status = "LOCKED"` on Twin.
    * **Twin State:** `status: { "value": "LOCKED", "desired": "LOCKED" }` (Outbox: Cleared/Synchronized)
7.  **Twin Actor notifies App (Optional):** Sends event for synchronized state.

### 2.2. The Infinite Loop Scenario (Without a Real Device Reporting Back)

This happens if the **Physical Door Lock Device Actor is missing or fails to report its actual state (`value`) back to Ditto** after receiving a command.

**The Oscillating Flow:**

1.  **App to Ditto Twin:** Sets `desired.status = "LOCKED"`.
    * **Twin State:** `status: { "value": "UNLOCKED", "desired": "LOCKED" }` (Outbox: Pending)
2.  **Ditto Twin to Ditto Connectivity:** `desired` change event emitted.
3.  **Ditto Connectivity to MQTT Broker (External Command):** Sends "Lock Door" command.
4.  **Mosquitto Broker to ... Nowhere / Non-Reporting Device:** Command sent, but **no `value` update returns to Ditto.**
    * **CRITICAL:** Ditto Twin's `value` remains `UNLOCKED`.
5.  **Ditto Connectivity Actor (Problem!):** Since `desired ("LOCKED")` still doesn't match `value ("UNLOCKED")`, Ditto's internal logic (or an external reconciliation service monitoring this discrepancy) **might continuously interpret this as an unfulfilled command and re-send the "Lock Door" command.**