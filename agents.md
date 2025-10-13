# agents

This repository uses a consistent workflow:

- Format code with `black` using the default configuration.
- Lint with `flake8` and respect the settings in `setup.cfg`.
- Run the test suite with `pytest`.

All pull requests must run and pass these checks locally before submission.
# Repository Guidelines

## Project Structure & Module Organization
- `smtpburst/` core Python package (sending, discovery, auth, pipeline, reporting).
- `tests/` pytest suite (`tests/test_*.py`). Avoid real network calls; mock I/O.
- `examples/` sample configs/pipelines (e.g., `examples/config.yaml`).
- `scripts/` helper scripts for tests and packaging.
- Top-level: `README.md`, `spec.md`, `pyproject.toml`, `setup.cfg`, `requirements-dev.txt`.

## Build, Test, and Development Commands
- Install dev deps: `pip install -r requirements-dev.txt && pip install -e .`
- Run tests: `pytest` or `./scripts/run_tests.sh` (with coverage).
- Format: `black .` (CI uses `black --check .`).
- Lint: `flake8` (rules in `setup.cfg`).
- Run locally: `python -m smtpburst --help` or entry point `smtp-burst`.
- Package (optional): `./scripts/build_macos.sh`, `./scripts/build_ubuntu.sh`.

## Coding Style & Naming Conventions
- Python 3.11+. Use `black` defaults; line length enforced via flake8 (88).
- Ignore rules: E203, W503; see `setup.cfg`.
- Naming: `snake_case` for functions/vars, `PascalCase` for classes, `SCREAMING_SNAKE_CASE` for constants.
- Keep modules focused; prefer small PRs. Add/adjust docstrings where useful.

## Testing Guidelines
- Framework: `pytest` with coverage. Place tests in `tests/` as `test_*.py`.
- Use `monkeypatch`/fakes to avoid external network; do not rely on real SMTP/DNS.
- Add tests for new CLI flags, config parsing, and edge cases.
- Run locally: `pytest -q`; ensure `black --check .` and `flake8` pass before PR.

## Commit & Pull Request Guidelines
- Commits: concise, imperative (“Add async sender”, “Fix TLS probe error”).
- PRs must include: purpose/summary, scope of changes, testing notes, and any docs updates (README/examples/spec) if flags or behavior change.
- Requirements to merge: `black --check .`, `flake8`, and `pytest` all pass locally.
- Avoid version bumps and unrelated refactors. Update examples when introducing new pipeline actions.

## Security & Configuration Tips
- Configuration lives in `smtpburst/config.py` and CLI (`smtpburst/cli.py`).
- Optional deps: `PyYAML`, `dnspython`, `aiosmtplib`. Guard imports; keep graceful fallbacks.
- When adding network features, provide timeouts, input validation, and clear error messages.
