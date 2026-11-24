# LimpiaHuancayo — Backend

LimpiaHuancayo es un proyecto universitario para registrar y dar seguimiento a reportes ciudadanos sobre residuos en Huancayo. Los ciudadanos pueden registrar reportes geolocalizados, adjuntar una fotografía y consultar sus propios reportes. Los administradores pueden consultar todos los reportes y gestionar sus estados.

La API usa **Python 3.14**, **FastAPI**, **PostgreSQL 18**, **psycopg 3** y **JWT HS256**. El proyecto usa **uv** para gestionar Python, las dependencias y la ejecución. El código está en `src/backend/` y los scripts de base de datos están en `database/`.

## 1. Preparar Windows y abrir el proyecto

- Instala Git y abre una terminal PowerShell.
- Instala Visual Studio Code. Abre **Archivo → Abrir carpeta** y selecciona la raíz del backend, donde están `pyproject.toml` y `uv.lock`. Abre **Terminal → Nueva terminal**. Si tienes `code` en el PATH, también puedes ejecutar `code .` desde esa carpeta. [VS Code para Windows](https://code.visualstudio.com/docs/setup/windows)
- Instala uv y abre una terminal nueva para que reconozca el comando. [Instalación de uv](https://docs.astral.sh/uv/getting-started/installation/)
- Instala PostgreSQL 18 con las herramientas de línea de comandos. Para los ejemplos, el servidor usa `localhost:5432` y el rol de administración `postgres`. pgAdmin 4 es opcional y el manual SQL explica cómo usarlo para preparar el administrador inicial. [PostgreSQL para Windows](https://www.postgresql.org/download/windows/)

Desde la raíz del backend, instala las dependencias con uv y comprueba la versión de Python del proyecto.

```powershell
uv --version
uv sync
uv run python --version
```

## 2. Configurar el entorno

Copia [`.env.example`](.env.example) a `.env` en la raíz del backend y completa los valores de tu instalación local. El código carga ese archivo al iniciar y las variables ya definidas en la terminal tienen prioridad. Mantén `.env`, las contraseñas y los tokens fuera de Git. [Configuración del backend](src/backend/core/config.py)

| Variable | Valor predeterminado o esperado |
| --- | --- |
| `APP_NAME` | `LimpiaHuancayo API` |
| `DB_HOST` | `localhost` |
| `DB_PORT` | `5432` |
| `DB_NAME` | `limpiahuancayo` |
| `DB_USER` | Configura `limpiahuancayo_app`. |
| `DB_PASSWORD` | Usa la contraseña local del rol de aplicación. |
| `DB_SSLMODE` | `prefer` en local. Usa `verify-full` para Supabase. |
| `DB_SSLROOTCERT` | Vacío en local. Ruta del certificado CA cuando se usa `verify-full`. |
| `JWT_SECRET` | Define un secreto aleatorio de al menos 32 caracteres. |
| `JWT_ALGORITHM` | `HS256`, único algoritmo admitido. |
| `JWT_EXPIRE_MINUTES` | `30`. Debe ser un entero positivo. |
| `CORS_ORIGINS` | Vacío con el proxy de Angular. En Render, indica los orígenes exactos del frontend separados por comas. |
| `REPORTES_FOTOS_DIR` | `storage/reportes`. Las rutas relativas se resuelven desde la raíz del backend. |

## 3. Preparar PostgreSQL

### Base nueva

Desde PowerShell, abre `psql` como `postgres`. Si está en el PATH, puedes usar `psql` directamente. El ejemplo usa la ruta habitual de PostgreSQL 18 en Windows.

```powershell
$psql = 'C:\Program Files\PostgreSQL\18\bin\psql.exe'
& $psql -X -h localhost -p 5432 -U postgres -W -d postgres
```

Dentro de `psql`, crea la base y el rol si todavía no existen. `\password` solicita la contraseña del rol de aplicación de forma interactiva.

```sql
CREATE DATABASE limpiahuancayo;
CREATE ROLE limpiahuancayo_app LOGIN;
\password limpiahuancayo_app
GRANT CONNECT ON DATABASE limpiahuancayo TO limpiahuancayo_app;
\connect limpiahuancayo
GRANT USAGE ON SCHEMA public TO limpiahuancayo_app;
\quit
```

El rol de aplicación debe poder conectarse, usar el esquema y ejecutar las rutinas autorizadas por los scripts. Reserva los permisos directos sobre tablas para los roles que administran la base. Usa `limpiahuancayo_app` en el backend.

Aplica los scripts **01 a 23**, en el orden exacto del [manual de base de datos](database/README.txt), como propietario de las tablas y rutinas. Desde la raíz del backend, este comando muestra cómo aplicar el primer archivo. Cambia el archivo en cada paso y detente si `psql` devuelve un error.

```powershell
$env:PGCLIENTENCODING = 'UTF8'
& $psql -X -h localhost -p 5432 -U postgres -W -d limpiahuancayo -v ON_ERROR_STOP=1 -f '.\database\01_esquema.sql'
```

Al llegar al **06**, sigue las instrucciones de inicialización del Administrador en el manual. Los parámetros de ese paso y el script deben ejecutarse en la misma sesión. Después continúa del 07 al 23. El registro de ciudadanos se realiza mediante la API.

### Base existente con los scripts 01–21 aplicados

Genera un respaldo de la base y comprueba en el catálogo de PostgreSQL si ya existe el procedimiento de RF03.

```sql
SELECT to_regprocedure(
    'public.sp_reporte_registrar_con_fotografia(bigint,bigint,bigint,text,varchar,numeric,numeric,text,bigint)'
);
```

Si devuelve `NULL`, aplica el **script 22** como propietario. Si devuelve la rutina, el 22 ya está instalado. Evita reejecutar los scripts 01–21 sobre la base existente. Después comprueba si falta el 23 y sigue el orden del [manual de base de datos](database/README.txt).

```powershell
$env:PGCLIENTENCODING = 'UTF8'
& $psql -X -h localhost -p 5432 -U postgres -W -d limpiahuancayo -v ON_ERROR_STOP=1 -f '.\database\22_reportes_fotografias.sql'
```

Antes de habilitar el filtro administrativo por fecha, comprueba si existe `public.fn_reporte_listar_admin_por_fecha(bigint,bigint,bigint,bigint,integer,integer,date,date)` con `to_regprocedure`. Si falta y el 22 ya está instalado, ejecuta el mismo comando con `-f '.\database\23_reportes_admin_fechas.sql'`.

## 4. Iniciar y detener el servidor

```powershell
uv run uvicorn backend.main:app --reload
```

- [Swagger UI](http://127.0.0.1:8000/docs) permite explorar los endpoints y enviar solicitudes.
- [Estado del servidor](http://127.0.0.1:8000/health) devuelve `{"status":"ok"}` cuando el servidor HTTP responde. Para comprobar también la conexión a PostgreSQL y una consulta al catálogo, define explícitamente las cinco variables `DB_*` en `.env` y ejecuta `uv run python test_conexion.py` desde la raíz.

Para detener el servidor, pulsa **Ctrl+C** en la terminal donde se ejecuta Uvicorn.

## 5. Registrar una cuenta de prueba y obtener un JWT

1. En Swagger, abre `POST /api/usuarios/registro`, selecciona **Try it out** y envía un objeto JSON con `nombre`, `email` y `password`. Usa un nombre y un correo de prueba válidos, y una contraseña de al menos ocho caracteres. Espera **201** con el `id` de la cuenta. El registro público asigna el rol **Ciudadano**.
2. Abre `POST /api/auth/login` y envía `email` y `password` de esa cuenta. La respuesta contiene `access_token`, `token_type` y `expires_in`.
3. Pulsa **Authorize** y pega únicamente el valor de `access_token`. Swagger añade el prefijo `Bearer`. Ejecuta `GET /api/auth/me` y confirma que el rol sea `Ciudadano`.

Las contraseñas se reciben en los endpoints de registro e inicio de sesión. El backend almacena un hash **Argon2id** al registrar la cuenta y lo verifica al iniciar sesión. Usa el endpoint de registro para crear las cuentas ciudadanas de prueba. [Seguridad del backend](src/backend/core/security.py)

## 6. Probar reportes y fotografías

Con la cuenta de Ciudadano autorizada en Swagger, consulta `GET /api/catalogos/distritos` y `GET /api/catalogos/tipos-reporte` para obtener los identificadores válidos. Las altas de esta sección crean registros en la base configurada. Úsalas en un entorno de desarrollo con datos de prueba.

**Sin fotografía.** En `POST /api/reportes`, selecciona **Try it out** y envía JSON con los siguientes campos. Sustituye los identificadores por los del catálogo de tu base.

```json
{
  "distrito_id": 1,
  "tipo_id": 1,
  "descripcion": "Reporte de prueba",
  "ubicacion": "Punto de prueba en Huancayo",
  "latitud": -12.0684,
  "longitud": -75.2103
}
```

**Con fotografía.** En `POST /api/reportes/con-fotografia`, selecciona **Try it out**, completa los mismos campos y elige un archivo en `fotografia`. Swagger envía `multipart/form-data`. Usa un JPEG, PNG o WebP estático de hasta **5 MiB** y **24 millones de píxeles**. El backend lo normaliza a JPEG y elimina los metadatos. En ambos casos, la respuesta esperada es **201** con el `id` del reporte.

**Detalle y descarga.** Consulta `GET /api/reportes/{reporte_id}` con el ID devuelto. El detalle incluye `tiene_fotografia` y una `fotografia_url` relativa, o `null` si el reporte no tiene foto. Ejecuta `GET /api/reportes/{reporte_id}/fotografia` desde Swagger con el token activo. Fuera de Swagger, un cliente HTTP debe enviar la cabecera `Authorization` con el esquema `Bearer`. El propietario o un Administrador activo recibe **200**, `Content-Type: image/jpeg` y `Cache-Control: private, no-store`. Sin token se espera **401** y para otro Ciudadano se espera **404**.

En desarrollo las fotos se guardan en el directorio local definido por `REPORTES_FOTOS_DIR`. La API expone la URL de descarga autenticada y conserva la clave del archivo internamente. Supabase Storage todavía no está integrado.

## 7. Resolver problemas frecuentes

| Síntoma | Qué revisar |
| --- | --- |
| PostgreSQL rechaza la conexión o agota el tiempo de espera | Comprueba que el servicio de PostgreSQL 18 esté iniciado y que `DB_HOST`, `DB_PORT` y `DB_NAME` coincidan con tu instalación. Ejecuta la comprobación manual de conexión. |
| PostgreSQL rechaza la contraseña | Revisa `DB_USER`, `DB_PASSWORD` y las variables de la terminal. El backend usa la contraseña del rol de aplicación. |
| La API no inicia por un error JWT | Comprueba que `JWT_SECRET` tenga al menos 32 caracteres, que el algoritmo sea `HS256` y que la caducidad sea un entero positivo. |
| Swagger devuelve `401` o `403` | Inicia sesión de nuevo si expiró el JWT. Comprueba que la cuenta esté activa y que su rol tenga acceso a la ruta. |
| `uv` no se reconoce o faltan dependencias | Abre otra terminal, verifica `uv --version` y ejecuta `uv sync` desde la raíz. Confirma Python 3.14 con `uv run python --version`. |
| Falta una rutina o PostgreSQL deniega su ejecución | Confirma la base de destino, el orden de instalación y el permiso `EXECUTE` de la rutina para `limpiahuancayo_app`. Para el alta con foto, comprueba que se haya aplicado el 22. |
| La carga de foto devuelve `413`, `415` o `422` | Revisa el tamaño, que la solicitud sea multipart, que incluya el campo `fotografia` y que el archivo se pueda abrir como una imagen estática admitida. |
| La foto no se guarda o no se puede recuperar | Comprueba que `REPORTES_FOTOS_DIR` sea accesible para el proceso de Uvicorn y que tenga permisos de lectura y escritura. Si cambiaste el directorio, comprueba dónde quedaron las fotos ya registradas. |

## 8. Comandos Git de referencia

```powershell
git status --short --branch
git diff
git log -5 --oneline
git switch -c docs/guia-backend
```

Revisa los cambios antes de preparar un commit y mantén fuera del repositorio `.env`, los respaldos y las fotografías locales.

## 9. Preparar Supabase y Render

### PostgreSQL en Supabase

1. En el proyecto de Supabase, abre **Connect → Session pooler** y copia el host, el puerto y el nombre de la base que muestra el panel. El pooler de sesión permite usar psycopg sin cambios en el acceso a las rutinas. Descarga la CA desde **Database Settings → SSL Configuration**. [Conexiones a PostgreSQL en Supabase](https://supabase.com/docs/guides/database/connecting-to-postgres)
2. Usa el rol propietario para preparar la base. Crea el rol SQL `limpiahuancayo_app` con `LOGIN` y contraseña propia, con acceso al esquema y ejecución de las rutinas. En un proyecto dedicado a LimpiaHuancayo, desactiva la **Data API** si no la usas. Revisa los privilegios de `anon`, `authenticated`, `service_role` y `PUBLIC` sobre los objetos de LimpiaHuancayo, incluidos los privilegios por defecto, antes de exponer el servicio. [Seguridad de la Data API](https://supabase.com/docs/guides/api/securing-your-api)
3. En una base nueva, aplica manualmente los scripts 01–23 en orden, como propietario y con UTF-8. Sobre una base existente, revisa la versión y aplica solo los scripts faltantes. El contenedor arranca FastAPI y la instalación de SQL se realiza por separado. [Orden de instalación](database/README.txt)

### FastAPI en Render

Crea manualmente un **Web Service** desde el repositorio GitHub del backend cuando esté publicado.

| Campo | Valor |
| --- | --- |
| Runtime | Docker |
| Root Directory, Docker Build Context | Raíz del repositorio, `.` |
| Dockerfile Path | `./Dockerfile` |
| Docker Command | Dejar vacío para usar el `CMD` del Dockerfile. |
| Health Check Path | `/health` |

El comando del contenedor es `uv run --no-sync uvicorn backend.main:app --host 0.0.0.0 --port "$PORT"`, con valor de respaldo `10000`. [Docker en Render](https://render.com/docs/docker)

| Variable de Render | Valor |
| --- | --- |
| `DB_HOST`, `DB_PORT`, `DB_NAME` | Valores de **Session pooler** en Supabase, normalmente puerto `5432` y base `postgres`. |
| `DB_USER` | `limpiahuancayo_app.<project-ref>` para Session pooler. |
| `DB_PASSWORD` | Contraseña del rol de aplicación. |
| `DB_SSLMODE` | `verify-full` |
| `DB_SSLROOTCERT` | `/etc/secrets/supabase-root.crt`. Carga la CA con ese nombre en **Secret Files**. |
| `JWT_SECRET` | Secreto propio de LimpiaHuancayo, aleatorio y de al menos 32 caracteres. |
| `CORS_ORIGINS` | Origen HTTPS exacto del Static Site, sin ruta. Agrega dominios adicionales explícitamente si los usas. |
| `APP_NAME`, `JWT_ALGORITHM`, `JWT_EXPIRE_MINUTES` | Opcionales. Conservan los valores predeterminados indicados en esta guía. |
| `REPORTES_FOTOS_DIR` | `/app/storage/reportes` de forma predeterminada en Docker. |

Mantén los secretos en el servicio del backend. Tras desplegar, prueba `GET /health` y `GET /api/catalogos/estados-reporte`. El segundo comprueba la conexión y la ejecución de una rutina con el rol de aplicación. Configura el origen público del backend como `API_BASE_URL` en el Static Site y prueba una recarga directa en `/ciudadano/reportes`. [Archivos secretos en Docker](https://render.com/docs/docker-secrets)

### Fotografías persistentes

El proveedor activo guarda JPEG en el sistema de archivos local. Render usa un sistema de archivos efímero por defecto. Si se habilitan reportes con foto antes de integrar Storage, adjunta un disco persistente en `/app/storage/reportes` y comprueba que sea escribible por el usuario del contenedor. Sin persistencia, un reinicio puede dejar referencias en PostgreSQL a archivos que ya no existen. [Discos persistentes de Render](https://render.com/docs/disks)

La solución prevista es un **bucket privado** de Supabase Storage y un proveedor nuevo de `AlmacenFotografias` en el backend. Las credenciales se configurarían solo en FastAPI. Se conservaría la clave opaca en `imagen_path` y el endpoint existente seguiría autorizando al propietario o al administrador antes de servir el JPEG. Para trasladar fotos existentes, copia los objetos conservando sus claves y comprueba que se puedan recuperar antes de cambiar el proveedor. [Buckets privados de Supabase](https://supabase.com/docs/guides/storage/buckets/fundamentals) · [Interfaz de almacenamiento](src/backend/core/almacenamiento_fotografias.py)

## 10. GitHub Actions

[Backend CI/CD](.github/workflows/ci-cd.yml) valida los pushes a `master`, los pull requests dirigidos a `master` y las ejecuciones manuales. En Ubuntu usa Python 3.14 y uv 0.13.6, instala las dependencias de `uv.lock` con `uv sync --locked`, compila la sintaxis de Python, inicia FastAPI en loopback y exige que `GET /health` devuelva `{"status":"ok"}`. También construye la imagen con el Dockerfile del repositorio.

`/health` comprueba el arranque y la respuesta HTTP de la API. La comprobación usa configuración ficticia, deshabilita la carga de `.env` y apunta PostgreSQL a loopback. Actualmente el repositorio carece de una suite automatizada y de herramientas de análisis estático configuradas. `test_conexion.py` es una comprobación manual de PostgreSQL y CI solo compila su sintaxis.

El job de despliegue requiere CI exitoso. Un push a `master` puede activarlo automáticamente. En una ejecución manual, selecciona `master` y marca `deploy` para solicitarlo. Los pull requests solo ejecutan CI. GitHub serializa las solicitudes al hook y puede reemplazar una solicitud pendiente por otra más reciente. Antes de llamar al hook, el job verifica que el SHA validado sigue siendo la punta de `master`. Render recibe ese SHA en `ref` y construye la imagen a partir de ese commit. Un HTTP 200 o 202 confirma que Render aceptó la solicitud. El estado final se consulta en **Deploys**. [Concurrencia en GitHub Actions](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency) · [Deploy Hooks de Render](https://render.com/docs/deploy-hooks)

### Configuración manual

1. En Render, comprueba que el **Web Service** del backend usa Docker, apunta a `LemJos74/backend_final` en `master` y conserva `/health` como ruta de salud. Desactiva **Auto-Deploy** antes de habilitar el pipeline. Si has habilitado vistas previas automáticas de pull requests para este servicio, desactívalas también.
2. Copia el **Deploy Hook** del servicio backend desde **Settings**. En GitHub, guárdalo en **Settings → Secrets and variables → Actions → Secrets** como secreto de repositorio `RENDER_DEPLOY_HOOK`. Usa la URL completa generada por Render. El workflow añadirá `ref`.
3. Conserva las credenciales de PostgreSQL, el secreto JWT y el certificado en Render. GitHub Actions solo necesita el secreto del hook.
4. Cuando se autorice publicar el workflow, abre un pull request hacia `master` y verifica que **Validar backend** termine correctamente y que el job de despliegue se omita. Cuando se autorice el primer despliegue, comprueba en **Deploys** que Render publique el SHA esperado.

### Verificación local

Desde la raíz del backend, ejecuta en PowerShell con Docker en modo de contenedores Linux.

```powershell
uv sync --locked --python 3.14
uv run --locked --no-sync python -m compileall -q src test_conexion.py
docker build --tag limpiahuancayo-backend:ci .

$env:PYTHON_DOTENV_DISABLED = '1'
$env:JWT_SECRET = 'ci-only-placeholder-not-a-production-secret'
$env:DB_HOST = '127.0.0.1'
$env:DB_PORT = '1'
uv run --locked --no-sync uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

En otra terminal, ejecuta `curl.exe --fail --noproxy "*" http://127.0.0.1:8000/health` y comprueba que responde con `{"status":"ok"}`. Detén Uvicorn con **Ctrl+C**.
