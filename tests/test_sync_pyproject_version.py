"""Tests for the pyproject-version-sync pre-commit hook."""

from collections.abc import Callable
from pathlib import Path

import pytest
from typer.testing import CliRunner

from pyproject_version_sync.sync_pyproject_version import (
    find_latest_tag,
    find_version_in_toml,
    sync_pyproject_version,
    write_new_version_to_toml,
)

# The version string appears in several places other than [tool.poetry].version, all of which must be left alone
PYPROJECT = """\
[tool.poetry]
name = "example"
description = "Successor to 0.1.0 of something else"
authors = [
    "A Person <a@example.com>",
]
version = "0.1.0"  # managed by pyproject-version-sync

[tool.poetry.dependencies]
foo = "0.1.0"

[tool.other]
version = "0.1.0"
"""
PYPROJECT_FIXED = PYPROJECT.replace('version = "0.1.0"  #', 'version = "0.2.0"  #')


@pytest.fixture
def toml_file(tmp_path: Path) -> Path:
    path = tmp_path / "pyproject.toml"
    path.write_text(PYPROJECT)
    return path


@pytest.mark.parametrize(
    ("tag", "expected"),
    [
        ("v1.2.3", "1.2.3"),
        ("1.2.3", "1.2.3"),
        ("v1.2.3-rc1", "1.2.3"),
        ("1.2.3.post1", "1.2.3"),
    ],
)
def test_find_latest_tag_extracts_version(tag_new_commit: Callable[[str], None], tag: str, expected: str) -> None:
    tag_new_commit(tag)
    assert find_latest_tag() == expected


def test_find_latest_tag_uses_most_recently_tagged_commit(tag_new_commit: Callable[[str], None]) -> None:
    for tag in ("v0.1.0", "v0.3.0", "v0.2.0"):
        tag_new_commit(tag)
    assert find_latest_tag() == "0.2.0"


def test_find_latest_tag_rejects_non_semver_tag(tag_new_commit: Callable[[str], None]) -> None:
    tag_new_commit("release-1")
    with pytest.raises(IndexError):
        find_latest_tag()


def test_find_version_in_toml(toml_file: Path) -> None:
    assert find_version_in_toml(toml_file) == "0.1.0"


def test_write_new_version_only_changes_tool_poetry_version(toml_file: Path) -> None:
    write_new_version_to_toml(toml_file, "0.1.0", "0.2.0")
    assert toml_file.read_text() == PYPROJECT_FIXED


@pytest.mark.parametrize(
    "version_line",
    [
        'version = "0.1.0"',
        "version = '0.1.0'",
        'version="0.1.0"',
    ],
)
def test_write_new_version_handles_formatting(tmp_path: Path, version_line: str) -> None:
    toml_file = tmp_path / "pyproject.toml"
    toml_file.write_text(f'[tool.poetry]  # comment\nname = "example"\n{version_line}\n')

    write_new_version_to_toml(toml_file, "0.1.0", "0.2.0")

    assert (
        toml_file.read_text()
        == f'[tool.poetry]  # comment\nname = "example"\n{version_line.replace("0.1.0", "0.2.0")}\n'
    )


def test_write_new_version_does_not_look_past_tool_poetry(tmp_path: Path) -> None:
    contents = '[tool.poetry]\nname = "example"\n\n[tool.other]\nversion = "0.1.0"\n'
    toml_file = tmp_path / "pyproject.toml"
    toml_file.write_text(contents)

    with pytest.raises(ValueError, match=r"Could not find version"):
        write_new_version_to_toml(toml_file, "0.1.0", "0.2.0")

    assert toml_file.read_text() == contents


def test_cli_passes_when_versions_match(tag_new_commit: Callable[[str], None], toml_file: Path) -> None:
    tag_new_commit("v0.1.0")

    result = CliRunner().invoke(sync_pyproject_version, [str(toml_file)])

    assert result.exit_code == 0
    assert toml_file.read_text() == PYPROJECT


def test_cli_fails_on_mismatch_without_fixing(tag_new_commit: Callable[[str], None], toml_file: Path) -> None:
    tag_new_commit("v0.2.0")

    result = CliRunner().invoke(sync_pyproject_version, [str(toml_file)])

    assert result.exit_code == 1
    assert "found tool.poetry.version = 0.1.0. Expected 0.2.0" in result.stderr
    assert toml_file.read_text() == PYPROJECT


def test_cli_fix_rewrites_version_and_still_fails(tag_new_commit: Callable[[str], None], toml_file: Path) -> None:
    tag_new_commit("v0.2.0")
    runner = CliRunner()

    result = runner.invoke(sync_pyproject_version, [str(toml_file), "--fix"])

    # Fails so pre-commit blocks the commit until the fixed file is staged
    assert result.exit_code == 1
    assert "Syncing version" in result.stderr
    assert toml_file.read_text() == PYPROJECT_FIXED
    assert runner.invoke(sync_pyproject_version, [str(toml_file)]).exit_code == 0


def test_cli_rejects_missing_file(git_repo: Path) -> None:
    result = CliRunner().invoke(sync_pyproject_version, [str(git_repo / "missing.toml")])
    assert result.exit_code == 2
