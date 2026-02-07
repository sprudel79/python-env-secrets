"""
python-dotenv integration — layered configuration loading.

Run:
    pip install python-dotenv        # or: pip install python-env-secrets[dotenv]
    python examples/dotenv_integration.py

Demonstrates the loading order:
    1. .env file is loaded first  (non-sensitive defaults)
    2. User secrets are layered on top  (sensitive overrides)

This mirrors a common pattern: a committable config file holds defaults while
secrets override with sensitive values during development.
"""

import os
import tempfile
from pathlib import Path

from python_env_secrets import UserSecretsManager


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        project_dir = Path(tmp)

        # ----- Step 1: Create a .env with non-sensitive defaults ------
        env_file = project_dir / ".env"
        env_file.write_text(
            "# Non-sensitive defaults (safe to commit)\n"
            "APP_NAME=MyApp\n"
            "LOG_LEVEL=info\n"
            "DATABASE_URL=sqlite:///./dev.db\n"
            "API_KEY=placeholder\n"
        )
        print("1) Created .env with defaults:")
        print(f"   {env_file.read_text()}")

        # ----- Step 2: Load .env with python-dotenv -------------------
        try:
            from dotenv import load_dotenv

            load_dotenv(env_file)
            print("2) Loaded .env via python-dotenv")
        except ImportError:
            print("2) python-dotenv not installed — skipping .env load")
            print("   Install it with: pip install python-dotenv")
            # Manually load for the demo to continue
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip()

        print(f"   DATABASE_URL = {os.environ.get('DATABASE_URL')}")
        print(f"   API_KEY      = {os.environ.get('API_KEY')}")

        # ----- Step 3: Init user secrets (adds GUID to .env) ----------
        print("\n3) Initialise user secrets")
        manager = UserSecretsManager(project_dir=project_dir)
        print(f"   USER_SECRETS_ID: {manager.user_secrets_id}")

        # ----- Step 4: Store real secrets -----------------------------
        print("\n4) Set sensitive overrides in user secrets")
        manager.set("DATABASE_URL", "postgresql://prod-user:s3cret@db.example.com/app")
        manager.set("API_KEY", "sk-live-abc123xyz")

        # ----- Step 5: Show the result --------------------------------
        print("\n5) Final environment (secrets override .env defaults):")
        print(f"   APP_NAME     = {os.environ.get('APP_NAME')}")
        print(f"   LOG_LEVEL    = {os.environ.get('LOG_LEVEL')}")
        print(f"   DATABASE_URL = {os.environ.get('DATABASE_URL')}")
        print(f"   API_KEY      = {os.environ.get('API_KEY')}")

        # ----- Step 6: Show what's where ------------------------------
        print("\n6) What lives where:")
        print("   .env file (committable):")
        for line in env_file.read_text().splitlines():
            print(f"      {line}")

        print(f"\n   .secrets file (private, at {manager.secrets_path}):")
        if manager.secrets_path:
            for line in manager.secrets_path.read_text().splitlines():
                print(f"      {line}")

        # ----- Step 7: The integrate_with_dotenv() shortcut -----------
        print("\n7) Shortcut: integrate_with_dotenv()")
        print("   In a real project, replace steps 2-3 with a single call:")
        print()
        print("       from python_env_secrets import integrate_with_dotenv")
        print("       integrate_with_dotenv()")
        print()
        print("   This loads .env first, then layers user secrets on top.")

    print("\nDone.")


if __name__ == "__main__":
    main()
