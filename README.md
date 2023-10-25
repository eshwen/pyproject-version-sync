# pyproject-version-check

[![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/downloads/release/python-31012/)
[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://pre-commit.com/)

Pre-commit hook to align the pyproject.toml version with the latest tag in the repo.

## Usage

To flag whether the latest tag in the repo matches the version in the `pyproject.toml` file, add the following to
your `.pre-commit-config.yaml`:

```yaml
  - repo: https://github.com/eshwen/pyproject-version-check
    rev: v0.1.0
    hooks:
      - id: pyproject-version-check
```

Or, to enable autofix:

```yaml
  - repo: https://github.com/eshwen/pyproject-version-check
    rev: v0.1.0
    hooks:
      - id: pyproject-version-check
        args: [--fix]
```
