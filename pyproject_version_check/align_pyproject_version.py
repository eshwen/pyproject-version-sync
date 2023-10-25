"""This pre-commit hook ensures that the version in pyproject.toml matches the latest git tag."""
import argparse
import logging
import re
import subprocess
from pathlib import Path

import tomli

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)
LOGGER.addHandler(logging.StreamHandler())


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
    """
    pyproject_raw = Path.open(toml_file).read()

    # Ignore all the stuff after the block of interest
    # Avoids edge case where we may overwrite the version of something else in the file by mistake
    block = re.findall(
        rf"\[tool\.poetry\][^\n]*.*\nversion\s?=\s?[\"|\']{re.escape(version_pyproject)}[\"|\']\n",
        pyproject_raw,
        flags=re.DOTALL,
    )[0]
    new_block = block.replace(version_pyproject, version_git)

    pyproject_new = pyproject_raw.replace(block, new_block)
    with Path.open(toml_file, "w") as f_out:
        f_out.write(pyproject_new)


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
    toml_file = args.toml_file

    version_pyproject = find_version_in_toml(toml_file)

    if version_pyproject != (version_git := find_latest_tag()):
        if not fix:
            raise ValueError(
                f"In pyproject.toml, found tool.poetry.version = {version_pyproject}. Expected {version_git}. "
                f"Run with the `--fix` option to automatically update.",
            )

        LOGGER.info("Updating version in pyproject.toml to match latest git tag.")
        write_new_version_to_toml(toml_file, version_pyproject, version_git)


if __name__ == "__main__":
    main()
