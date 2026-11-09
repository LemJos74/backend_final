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

04 aplica SECURITY DEFINER, search_path y permisos EXECUTE al rol de
aplicacion para las rutinas de usuarios. 05 crea las funciones de consulta
de los tres catalogos. Si se vuelve a ejecutar 03, ejecutar 04 otra vez.

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
