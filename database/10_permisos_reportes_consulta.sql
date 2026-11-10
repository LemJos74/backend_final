-- LimpiaHuancayo - Seguridad y permisos de consulta de reportes v1
-- Requiere 01_esquema.sql, 02_datos_iniciales.sql y 09_reportes_consulta.sql.
-- Ejecutar como propietario de las rutinas.
--
-- 09 ya crea la funcion con SECURITY DEFINER, search_path seguro y permisos
-- restringidos dentro de su propia transaccion. Este script vuelve a aplicar
-- esas propiedades de forma idempotente y sirve como endurecimiento posterior.
BEGIN;

ALTER FUNCTION public.fn_reporte_listar_mios(
    BIGINT, INTEGER, INTEGER
)
    SECURITY DEFINER;

ALTER FUNCTION public.fn_reporte_listar_mios(
    BIGINT, INTEGER, INTEGER
)
    SET search_path = pg_catalog, pg_temp;

REVOKE ALL ON FUNCTION public.fn_reporte_listar_mios(
    BIGINT, INTEGER, INTEGER
) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION public.fn_reporte_listar_mios(
    BIGINT, INTEGER, INTEGER
) TO limpiahuancayo_app;

COMMIT;
