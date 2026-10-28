"""This pre-commit hook ensures that the version in pyproject.toml matches the latest git tag."""

import re
import subprocess
from pathlib import Path
from typing import Annotated

import tomli
import typer


def _execute_in_shell(cmd: str) -> subprocess.CompletedProcess:
    return subprocess.run(cmd.split(), check=True, capture_output=True)  # noqa: S603


def execute_and_clean(cmd: str) -> str:
    """
    Execute a command in the shell and return the output, stripped of whitespace.

    Args:
        cmd: Command to execute.

    Returns:
        Output of command, stripped of whitespace.
    """
    return _execute_in_shell(cmd).stdout.decode().strip()


def _find_latest_revision() -> str:
    cmd = "git rev-list --tags --max-count=1"
    return execute_and_clean(cmd)


def find_latest_tag() -> str:
    """
    Find the latest tag in the git repo.

    Returns:
        Latest tag.
    """
    latest_rev = _find_latest_revision()

    cmd = f"git describe --tags {latest_rev}"
    latest_tag = execute_and_clean(cmd)
    return re.findall(r"^v?(\d+\.\d+\.\d+).*", latest_tag)[0]


def find_version_in_toml(toml_file: Path) -> str:
    """
    Find the project version in pyproject.toml.

    Args:
        toml_file: Path to pyproject.toml.

    Returns:
        Project version.
    """
    with Path.open(toml_file, "rb") as f:
        pyproject = tomli.load(f)

    return pyproject["tool"]["poetry"]["version"]


def write_new_version_to_toml(toml_file: Path, version_pyproject: str, version_git: str) -> None:
    """
    Write the new version to pyproject.toml.

    Args:
        toml_file: Path to pyproject.toml.
        version_pyproject: Version in pyproject.toml.
        version_git: Latest git tag.

    Raises:
        ValueError: If no `version` key is found in the `[tool.poetry]` table.
    """
    pyproject_raw = Path.open(toml_file).read()

    # Only skip lines that don't start a new table, so the match can't run past the end of [tool.poetry]
    # and overwrite the version of something else in the file by mistake
    pyproject_new, n_subs = re.subn(
        rf"(\[tool\.poetry\][^\n]*\n(?:(?!\[)[^\n]*\n)*?version\s?=\s?[\"']){re.escape(version_pyproject)}([\"'])",
        rf"\g<1>{version_git}\g<2>",
        pyproject_raw,
        count=1,
    )
    if not n_subs:
        raise ValueError(f"Could not find version = {version_pyproject!r} in the [tool.poetry] table of {toml_file}.")

    with Path.open(toml_file, "w") as f_out:
        f_out.write(pyproject_new)


sync_pyproject_version = typer.Typer(add_completion=False)


@sync_pyproject_version.command(context_settings={"help_option_names": ["-h", "--help"]})
def cli(
    toml_file: Annotated[Path, typer.Argument(exists=True, dir_okay=False, help="Path to pyproject.toml.")],
    fix: Annotated[
        bool,
        typer.Option(
            "--fix",
            help="If set, automatically update the version in pyproject.toml to match the latest git tag.",
        ),
    ] = False,
) -> None:
    """
    Update version in pyproject.toml to match latest git tag.

    Args:
        toml_file: Path to pyproject.toml.
        fix: If set, automatically update the version in pyproject.toml to match the latest git tag.

    Raises:
        Exit: With a non-zero exit code if the versions don't match, whether or not they were fixed.
    """
    version_pyproject = find_version_in_toml(toml_file)

    if version_pyproject != (version_git := find_latest_tag()):
        if not fix:
            typer.echo(
                f"In pyproject.toml, found tool.poetry.version = {version_pyproject}. Expected {version_git}. "
                f"Run with the `--fix` option to automatically sync.",
                err=True,
            )
            raise typer.Exit(code=1)

        write_new_version_to_toml(toml_file, version_pyproject, version_git)
        typer.echo("Syncing version in pyproject.toml to match latest git tag.", err=True)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    sync_pyproject_version()
