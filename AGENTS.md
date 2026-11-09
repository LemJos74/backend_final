# AGENTS.md

## Project shape

LimpiaHuancayo backend is early-stage. Python 3.14 + `uv`. The FastAPI app lives in `app/` (entrypoint `app.main:app`); `src/backend/` is the original scaffold and still only prints a placeholder. Most domain logic is implemented in PostgreSQL routines under `database/`. The API currently exposes only `GET /` and `GET /health`; `/health` does not check PostgreSQL.

## Commands

- Use `uv` for everything. Bare `python` is not available (Windows Store alias); use `uv run python ...` or `.venv\Scripts\python`.
- `uv sync` — install/refresh dependencies from `pyproject.toml` + `uv.lock`.
- `uv run uvicorn app.main:app --reload` — run the API from the repository root. Swagger UI: `http://127.0.0.1:8000/docs`.
- `uv run python test_conexion.py` — manual DB connectivity smoke script; it is not pytest.
- `uv run backend` — legacy placeholder entrypoint only.
- No lint, format, typecheck, test, or CI config exists. Do not invent pytest/ruff/mypy commands.

## Architecture (required)

- Layers: `apis → services → repositories`; `schemas` for Pydantic models and `core` for configuration/connections.
- No ORM, SQLAlchemy, or Alembic.
- Repositories access PostgreSQL only through stored routines:
  - reads: `SELECT * FROM public.fn_...(...)`
  - writes: `CALL public.sp_...(...)`
- Never run direct `SELECT/INSERT/UPDATE/DELETE` against tables from Python.
- Do not change the schema or existing routines without explicit approval. Add new numbered SQL scripts instead.
- Backend and frontend are separate Git repositories.

## Domain rules

- Roles: `Ciudadano` and `Administrador`.
- Citizens register, log in, create reports, and can read only their own reports.
- Reports are immutable after creation: no edit/delete routines or endpoints.
- Only administrators change report state and admin observations.
- `Resuelto` and `Rechazado` are final states.
- Report/map data requires authentication.

## Database

- `.env` at the repo root supplies `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`; it is gitignored and must never be committed.
- Setup is manual (psql/pgAdmin). Prerequisite: database `limpiahuancayo` and role `limpiahuancayo_app` exist. Run as table/routine owner, in order:
  `01_esquema.sql` → `02_datos_iniciales.sql` → `03_usuarios_rutinas.sql` → `04_permisos_usuarios.sql` → `05_catalogos_consulta.sql`.
- `03` creates the user routines; `04` sets `SECURITY DEFINER`/`search_path` and grants EXECUTE to `limpiahuancayo_app`; `05` creates and grants the three catalog functions. If `03` is re-run, re-run `04`.
- The app role must have EXECUTE on routines and no direct table privileges. Keep it that way.
- Scripts use `IF NOT EXISTS`; they do not migrate existing tables. Do not re-run them blindly on a populated database.
- Naming: `fn_*` are read/list functions, `sp_*` are mutation procedures. Preserve Spanish error messages and SQLSTATE codes (`22023` validation, `P0002` not found).
- `test_conexion.py` exercises only `fn_tipo_reporte_listar()` (defined in `05`); it does not test user routines or the API.
- `database/README.txt` documents the current setup order.

## Layout

- `app/` — FastAPI application; `app/main.py` is the entrypoint.
- `app/core/` — `.env` settings and the psycopg 3 connection helper.
- `app/apis/`, `app/services/`, `app/repositories/`, `app/schemas/` — layer packages (empty for now).
- `database/` — numbered SQL scripts, applied manually in order.
- `src/backend/` — legacy scaffold; do not add new API code there.
- `test_conexion.py` — standalone script at the root, not a test package.
