# Playground for Eclipse Ditto

This repository contains comprehensive examples and experiments with Eclipse Ditto, a digital twin framework for IoT devices.

## 🚀 Quick Start

### Prerequisites

- **Docker & Docker Compose** - For running Eclipse Ditto services
- **Python 3.13+** - For running examples
- **UV Package Manager** - Fast Python package manager

### Setup

1. **Install UV (if missing):**
   ```bash
   brew install uv  # macOS
   # or visit https://docs.astral.sh/uv/getting-started/installation/
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```

3. **Start Eclipse Ditto:**
   ```bash
   uv run poe start-ditto
   ```

4. **Explore the examples:**

   Make sure to rename .env.example to .env at the root of the repository.


   ```bash
   uv run poe --help  # See all available commands
   ```

## 🎯 Available Examples

### Basic Examples
- **Example 1**: Device State Sync - Basic state management
- **Example 2**: Remote Device Control - Command and control patterns
- **Example 3**: Digital Twin Enhancement - External data integration
- **Example 4**: Outbox Pattern - Reliable command delivery

### Communication Examples
- **Example 5**: Inbox/Outbox Flow - Bidirectional communication
- **Example 6**: MQTT Connection - Basic MQTT integration

### Thing Search Examples
- **Example 7**: Fleet Management - Managing device fleets

## 🛠️ Running Examples

```bash
# Run individual examples
uv run poe e1    # Device State Sync
uv run poe e2    # Remote Device Control
uv run poe e3    # Digital Twin Enhancement
# ... etc
```

### Manual Execution

Either rely on the shell script or refer to the example specific README to understand detailed steps

```bash
# Navigate to example directory
cd examples/1-device-state-sync

# Run the example
./run_example.sh
```
