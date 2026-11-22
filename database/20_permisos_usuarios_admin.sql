-- LimpiaHuancayo - Seguridad y permisos de administración de usuarios v1
-- Requiere 01_esquema.sql, 02_datos_iniciales.sql, 03_usuarios_rutinas.sql,
-- 04_permisos_usuarios.sql y 19_usuarios_admin.sql.
-- Ejecutar como propietario de las rutinas.
--
-- 19 ya crea las rutinas con SECURITY DEFINER, search_path seguro y permisos
-- restringidos dentro de su propia transacción. Este script vuelve a aplicar
-- esas propiedades de forma idempotente y sirve como verificación y
-- endurecimiento posterior.
--
-- ALTER/REVOKE/GRANT del procedimiento usan solo la firma de los parámetros
-- IN. Los parámetros OUT no forman parte de la identidad de la rutina, aunque
-- el CALL sí deba recibirlos como NULL.
BEGIN;

ALTER FUNCTION public.fn_usuario_listar_admin(
    BIGINT, TEXT, VARCHAR, BOOLEAN, INTEGER, INTEGER
)
    SECURITY DEFINER;

ALTER FUNCTION public.fn_usuario_listar_admin(
    BIGINT, TEXT, VARCHAR, BOOLEAN, INTEGER, INTEGER
)
    SET search_path = pg_catalog, pg_temp;

REVOKE ALL ON FUNCTION public.fn_usuario_listar_admin(
    BIGINT, TEXT, VARCHAR, BOOLEAN, INTEGER, INTEGER
) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION public.fn_usuario_listar_admin(
    BIGINT, TEXT, VARCHAR, BOOLEAN, INTEGER, INTEGER
) TO limpiahuancayo_app;

ALTER PROCEDURE public.sp_usuario_cambiar_estado_admin(
    BIGINT, BIGINT, BOOLEAN
)
    SECURITY DEFINER;

ALTER PROCEDURE public.sp_usuario_cambiar_estado_admin(
    BIGINT, BIGINT, BOOLEAN
)
    SET search_path = pg_catalog, pg_temp;

REVOKE ALL ON PROCEDURE public.sp_usuario_cambiar_estado_admin(
    BIGINT, BIGINT, BOOLEAN
) FROM PUBLIC;

GRANT EXECUTE ON PROCEDURE public.sp_usuario_cambiar_estado_admin(
    BIGINT, BIGINT, BOOLEAN
) TO limpiahuancayo_app;

-- La revocación aprobada de las rutinas antiguas se ejecuta en
-- 21_revocar_rutinas_usuarios_antiguas.sql. No se incluye aquí para evitar
-- duplicar la operación y para que la verificación de permisos efectivos
-- quede en un único script.

COMMIT;
