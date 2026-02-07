"""
Python Env Secrets Manager.

Stores a ENV_SECRETS_ID (GUID) in the project's local .env file and keeps
the actual secrets in a central, user-scoped directory:

    Linux / macOS : ~/.python/envsecrets/<guid>/.secrets
    Windows       : %APPDATA%/Python/EnvSecrets/<guid>/.secrets

Secrets are plain-text key=value pairs (same format as .env files) and are
automatically injected into ``os.environ`` on load.
"""

from __future__ import annotations

import logging
import os
import platform
import stat
import uuid
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

__all__ = ["EnvSecretsManager"]


class EnvSecretsManager:
    """Manage env secrets stored outside the project directory."""

    ENV_FILE_NAME = ".env"
    SECRETS_FILE_NAME = ".secrets"
    ENV_SECRETS_ID_KEY = "ENV_SECRETS_ID"

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(
        self,
        project_dir: Path | None = None,
        *,
        auto_init: bool = True,
    ) -> None:
        """
        Parameters
        ----------
        project_dir:
            Directory that contains (or will contain) the ``.env`` file.
            Defaults to the current working directory.
        auto_init:
            When *True* (the default), :meth:`init` is called automatically so
            secrets are available immediately after construction.
        """
        self.project_dir = Path(project_dir) if project_dir else Path.cwd()
        self.env_file_path = self.project_dir / self.ENV_FILE_NAME
        self.secrets_base_dir = _secrets_base_dir()
        self.env_secrets_id: str | None = None
        self.secrets_path: Path | None = None

        if auto_init:
            self.init()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def init(self) -> str:
        """Initialise (or reconnect to) env secrets for this project.

        * Reads ``ENV_SECRETS_ID`` from ``.env`` – or generates a new GUID.
        * Creates the secrets directory and file if they don't exist.
        * Loads secrets into ``os.environ``.

        Returns the env-secrets GUID.
        """
        env_vars = _read_dotenv(self.env_file_path)

        if self.ENV_SECRETS_ID_KEY in env_vars:
            self.env_secrets_id = env_vars[self.ENV_SECRETS_ID_KEY]
            logger.info("Found existing ENV_SECRETS_ID: %s", self.env_secrets_id)
        else:
            self.env_secrets_id = str(uuid.uuid4())
            logger.info("Generated new ENV_SECRETS_ID: %s", self.env_secrets_id)
            _upsert_env_key(
                self.env_file_path, self.ENV_SECRETS_ID_KEY, self.env_secrets_id
            )

        secrets_dir = self.secrets_base_dir / self.env_secrets_id
        secrets_dir.mkdir(parents=True, exist_ok=True)
        self.secrets_path = secrets_dir / self.SECRETS_FILE_NAME

        if not self.secrets_path.exists():
            _write_secrets(self.secrets_path, {}, self.project_dir, self.env_secrets_id)
            logger.info("Created secrets file: %s", self.secrets_path)
        else:
            logger.info("Using existing secrets file: %s", self.secrets_path)

        self.load()
        return self.env_secrets_id

    def load(self) -> dict[str, str]:
        """Load secrets from disk and inject them into ``os.environ``.

        Returns the loaded key/value pairs.
        """
        self._ensure_initialised()
        assert self.secrets_path is not None  # for type-checker
        secrets = _read_dotenv(self.secrets_path)
        for key, value in secrets.items():
            os.environ[key] = value
        if secrets:
            logger.info("Loaded %d secret(s) into environment", len(secrets))
        return secrets

    def set(self, key: str, value: str) -> None:
        """Create or update a secret and set it in ``os.environ``."""
        self._ensure_initialised()
        assert self.secrets_path is not None
        secrets = _read_dotenv(self.secrets_path)
        secrets[key] = value
        _write_secrets(self.secrets_path, secrets, self.project_dir, self.env_secrets_id)
        os.environ[key] = value
        logger.info("Set secret: %s", key)

    def get(self, key: str) -> str | None:
        """Return the value of *key*, or ``None`` if it doesn't exist."""
        self._ensure_initialised()
        assert self.secrets_path is not None
        return _read_dotenv(self.secrets_path).get(key)

    def delete(self, key: str) -> bool:
        """Remove *key* from the secrets file and ``os.environ``.

        Returns ``True`` if the key existed, ``False`` otherwise.
        """
        self._ensure_initialised()
        assert self.secrets_path is not None
        secrets = _read_dotenv(self.secrets_path)
        if key not in secrets:
            return False
        del secrets[key]
        _write_secrets(self.secrets_path, secrets, self.project_dir, self.env_secrets_id)
        os.environ.pop(key, None)
        logger.info("Deleted secret: %s", key)
        return True

    def clear(self) -> int:
        """Remove **all** secrets.  Returns the number of secrets cleared."""
        self._ensure_initialised()
        assert self.secrets_path is not None
        secrets = _read_dotenv(self.secrets_path)
        count = len(secrets)
        for key in secrets:
            os.environ.pop(key, None)
        _write_secrets(self.secrets_path, {}, self.project_dir, self.env_secrets_id)
        logger.info("Cleared %d secret(s)", count)
        return count

    def list(self) -> dict[str, str]:
        """Return all secrets as a dictionary (does **not** modify ``os.environ``)."""
        self._ensure_initialised()
        assert self.secrets_path is not None
        return _read_dotenv(self.secrets_path)

    def info(self) -> dict[str, Any]:
        """Return a summary of the current configuration."""
        secrets = self.list() if self.secrets_path else {}
        return {
            "project_dir": str(self.project_dir),
            "env_file": str(self.env_file_path),
            "env_file_exists": self.env_file_path.exists(),
            "env_secrets_id": self.env_secrets_id,
            "secrets_base_dir": str(self.secrets_base_dir),
            "secrets_file": str(self.secrets_path) if self.secrets_path else None,
            "secrets_file_exists": self.secrets_path.exists() if self.secrets_path else False,
            "secrets_count": len(secrets),
        }

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _ensure_initialised(self) -> None:
        if self.secrets_path is None or self.env_secrets_id is None:
            raise RuntimeError(
                "EnvSecretsManager is not initialised. "
                "Call init() or pass auto_init=True (the default)."
            )


# ======================================================================
# Module-private helpers
# ======================================================================


def _secrets_base_dir() -> Path:
    """Return the OS-appropriate base directory for env secrets."""
    system = platform.system()
    if system in ("Linux", "Darwin"):
        return Path.home() / ".python" / "envsecrets"
    if system == "Windows":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "Python" / "EnvSecrets"
        return Path.home() / "AppData" / "Roaming" / "Python" / "EnvSecrets"
    # Fallback
    return Path.home() / ".python" / "envsecrets"


def _read_dotenv(path: Path) -> dict[str, str]:
    """Parse a key=value file (supports comments, ``export`` prefix, quotes)."""
    result: dict[str, str] = {}
    if not path.exists():
        return result
    with open(path, encoding="utf-8") as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[7:]
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            # Strip matching quotes
            if len(value) >= 2 and value[0] in ('"', "'") and value[0] == value[-1]:
                value = value[1:-1]
            result[key] = value
    return result


def _upsert_env_key(env_path: Path, key: str, value: str) -> None:
    """Insert or update a single key in a .env file, preserving other content."""
    lines: list[str] = []
    replaced = False

    if env_path.exists():
        with open(env_path, encoding="utf-8") as fh:
            for raw_line in fh:
                stripped = raw_line.strip()
                if (
                    stripped
                    and not stripped.startswith("#")
                    and "=" in stripped
                    and stripped.split("=", 1)[0].strip() == key
                ):
                    lines.append(f"{key}={value}\n")
                    replaced = True
                else:
                    lines.append(raw_line)

    if not replaced:
        # Ensure we start on a new line
        if lines and not lines[-1].endswith("\n"):
            lines.append("\n")
        lines.append(f"{key}={value}\n")

    with open(env_path, "w", encoding="utf-8") as fh:
        fh.writelines(lines)


def _write_secrets(
    path: Path,
    secrets: dict[str, str],
    project_dir: Path | None = None,
    env_secrets_id: str | None = None,
) -> None:
    """Write a secrets dictionary to *path* in key=value format."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("# Python Env Secrets\n")
        fh.write("# Do not share or commit this file to source control.\n")
        if project_dir:
            fh.write(f"# Project: {project_dir}\n")
        if env_secrets_id:
            fh.write(f"# ID: {env_secrets_id}\n")
        fh.write("\n")
        for k, v in secrets.items():
            # Quote values that contain problematic characters
            if any(ch in v for ch in (" ", "=", "#", "'", '"')):
                v = f'"{v}"'
            fh.write(f"{k}={v}\n")

    # Restrictive permissions on Unix
    if platform.system() in ("Linux", "Darwin"):
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)  # 0o600
