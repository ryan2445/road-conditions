# Road Conditions

Traffic camera and road condition tracker with a Python backend and Svelte frontend.

## Linting & Formatting

### Frontend (`frontend/`)

Uses ESLint and Prettier (configured in `eslint.config.js` and `.prettierrc`).

```bash
cd frontend
npm run lint          # Lint with ESLint
npm run format        # Format with Prettier
npm run format:check  # Check Prettier formatting
npm run check         # Type-check
```

### Backend (`backend/`)

Uses Ruff and mypy (configured in `pyproject.toml`).

```bash
cd backend
uv run ruff check .   # Lint (add --fix to auto-fix)
uv run ruff format .  # Format (use --check to verify)
uv run mypy .         # Type-check
```
