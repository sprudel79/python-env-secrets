"""Tests for the CLI entry point."""

from __future__ import annotations

from pathlib import Path

import pytest

from python_env_secrets.cli import main


@pytest.fixture()
def cli_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Set up an isolated environment for CLI tests."""
    project = tmp_path / "cli_project"
    project.mkdir()
    secrets_base = tmp_path / "cli_secrets"
    secrets_base.mkdir()
    monkeypatch.setattr(
        "python_env_secrets.manager._secrets_base_dir", lambda: secrets_base
    )
    return project


class TestCli:
    def test_init(self, cli_env: Path, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main(["--project", str(cli_env), "init"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "ENV_SECRETS_ID" in out

    def test_set_and_get(self, cli_env: Path, capsys: pytest.CaptureFixture[str]) -> None:
        main(["--project", str(cli_env), "set", "MYKEY", "myval"])
        rc = main(["--project", str(cli_env), "get", "MYKEY"])
        assert rc == 0
        assert "myval" in capsys.readouterr().out

    def test_get_missing(self, cli_env: Path) -> None:
        main(["--project", str(cli_env), "init"])
        rc = main(["--project", str(cli_env), "get", "NOPE"])
        assert rc == 1

    def test_list(self, cli_env: Path, capsys: pytest.CaptureFixture[str]) -> None:
        main(["--project", str(cli_env), "set", "A", "1111"])
        rc = main(["--project", str(cli_env), "list"])
        assert rc == 0
        assert "A" in capsys.readouterr().out

    def test_delete(self, cli_env: Path, capsys: pytest.CaptureFixture[str]) -> None:
        main(["--project", str(cli_env), "set", "DEL", "bye"])
        rc = main(["--project", str(cli_env), "delete", "DEL"])
        assert rc == 0
        assert "Deleted" in capsys.readouterr().out

    def test_clear(self, cli_env: Path, capsys: pytest.CaptureFixture[str]) -> None:
        main(["--project", str(cli_env), "set", "X", "1"])
        main(["--project", str(cli_env), "set", "Y", "2"])
        capsys.readouterr()  # drain
        rc = main(["--project", str(cli_env), "clear"])
        assert rc == 0
        assert "2" in capsys.readouterr().out

    def test_info(self, cli_env: Path, capsys: pytest.CaptureFixture[str]) -> None:
        main(["--project", str(cli_env), "init"])
        capsys.readouterr()
        rc = main(["--project", str(cli_env), "info"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "ENV_SECRETS_ID" in out

    def test_no_command_prints_help(self, capsys: pytest.CaptureFixture[str]) -> None:
        rc = main([])
        assert rc == 0
        assert "env-secrets" in capsys.readouterr().out
