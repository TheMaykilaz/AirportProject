# Code Linting with Ruff

This project uses [Ruff](https://docs.astral.sh/ruff/) for fast Python linting and formatting.

## Quick Start

### Run Linting Locally

```bash
# Inside Docker container
docker-compose exec web ruff check .

# Fix auto-fixable issues
docker-compose exec web ruff check . --fix

# Format code
docker-compose exec web ruff format .

# Check formatting without modifying files
docker-compose exec web ruff format --check .
```

### Using the Lint Script

```bash
# Make script executable (Linux/Mac)
chmod +x lint.sh

# Run linting and formatting
./lint.sh
```

## Configuration

Ruff configuration is in `ruff.toml`. Key settings:

- **Line length**: 120 characters (Django standard)
- **Target**: Python 3.12
- **Rules enabled**: 
  - `E`, `W` - pycodestyle errors and warnings
  - `F` - pyflakes
  - `I` - isort (import sorting)
  - `N` - pep8-naming
  - `UP` - pyupgrade
  - `B` - flake8-bugbear
  - `DJ` - flake8-django
  - And more...

### Per-File Ignores

- `migrations/` - All rules ignored
- `views.py`, `urls.py` - Unused imports allowed (re-exports)
- `__init__.py` - Unused imports allowed
- `settings.py` - Long lines allowed

## CI/CD Integration

Ruff runs automatically in GitLab CI on every push and merge request:

1. **Lint stage** - Checks code quality
2. Currently set to `allow_failure: true` (warnings only)
3. View results in GitLab CI pipeline

## Pre-commit Hooks (Optional)

Install pre-commit hooks to run Ruff automatically before commits:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

## Common Issues

### Undefined Names (F821)
If you see "undefined name" errors, ensure all imports are present:
```python
from django.db.models import Q  # Missing import
```

### Unused Imports (F401)
- If imports are used in `urls.py`, they're allowed in `views.py`
- Add `# noqa: F401` to specific lines if needed

### Import Sorting (I001)
Ruff automatically sorts imports. Run `ruff check --fix` to fix.

## Disable Specific Rules

```python
# Disable for entire file
# ruff: noqa

# Disable specific rule for line
result = some_function()  # noqa: F841

# Disable specific rule for file
# ruff: noqa: F401
```

## Resources

- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Ruff Rules](https://docs.astral.sh/ruff/rules/)
- [Configuration Options](https://docs.astral.sh/ruff/configuration/)
