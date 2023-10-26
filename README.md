# pyproject-version-sync

[![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/downloads/release/python-31012/)
[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://pre-commit.com/)

Pre-commit hook to sync the pyproject.toml version to the latest tag in the repo.

## Usage

To flag whether the latest tag in the repo matches the version in the `pyproject.toml` file, add the following to
your `.pre-commit-config.yaml`:

```yaml
  - repo: https://github.com/eshwen/pyproject-version-sync
    rev: v0.2.1
    hooks:
      - id: pyproject-version-sync
```

Or, to enable autofix:

```yaml
  - repo: https://github.com/eshwen/pyproject-version-sync
    rev: v0.2.1
    hooks:
      - id: pyproject-version-sync
        args: [--fix]
```

### Examples

With the default arguments:

![default](https://github.com/eshwen/pyproject-version-sync/assets/24566108/f04f16ab-069f-4ebf-bec6-cfee77a5bf9c)

With autofix:

![fix](https://github.com/eshwen/pyproject-version-check/assets/24566108/88fe1e2c-0a15-416c-8108-dbb756783c8d)

(Styling shamelessly nicked from <https://github.com/ines/termynal>. Check out that repo for cool terminal animations!)
