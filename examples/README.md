# Examples

Runnable examples showing how to integrate `python-env-secrets` into different
types of Python projects.

## Prerequisites

From the **repository root**, install the package in editable mode:

```bash
pip install -e ".[dotenv]"
```

The `[dotenv]` extra pulls in `python-dotenv`, which the dotenv integration
example relies on.

## Running

```bash
# Basic usage — init, set, get, list, clear
python examples/basic_usage.py

# FastAPI app with secrets-backed settings
pip install fastapi uvicorn
python examples/fastapi_app.py
# Then open http://localhost:8000/health

# python-dotenv integration — layered loading
python examples/dotenv_integration.py
```

Each example creates its own temporary project directory so it won't interfere
with your real files. Look at the console output to see what's happening at
each step.
