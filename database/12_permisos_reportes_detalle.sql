-- LimpiaHuancayo - Seguridad y permisos del detalle de reportes v1
-- Requiere 01_esquema.sql, 02_datos_iniciales.sql y 11_reportes_detalle.sql.
-- Ejecutar como propietario de las rutinas.
--
-- 11 ya crea la funcion con SECURITY DEFINER, search_path seguro y permisos
-- restringidos dentro de su propia transaccion. Este script vuelve a aplicar
-- esas propiedades de forma idempotente y sirve como endurecimiento posterior.
BEGIN;

ALTER FUNCTION public.fn_reporte_obtener(
    BIGINT, BIGINT
)
    SECURITY DEFINER;

ALTER FUNCTION public.fn_reporte_obtener(
    BIGINT, BIGINT
)
    SET search_path = pg_catalog, pg_temp;

REVOKE ALL ON FUNCTION public.fn_reporte_obtener(
    BIGINT, BIGINT
) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION public.fn_reporte_obtener(
    BIGINT, BIGINT
) TO limpiahuancayo_app;

COMMIT;
