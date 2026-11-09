# AGENTS.md

## Project shape

LimpiaHuancayo backend is early-stage. Python 3.14 + `uv`. The FastAPI app lives in `src/backend/` (entrypoint `backend.main:app`), packaged as `backend` through `uv_build`'s `src/` layout. Most domain logic is implemented in PostgreSQL routines under `database/`. The API currently exposes `GET /`, `GET /health`, `POST /api/usuarios/registro`, and read-only catalogs under `/api/catalogos` (`distritos`, `tipos-reporte`, `estados-reporte`); `/health` checks only the HTTP server, not PostgreSQL.

## Commands

- Use `uv` for everything. Bare `python` is not available (Windows Store alias); use `uv run python ...` or `.venv\Scripts\python`.
- `uv sync` — install/refresh dependencies from `pyproject.toml` + `uv.lock`.
- `uv run uvicorn backend.main:app --reload` — run the API from the repository root. Swagger UI: `http://127.0.0.1:8000/docs`.
- `uv run python test_conexion.py` — manual DB connectivity smoke script; it is not pytest.
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
- Public registration creates only `Ciudadano`; `sp_usuario_registrar` assigns the role. Passwords are hashed with Argon2id in the service and never stored or logged in plaintext.
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

- `src/backend/` — FastAPI application; `src/backend/main.py` is the entrypoint.
- `src/backend/core/` — `.env` settings, the psycopg 3 connection helper, and shared exceptions.
- `src/backend/apis/` — HTTP routers (`catalogos.py`, `usuarios.py`).
- `src/backend/services/` — application orchestration (`catalogos.py`, `usuarios.py`).
- `src/backend/repositories/` — stored-routine access (`catalogos.py`, `usuarios.py`).
- `src/backend/schemas/` — Pydantic request/response models (`catalogos.py`, `usuarios.py`).
- `database/` — numbered SQL scripts, applied manually in order.
- `test_conexion.py` — standalone script at the root, not a test package.
