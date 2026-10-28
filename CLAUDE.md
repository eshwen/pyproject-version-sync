# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A [pre-commit](https://pre-commit.com/) hook that checks that `tool.poetry.version` in `pyproject.toml` matches the latest git tag in the repo, and with `--fix` rewrites the version to match. The package is a single module, `pyproject_version_sync/sync_pyproject_version.py`.

## Commands

Dependencies are managed with uv (Python >=3.11, uv 0.13.x), and the build backend is hatchling:

```bash
uv sync                                      # install with dev deps (the `dev` group includes lint/type)
uv run pre-commit run --all-files            # run every lint/format/type check
uv run ruff check --fix .                    # lint (wide rule set; Google-style docstrings required)
uv run ruff format .                         # format (line length 120)
uv run pyrefly check pyproject_version_sync  # type check (strict preset)
```

Run the hook against a Poetry project's pyproject.toml. It reads tags from the git repo in the current working directory. This repo's own `pyproject.toml` uses `[project]`, not `[tool.poetry]`, so the hook can't check it.

```bash
uv run --project /path/to/pyproject-version-sync sync_pyproject_version pyproject.toml [--fix]
```

To try the hook from another repo without publishing a tag, run `pre-commit try-repo /path/to/pyproject-version-sync pyproject-version-sync` from that repo.

There is no test suite. The `name-tests-test --pytest-test-first` pre-commit hook means any test files you add must be named `test_*.py`.

## How it works

- **Wiring:** `.pre-commit-hooks.yaml` defines the hook `pyproject-version-sync`, whose `entry` is the console script `sync_pyproject_version`. `[project.scripts]` in `pyproject.toml` maps that script to the Typer app `sync_pyproject_version`, whose single command is `cli()`. The hook only fires when `^pyproject\.toml$` is among the changed files, and pre-commit passes that path as the positional `toml_file` argument.
- **Latest tag:** `git rev-list --tags --max-count=1` gives the most recently tagged commit, and `git describe --tags` on that commit gives the tag name. The regex `^v?(\d+\.\d+\.\d+)` takes the version from it, so a leading `v` and any suffix such as `-rc1` are dropped. A tag that isn't strict `X.Y.Z` raises `IndexError`.
- **Reading the version:** the file is parsed with `tomli`, and only `[tool.poetry].version` is read. PEP 621 `[project].version` isn't supported.
- **Writing the version (`--fix`):** the file is edited as raw text rather than re-serialised, so formatting and comments are kept. A single `re.subn` replaces only the value of the first `version = "..."` line inside the `[tool.poetry]` table. The pattern won't skip past a line starting with `[`, so it can't reach a later table, and other `version` keys aren't touched. If there's no match it raises `ValueError` rather than writing the file unchanged.
- **Exit codes:** the script exits non-zero both when it finds a mismatch and when it fixes one. That's intentional: pre-commit fails the commit so the user can stage the updated file.

## Conventions and gotchas

- The README's usage examples pin `rev: v0.2.1`. When releasing, bump `project.version`, tag the release, and update those README `rev:` values.
- The comments in `.pre-commit-config.yaml` say tool revisions should match `uv.lock`. Dependency bumps to `pyproject.toml`/`uv.lock` don't update the pre-commit revs, so they drift.
- `auto-walrus` runs in pre-commit and rewrites assignments into walrus expressions where it can.
- `.claude/settings.json` sets up two Claude Code hooks. Any Bash call that runs `git commit` first runs `.claude/hooks/require-pre-commit.sh`, which runs `uv run pre-commit run --all-files` and blocks the commit if it fails. Every `.py` file Claude writes or edits is formatted with `ruff format` afterwards.
