-- LimpiaHuancayo - Seguridad y permisos de rutinas de usuarios v1
-- Requiere 01_esquema.sql, 02_datos_iniciales.sql y 03_usuarios_rutinas.sql.
-- Ejecutar como propietario de las rutinas.
-- Si se vuelve a ejecutar 03, ejecutar este script nuevamente.

BEGIN;

-- Funciones de lectura de usuarios
ALTER FUNCTION public.fn_usuario_obtener_por_email(TEXT)
    SECURITY DEFINER;
ALTER FUNCTION public.fn_usuario_obtener_por_email(TEXT)
    SET search_path = pg_catalog, pg_temp;

ALTER FUNCTION public.fn_usuario_obtener_por_id(BIGINT)
    SECURITY DEFINER;
ALTER FUNCTION public.fn_usuario_obtener_por_id(BIGINT)
    SET search_path = pg_catalog, pg_temp;

ALTER FUNCTION public.fn_usuario_listar(TEXT, BIGINT, BOOLEAN, INTEGER, INTEGER)
    SECURITY DEFINER;
ALTER FUNCTION public.fn_usuario_listar(TEXT, BIGINT, BOOLEAN, INTEGER, INTEGER)
    SET search_path = pg_catalog, pg_temp;

-- Procedimientos de escritura de usuarios
ALTER PROCEDURE public.sp_usuario_registrar(VARCHAR, VARCHAR, TEXT, BIGINT)
    SECURITY DEFINER;
ALTER PROCEDURE public.sp_usuario_registrar(VARCHAR, VARCHAR, TEXT, BIGINT)
    SET search_path = pg_catalog, pg_temp;

ALTER PROCEDURE public.sp_usuario_actualizar_perfil(BIGINT, VARCHAR)
    SECURITY DEFINER;
ALTER PROCEDURE public.sp_usuario_actualizar_perfil(BIGINT, VARCHAR)
    SET search_path = pg_catalog, pg_temp;

ALTER PROCEDURE public.sp_usuario_cambiar_estado(BIGINT, BOOLEAN)
    SECURITY DEFINER;
ALTER PROCEDURE public.sp_usuario_cambiar_estado(BIGINT, BOOLEAN)
    SET search_path = pg_catalog, pg_temp;

-- Quitar acceso publico y conceder solo al rol de aplicacion
REVOKE ALL ON FUNCTION public.fn_usuario_obtener_por_email(TEXT) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.fn_usuario_obtener_por_id(BIGINT) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.fn_usuario_listar(TEXT, BIGINT, BOOLEAN, INTEGER, INTEGER) FROM PUBLIC;
REVOKE ALL ON PROCEDURE public.sp_usuario_registrar(VARCHAR, VARCHAR, TEXT, BIGINT) FROM PUBLIC;
REVOKE ALL ON PROCEDURE public.sp_usuario_actualizar_perfil(BIGINT, VARCHAR) FROM PUBLIC;
REVOKE ALL ON PROCEDURE public.sp_usuario_cambiar_estado(BIGINT, BOOLEAN) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION public.fn_usuario_obtener_por_email(TEXT) TO limpiahuancayo_app;
GRANT EXECUTE ON FUNCTION public.fn_usuario_obtener_por_id(BIGINT) TO limpiahuancayo_app;
GRANT EXECUTE ON FUNCTION public.fn_usuario_listar(TEXT, BIGINT, BOOLEAN, INTEGER, INTEGER) TO limpiahuancayo_app;
GRANT EXECUTE ON PROCEDURE public.sp_usuario_registrar(VARCHAR, VARCHAR, TEXT, BIGINT) TO limpiahuancayo_app;
GRANT EXECUTE ON PROCEDURE public.sp_usuario_actualizar_perfil(BIGINT, VARCHAR) TO limpiahuancayo_app;
GRANT EXECUTE ON PROCEDURE public.sp_usuario_cambiar_estado(BIGINT, BOOLEAN) TO limpiahuancayo_app;

COMMIT;
