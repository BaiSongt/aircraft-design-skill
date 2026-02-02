# Project Rules for Aircraft Design Tool

## Lint Commands
- **Check**: `ruff check .`
- **Fix auto-fixable issues**: `ruff check --fix .`
- **Format**: `ruff format .`

## Type Check Commands
- **Type check**: `mypy aircraft_design/`
- **Strict mode** (optional): `mypy --strict aircraft_design/`

## Combined Quality Check
```bash
ruff check . && ruff format --check . && mypy aircraft_design/
