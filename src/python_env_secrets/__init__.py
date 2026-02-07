"""
python-env-secrets — keep sensitive configuration out of your project directory.

Quick start::

    from python_env_secrets import EnvSecretsManager

    secrets = EnvSecretsManager()      # auto-initialises
    secrets.set("API_KEY", "sk-...")
    print(secrets.get("API_KEY"))

Or use the convenience helpers::

    from python_env_secrets import init_env_secrets, load_env_secrets

    init_env_secrets()

    import os
    print(os.environ["API_KEY"])
"""

from __future__ import annotations

from pathlib import Path

from .manager import EnvSecretsManager

__all__ = [
    "EnvSecretsManager",
    "init_env_secrets",
    "load_env_secrets",
    "get_secret",
    "set_secret",
    "integrate_with_dotenv",
]

__version__ = "0.1.0"

# ---------------------------------------------------------------------------
# Module-level convenience functions
# ---------------------------------------------------------------------------

_default_manager: EnvSecretsManager | None = None


def _get_manager() -> EnvSecretsManager:
    global _default_manager
    if _default_manager is None:
        _default_manager = EnvSecretsManager(auto_init=True)
    return _default_manager


def init_env_secrets(project_dir: Path | None = None) -> EnvSecretsManager:
    """Initialise env secrets for the current project and return the manager."""
    global _default_manager
    _default_manager = EnvSecretsManager(project_dir, auto_init=True)
    return _default_manager


def load_env_secrets() -> dict[str, str]:
    """Load all env secrets into ``os.environ`` and return them."""
    return _get_manager().load()


def get_secret(key: str) -> str | None:
    """Get a single secret value."""
    return _get_manager().get(key)


def set_secret(key: str, value: str) -> None:
    """Set a single secret value."""
    _get_manager().set(key, value)


def integrate_with_dotenv() -> bool:
    """Load ``.env`` via *python-dotenv* first, then layer env secrets on top.

    Returns ``True`` if python-dotenv was available, ``False`` otherwise.
    """
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        load_env_secrets()
        return False

    load_env_secrets()
    return True
