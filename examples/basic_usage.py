"""
Basic usage — walks through the full user-secrets lifecycle.

Run:
    python examples/basic_usage.py
"""

import os
import tempfile
from pathlib import Path

from python_env_secrets import UserSecretsManager


def main() -> None:
    # Use a temp directory so the example is self-contained
    with tempfile.TemporaryDirectory() as tmp:
        project_dir = Path(tmp)
        print(f"Project directory: {project_dir}\n")

        # 1. Initialise ------------------------------------------------
        print("1) Initialise user secrets")
        manager = UserSecretsManager(project_dir=project_dir)
        print(f"   USER_SECRETS_ID : {manager.user_secrets_id}")
        print(f"   Secrets file    : {manager.secrets_path}")
        print(f"   .env content    : {manager.env_file_path.read_text().strip()}")

        # 2. Set secrets -----------------------------------------------
        print("\n2) Set some secrets")
        manager.set("DATABASE_URL", "postgresql://user:pass@localhost/mydb")
        manager.set("API_KEY", "sk-example-key-123")
        manager.set("DEBUG", "true")
        print(f"   Stored {len(manager.list())} secrets")

        # 3. Read them back --------------------------------------------
        print("\n3) Read secrets back")
        for key, value in manager.list().items():
            print(f"   {key} = {value}")

        # 4. Verify they're in os.environ ------------------------------
        print("\n4) Verify os.environ")
        print(f"   os.environ['DATABASE_URL'] = {os.environ.get('DATABASE_URL')}")
        print(f"   os.environ['API_KEY']      = {os.environ.get('API_KEY')}")

        # 5. Update a secret -------------------------------------------
        print("\n5) Update DEBUG to 'false'")
        manager.set("DEBUG", "false")
        print(f"   DEBUG = {manager.get('DEBUG')}")

        # 6. Delete a secret -------------------------------------------
        print("\n6) Delete API_KEY")
        manager.delete("API_KEY")
        print(f"   API_KEY in secrets: {'API_KEY' in manager.list()}")
        print(f"   API_KEY in environ: {'API_KEY' in os.environ}")

        # 7. Show info -------------------------------------------------
        print("\n7) Info")
        for k, v in manager.info().items():
            print(f"   {k}: {v}")

        # 8. Clear all -------------------------------------------------
        print("\n8) Clear all secrets")
        count = manager.clear()
        print(f"   Cleared {count} secret(s)")
        print(f"   Remaining: {manager.list()}")

        # 9. Re-init — GUID is reused ---------------------------------
        print("\n9) Re-initialise (same project dir)")
        manager2 = UserSecretsManager(project_dir=project_dir)
        print(f"   Same GUID? {manager2.user_secrets_id == manager.user_secrets_id}")

    print("\nDone. Temp directory cleaned up automatically.")


if __name__ == "__main__":
    main()
