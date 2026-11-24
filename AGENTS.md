# AGENTS.md

## Entorno
- Backend LimpiaHuancayo: Python 3.14, `uv`, FastAPI, psycopg3 y PostgreSQL.
- Código en `src/backend/` (entrypoint `backend.main:app`); SQL en `database/`.
- Usar `uv` para todo. No usar `python` directo.
- `uv sync` instala dependencias. API: `uv run uvicorn backend.main:app --reload` desde la raíz. Swagger: `/docs`.
- `uv run python test_conexion.py` es un smoke manual de conexión, no una suite pytest.
- GitHub Actions es un requisito académico. Valida el backend con `uv sync --locked`, compilación de sintaxis, una comprobación HTTP de `/health` en loopback y un build Docker.
- Ejecuta las suites y herramientas de análisis configuradas cuando existan; incorpóralas al pipeline al añadirlas. Para CI usa valores ficticios y un entorno aislado, sin credenciales de producción ni ejecución de SQL.
- El CD en Render requiere CI exitoso en `master` y solicita el despliegue del SHA validado mediante un Deploy Hook guardado en GitHub Secrets.

## Arquitectura
- Capas: `apis` → `services` → `repositories`; `schemas` para Pydantic y `core` para configuración/conexión.
- Sin ORM, SQLAlchemy ni Alembic.
- Los repositories acceden a PostgreSQL solo mediante rutinas:
  - lecturas: `SELECT * FROM public.fn_...(...)`
  - escrituras: `CALL public.sp_...(...)`
- Prohibido ejecutar `SELECT/INSERT/UPDATE/DELETE` directo contra tablas desde Python.
- `fn_*` para lectura; `sp_*` para mutación.
- Usar `core.database.get_connection`; las escrituras se confirman con `with connection:`.
- Los repositories traducen SQLSTATE a excepciones de `core.exceptions`; las APIs las convierten en HTTP.
- No cambiar el esquema ni rutinas existentes sin aprobación explícita. Crear scripts SQL numerados; el orden vigente está en `database/README.txt`.
- Los scripts son manuales y no migran bases existentes; no reejecutarlos sobre una base poblada sin revisar.
- Las rutinas expuestas usan `SECURITY DEFINER` y `search_path` seguro.
- Mantener mensajes de error en español y los SQLSTATE existentes.
- Backend y frontend son repositorios Git separados.

## Seguridad
- Autenticación con JWT HS256; configuración y expiración en `core/config.py`/`.env`.
- Las rutas protegidas recargan el usuario desde PostgreSQL, leen su rol/estado y rechazan cuentas inactivas; nunca confiar en el rol del cliente ni en el JWT.
- Autorización con `requiere_rol(...)`; sin autenticación `401`, sin permiso `403`.
- Validar entrada y salida con Pydantic. No exponer secretos, contraseñas, hashes ni tokens en respuestas o logs.
- Contraseñas con Argon2id; nunca en texto plano.
- Aplicar mínimo privilegio en PostgreSQL: `limpiahuancayo_app` debe tener `EXECUTE` sobre las rutinas y ningún privilegio directo sobre tablas.

## Flujo de trabajo
- PLAN: investigar y proponer sin modificar archivos.
- Esperar aprobación explícita del usuario antes de implementar.
- BUILD: implementar únicamente el plan aprobado. Si cambia el alcance, volver a PLAN.
- Permitido: consultas SQL de diagnóstico de solo lectura; no alteran datos, esquema ni permisos.
- Requieren autorización explícita: ejecutar scripts SQL, cualquier operación de escritura sobre datos reales y las pruebas que modifiquen usuarios, reportes, estados o permisos, aunque sean temporales y se pretenda restaurar los datos.
- No hacer commits ni push sin autorización.
- No instalar ni actualizar dependencias sin autorización.

## Calidad
- Hacer cambios mínimos y enfocados; no modificar módulos ajenos ni descartar, sobrescribir o revertir cambios existentes que no pertenezcan a la tarea.
- Mantener compatibilidad con endpoints, contratos, datos y comportamientos existentes.
- Verificar los cambios con las pruebas o comprobaciones disponibles.
- Reportar resultados, riesgos y archivos modificados en español.

## Dominio
- Roles: `Ciudadano` y `Administrador`; el registro público crea solo `Ciudadano`.
- Un ciudadano solo accede a sus propios reportes y no puede editar su contenido tras registrarlo.
- Un administrador puede consultar todos los reportes y cambiar sus estados y observaciones mediante las transiciones autorizadas.
- `Resuelto` y `Rechazado` son estados finales.
- Los datos de reportes y mapa requieren autenticación.
