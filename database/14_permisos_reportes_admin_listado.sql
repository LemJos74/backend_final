-- LimpiaHuancayo - Seguridad y permisos del listado administrativo v1
-- Requiere 01_esquema.sql, 02_datos_iniciales.sql y 13_reportes_admin_listado.sql.
-- Ejecutar como propietario de las rutinas.
--
-- 13 ya crea la funcion con SECURITY DEFINER, search_path seguro y permisos
-- restringidos dentro de su propia transaccion. Este script vuelve a aplicar
-- esas propiedades de forma idempotente y sirve como verificacion y
-- endurecimiento posterior.
BEGIN;

ALTER FUNCTION public.fn_reporte_listar_admin(
    BIGINT, BIGINT, BIGINT, BIGINT, INTEGER, INTEGER
)
    SECURITY DEFINER;

ALTER FUNCTION public.fn_reporte_listar_admin(
    BIGINT, BIGINT, BIGINT, BIGINT, INTEGER, INTEGER
)
    SET search_path = pg_catalog, pg_temp;

REVOKE ALL ON FUNCTION public.fn_reporte_listar_admin(
    BIGINT, BIGINT, BIGINT, BIGINT, INTEGER, INTEGER
) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION public.fn_reporte_listar_admin(
    BIGINT, BIGINT, BIGINT, BIGINT, INTEGER, INTEGER
) TO limpiahuancayo_app;

COMMIT;
