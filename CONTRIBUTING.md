# Contributing

## Philosophy

KISS, YAGNI, SOLID, Clean Code (Bob Martin). Small, focused commits. Add only what is asked
for; resist out-of-scope refactors and speculative features.

## Commits

[Conventional Commits](https://www.conventionalcommits.org/): `type(scope): description`

- Imperative mood, English, max 72 chars, no trailing period.
- Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `perf`, `ci`, `build`.

## Workflow

1. Create a branch.
2. Write tests first (TDD), then the implementation.
3. Ensure `ruff check`, `ruff format --check`, `mypy src/`, and `pytest` all pass.
4. Keep commits small and conventional.
5. Open a PR; CI must be green.

## Local setup

```bash
uv sync --extra dev
uv run pre-commit install
uv run pytest
```
