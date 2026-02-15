"""This pre-commit hook ensures that the version in pyproject.toml matches the latest git tag."""

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import TypeVar

import tomlkit
from tomlkit.toml_document import TOMLDocument

PATHS = ["tool.poetry.version", "project.version"]
T = TypeVar("T")


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


def traverse(toml: TOMLDocument, path: str, cls: type[T]) -> T | None:
    """
    Traverse given toml by a given dotted path and verify found type.

    Args:
        toml: Toml documet.
        path: Dotted path, like "a.b.c".
        cls: Expected class.

    Returns:
        Object at a given path or None if not found.
    """
    try:
        for part in path.split("."):
            toml = toml[part]  # type: ignore[assignment]

        if not isinstance(toml, cls):
            return None
    except Exception:  # noqa: BLE001
        return None
    else:
        return toml


def traverse_set(toml: TOMLDocument, path: str, value: object) -> None:
    """
    Traverse given toml by a given dotted path and set value.

    Args:
        toml: Toml documet.
        path: Dotted path, like "a.b.c".
        value: string or int.
    """
    parts = path.split(".")
    inner_path, tail = parts[:-1], parts[-1]
    for part in inner_path:
        if nxt := toml.get(part):  # noqa: SIM108
            toml = nxt
        else:
            toml = toml.add(part, {})  # type: ignore[assignment, arg-type]

    toml[tail] = value


def find_version_in_toml(pyproject: TOMLDocument) -> tuple[str, str]:
    """
    Find the project version in pyproject.toml.

    Args:
        pyproject: Parsed pyproject.toml.

    Returns:
        Project version.
    """
    # If user has invalid values it will error out
    versions: list[tuple[str, str]] = []
    for path in PATHS:
        version = traverse(pyproject, path, str)
        if version:
            versions.append((path, version))

    if len(versions) != 1:
        sys.exit(f"Expected exactly one version in pyproject.toml, got: {versions}")
    return versions[0]


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Update version in pyproject.toml to match latest git tag.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("toml_file", type=Path, help="Path to pyproject.toml.")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="If set, automatically update the version in pyproject.toml to match the latest git tag.",
    )
    return parser.parse_args()


def main() -> None:
    """Run the pre-commit hook."""
    args = parse_args()
    fix = args.fix

    path = Path(args.toml_file)
    pyproject = tomlkit.parse(path.read_bytes())

    version_path, version_pyproject = find_version_in_toml(pyproject)

    if version_pyproject != (version_git := find_latest_tag()):
        if not fix:
            sys.exit(
                f"In pyproject.toml, found tool.poetry.version = {version_pyproject}. Expected {version_git}. "
                f"Run with the `--fix` option to automatically sync.",
            )

        traverse_set(pyproject, version_path, version_git)
        tomlkit.dump(pyproject, path.open("w"))

        sys.exit("Syncing version in pyproject.toml to match latest git tag.")

    sys.exit()


if __name__ == "__main__":
    main()
