"""Tests for python-env-secrets."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from python_env_secrets import EnvSecretsManager


@pytest.fixture()
def project_dir(tmp_path: Path) -> Path:
    """Return a temporary directory to act as the project root."""
    return tmp_path / "project"


@pytest.fixture()
def secrets_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Override the secrets base directory so tests don't touch real user data."""
    base = tmp_path / "secrets_home"
    base.mkdir()
    monkeypatch.setattr(
        "python_env_secrets.manager._secrets_base_dir", lambda: base
    )
    return base


@pytest.fixture()
def manager(
    project_dir: Path, secrets_home: Path
) -> EnvSecretsManager:
    """Return a fully-initialised manager in an isolated environment."""
    project_dir.mkdir(parents=True, exist_ok=True)
    return EnvSecretsManager(project_dir=project_dir, auto_init=True)


# ------------------------------------------------------------------
# Initialisation
# ------------------------------------------------------------------


class TestInit:
    def test_creates_env_file_with_guid(self, manager: EnvSecretsManager) -> None:
        assert manager.env_file_path.exists()
        content = manager.env_file_path.read_text()
        assert "ENV_SECRETS_ID=" in content
        assert manager.env_secrets_id is not None

    def test_creates_secrets_file(self, manager: EnvSecretsManager) -> None:
        assert manager.secrets_path is not None
        assert manager.secrets_path.exists()

    def test_reuses_existing_guid(
        self, project_dir: Path, secrets_home: Path
    ) -> None:
        project_dir.mkdir(parents=True, exist_ok=True)
        m1 = EnvSecretsManager(project_dir=project_dir, auto_init=True)
        guid1 = m1.env_secrets_id

        m2 = EnvSecretsManager(project_dir=project_dir, auto_init=True)
        assert m2.env_secrets_id == guid1

    def test_preserves_existing_env_content(
        self, project_dir: Path, secrets_home: Path
    ) -> None:
        project_dir.mkdir(parents=True, exist_ok=True)
        env_file = project_dir / ".env"
        env_file.write_text("EXISTING_VAR=hello\n")

        EnvSecretsManager(project_dir=project_dir, auto_init=True)
        content = env_file.read_text()
        assert "EXISTING_VAR=hello" in content
        assert "ENV_SECRETS_ID=" in content


# ------------------------------------------------------------------
# CRUD
# ------------------------------------------------------------------


class TestSetGetDeleteClear:
    def test_set_and_get(self, manager: EnvSecretsManager) -> None:
        manager.set("DB_URL", "postgres://localhost/test")
        assert manager.get("DB_URL") == "postgres://localhost/test"

    def test_set_updates_environ(self, manager: EnvSecretsManager) -> None:
        manager.set("MY_KEY", "my_value")
        assert os.environ.get("MY_KEY") == "my_value"
        # cleanup
        os.environ.pop("MY_KEY", None)

    def test_get_nonexistent_returns_none(self, manager: EnvSecretsManager) -> None:
        assert manager.get("NO_SUCH_KEY") is None

    def test_delete_existing(self, manager: EnvSecretsManager) -> None:
        manager.set("TO_DELETE", "val")
        assert manager.delete("TO_DELETE") is True
        assert manager.get("TO_DELETE") is None

    def test_delete_nonexistent(self, manager: EnvSecretsManager) -> None:
        assert manager.delete("NOPE") is False

    def test_clear(self, manager: EnvSecretsManager) -> None:
        manager.set("A", "1")
        manager.set("B", "2")
        count = manager.clear()
        assert count == 2
        assert manager.list() == {}

    def test_list(self, manager: EnvSecretsManager) -> None:
        manager.set("X", "10")
        manager.set("Y", "20")
        result = manager.list()
        assert result == {"X": "10", "Y": "20"}


# ------------------------------------------------------------------
# Loading into os.environ
# ------------------------------------------------------------------


class TestLoad:
    def test_load_injects_env(self, manager: EnvSecretsManager) -> None:
        manager.set("LOAD_TEST", "loaded")
        # Remove from env to verify load re-injects
        os.environ.pop("LOAD_TEST", None)
        loaded = manager.load()
        assert "LOAD_TEST" in loaded
        assert os.environ.get("LOAD_TEST") == "loaded"
        os.environ.pop("LOAD_TEST", None)


# ------------------------------------------------------------------
# Edge cases
# ------------------------------------------------------------------


class TestEdgeCases:
    def test_value_with_spaces_is_quoted(self, manager: EnvSecretsManager) -> None:
        manager.set("SPACED", "hello world")
        assert manager.get("SPACED") == "hello world"

    def test_value_with_equals(self, manager: EnvSecretsManager) -> None:
        manager.set("CONN", "host=localhost;port=5432")
        assert manager.get("CONN") == "host=localhost;port=5432"

    def test_overwrite_existing_secret(self, manager: EnvSecretsManager) -> None:
        manager.set("KEY", "v1")
        manager.set("KEY", "v2")
        assert manager.get("KEY") == "v2"

    def test_info_returns_dict(self, manager: EnvSecretsManager) -> None:
        info = manager.info()
        assert "env_secrets_id" in info
        assert "secrets_count" in info
        assert info["secrets_file_exists"] is True


# ------------------------------------------------------------------
# Uninitialised guard
# ------------------------------------------------------------------


class TestUninitialised:
    def test_raises_when_not_initialised(
        self, project_dir: Path, secrets_home: Path
    ) -> None:
        project_dir.mkdir(parents=True, exist_ok=True)
        m = EnvSecretsManager(project_dir=project_dir, auto_init=False)
        with pytest.raises(RuntimeError, match="not initialised"):
            m.set("K", "V")
