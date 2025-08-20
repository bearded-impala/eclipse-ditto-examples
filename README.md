# Playground for Eclipse Ditto

This repository contains comprehensive examples and experiments with Eclipse Ditto, a digital twin framework for IoT devices.

## 🚀 Quick Start

### Prerequisites

- **Docker & Docker Compose** - For running Eclipse Ditto services
- **Python 3.9+** - For running examples
- **UV Package Manager** - Fast Python package manager

### Setup

1. **Install UV (if missing):**
   ```bash
   # macOS
   brew install uv

   # Windows
   powershell -ExecutionPolicy Bypass -c "irm https://astral.sh/uv/install.ps1 | iex"

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
