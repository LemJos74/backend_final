LimpiaHuancayo - scripts de base de datos

Prerrequisito: crear la base de datos limpiahuancayo y el rol de aplicacion
limpiahuancayo_app en PostgreSQL.

Orden de ejecucion (conectado a limpiahuancayo y como propietario de las
tablas y rutinas):
1. 01_esquema.sql
2. 02_datos_iniciales.sql
3. 03_usuarios_rutinas.sql
4. 04_permisos_usuarios.sql
5. 05_catalogos_consulta.sql
6. 06_admin_inicial.sql

04 aplica SECURITY DEFINER, search_path y permisos EXECUTE al rol de
aplicacion para las rutinas de usuarios. 05 crea las funciones de consulta
de los tres catalogos. Si se vuelve a ejecutar 03, ejecutar 04 otra vez.

06 crea el primer usuario Administrador. Se ejecuta una sola vez, como
propietario, y es idempotente: si ya existe un Administrador no crea otro,
no modifica usuarios existentes y no concede permisos a limpiahuancayo_app.
No ejecutar 06 como limpiahuancayo_app.

Generar el hash Argon2id desde la raiz del proyecto. El siguiente bloque
evita que la contrasena quede en el historial de PowerShell:

  $seguro = Read-Host "Contrasena del administrador" -AsSecureString
  $credencial = New-Object System.Net.NetworkCredential("", $seguro)
  $texto = $credencial.Password
  $texto | uv run python -c "import sys; from backend.core.security import hash_password; print(hash_password(sys.stdin.readline().rstrip('\r\n')))"
  Remove-Variable texto, credencial, seguro

Copiar solo la linea que empieza con $argon2id$. Si uv muestra avisos de
compilacion, ignorarlos y copiar unicamente el hash.

Alternativa en una terminal interactiva:

  uv run python -c "from getpass import getpass; from backend.core.security import hash_password; print(hash_password(getpass('Contrasena del administrador: ')))"

La alternativa con getpass necesita una terminal interactiva real; en un
shell no interactivo puede quedarse esperando entrada.

En pgAdmin 4, abrir una Query Tool y ejecutar los parametros en la misma
sesion antes de ejecutar el archivo 06_admin_inicial.sql:

  SET lh.admin_email  = 'correo-del-administrador';
  SET lh.admin_nombre = 'Nombre del administrador';
  SET lh.admin_hash   = '<hash Argon2id generado localmente>';

Las sentencias SET con valores reales pueden quedar registradas en el
historial de pgAdmin (Query Tool history), aunque el script ejecute RESET.
RESET solo limpia la variable de la sesion, no el historial del cliente.
Use una pestana temporal, no guarde la consulta y borre el historial al
terminar.

Si el bloque DO falla, la transaccion queda abortada. En la misma Query
Tool ejecute:

  ROLLBACK;

Despues corrija los parametros y vuelva a ejecutar. No se habra creado ni
modificado ninguna cuenta. Si el error es por estar conectado como
limpiahuancayo_app, cierre la sesion y reconecte como propietario.

No guardar el hash ni la contrasena en el archivo SQL, en .env ni en Git.
Si se ejecuta 06 sin esos parametros, el script aborta sin crear nada.
El script tampoco promueve ciudadanos: si el correo ya existe con otro rol,
aborta sin modificar la cuenta.

Verificar el administrador (como propietario):

SELECT u.id, u.email, r.nombre AS rol, u.activo
FROM public.usuarios u
JOIN public.roles r ON r.id = u.rol_id
WHERE r.nombre = 'Administrador';

Verificar los catalogos:
SELECT * FROM roles;
SELECT * FROM distritos;
SELECT * FROM tipos_reporte;
SELECT * FROM estados_reporte;

El rol limpiahuancayo_app no debe tener privilegios directos sobre las
tablas; solo EXECUTE sobre las rutinas almacenadas.

No ejecutar en una base existente sin revisar el esquema: IF NOT EXISTS no
migra tablas ya creadas. Las reglas de negocio de reportes se implementaran
en una etapa posterior.
