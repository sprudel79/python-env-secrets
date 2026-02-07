"""
FastAPI integration — secrets-backed application settings.

Run:
    pip install fastapi uvicorn
    python examples/fastapi_app.py

Then visit:
    http://localhost:8000/health
    http://localhost:8000/settings

This example shows the recommended pattern: initialise user secrets once at
module level, then read values from os.environ (or via pydantic-settings)
throughout your application.
"""

import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from python_env_secrets import UserSecretsManager

# ------------------------------------------------------------------
# 1. Bootstrap secrets before the app starts
#
#    In a real project you'd just call:
#        from python_env_secrets import init_user_secrets
#        init_user_secrets()
#
#    Here we use a temp dir so the example is self-contained.
# ------------------------------------------------------------------

_tmp = tempfile.mkdtemp(prefix="fastapi_secrets_")
_manager = UserSecretsManager(project_dir=Path(_tmp))

# Seed some secrets if this is the first run
if _manager.info()["secrets_count"] == 0:
    _manager.set("APP_NAME", "MyFastAPIApp")
    _manager.set("SECRET_KEY", "change-me-in-production")
    _manager.set("DATABASE_URL", "sqlite:///./dev.db")
    _manager.set("DEBUG", "true")
    _manager.set("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173")


# ------------------------------------------------------------------
# 2. Define typed settings that pull from os.environ
# ------------------------------------------------------------------

@dataclass
class Settings:
    """Application settings — all values come from user secrets / env vars."""

    app_name: str = field(default_factory=lambda: os.environ.get("APP_NAME", "App"))
    secret_key: str = field(default_factory=lambda: os.environ.get("SECRET_KEY", ""))
    database_url: str = field(default_factory=lambda: os.environ.get("DATABASE_URL", ""))
    debug: bool = field(
        default_factory=lambda: os.environ.get("DEBUG", "false").lower() == "true"
    )
    allowed_origins: list[str] = field(
        default_factory=lambda: os.environ.get("ALLOWED_ORIGINS", "").split(",")
    )


settings = Settings()


# ------------------------------------------------------------------
# 3. Build the FastAPI app
# ------------------------------------------------------------------

def create_app():  # noqa: ANN201
    try:
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse
    except ImportError:
        print("FastAPI is not installed. Run: pip install fastapi uvicorn")
        print("\nShowing settings that would be loaded:\n")
        print(f"  APP_NAME        : {settings.app_name}")
        print(f"  SECRET_KEY      : {settings.secret_key[:6]}***")
        print(f"  DATABASE_URL    : {settings.database_url}")
        print(f"  DEBUG           : {settings.debug}")
        print(f"  ALLOWED_ORIGINS : {settings.allowed_origins}")
        print(f"\n  Secrets file    : {_manager.secrets_path}")
        return None

    app = FastAPI(title=settings.app_name, debug=settings.debug)

    @app.get("/health")
    async def health() -> JSONResponse:
        return JSONResponse(
            {
                "status": "ok",
                "app": settings.app_name,
                "debug": settings.debug,
            }
        )

    @app.get("/settings")
    async def show_settings() -> JSONResponse:
        """Expose non-sensitive settings (for demo purposes only)."""
        return JSONResponse(
            {
                "app_name": settings.app_name,
                "database_url": settings.database_url,
                "debug": settings.debug,
                "allowed_origins": settings.allowed_origins,
                "secrets_file": str(_manager.secrets_path),
                "user_secrets_id": _manager.user_secrets_id,
            }
        )

    return app


app = create_app()


# ------------------------------------------------------------------
# 4. Run with uvicorn when executed directly
# ------------------------------------------------------------------

if __name__ == "__main__":
    if app is None:
        raise SystemExit(1)

    import uvicorn

    print(f"\nSecrets loaded from: {_manager.secrets_path}")
    print(f"USER_SECRETS_ID:     {_manager.user_secrets_id}\n")
    uvicorn.run(app, host="127.0.0.1", port=8000)
