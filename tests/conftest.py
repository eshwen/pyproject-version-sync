"""Shared fixtures for the tests."""

import itertools
import os
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest


@pytest.fixture
def git_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """
    Empty git repo in a temporary directory, which is also made the working directory.

    The user's global and system git config are ignored so things like commit signing can't interfere.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    for role in ("AUTHOR", "COMMITTER"):
        monkeypatch.setenv(f"GIT_{role}_NAME", "Test")
        monkeypatch.setenv(f"GIT_{role}_EMAIL", "test@example.com")

    subprocess.run(["git", "init", "-q"], check=True)
    return tmp_path


@pytest.fixture
def tag_new_commit(git_repo: Path) -> Callable[[str], None]:
    """
    Make a function that creates an empty commit and tags it.

    Each commit is dated a minute after the last, because `git rev-list --tags` orders by commit date and commits made
    in the same second would tie.
    """
    timestamps = itertools.count(start=1_700_000_000, step=60)

    def _tag_new_commit(tag: str) -> None:
        date = f"@{next(timestamps)} +0000"
        env = {**os.environ, "GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date}
        subprocess.run(["git", "commit", "-q", "--allow-empty", "-m", tag], check=True, env=env)
        subprocess.run(["git", "tag", tag], check=True)

    return _tag_new_commit
