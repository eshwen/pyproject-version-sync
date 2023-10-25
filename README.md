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

### Examples

With the default arguments:

![default](https://github.com/eshwen/pyproject-version-check/assets/24566108/280ab0e5-df54-4f5d-a91f-698e84ff8335)

With autofix:

![fix](https://github.com/eshwen/pyproject-version-check/assets/24566108/939d65b5-20ed-4d53-97c7-784b4999aa37)

(Styling shamelessly nicked from <https://github.com/ines/termynal>. Check out that repo for cool terminal animations!)
