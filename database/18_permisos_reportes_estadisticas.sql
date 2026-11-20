-- LimpiaHuancayo - Seguridad y permisos de estadisticas administrativas v1
-- Requiere 01_esquema.sql, 02_datos_iniciales.sql y 17_reportes_estadisticas.sql.
-- Ejecutar como propietario de las rutinas.
--
-- 17 ya crea la funcion con SECURITY DEFINER, search_path seguro y permisos
-- restringidos dentro de su propia transaccion. Este script vuelve a aplicar
-- esas propiedades de forma idempotente y sirve como verificacion y
-- endurecimiento posterior.
BEGIN;

ALTER FUNCTION public.fn_reporte_estadisticas_admin(
    BIGINT
)
    SECURITY DEFINER;

ALTER FUNCTION public.fn_reporte_estadisticas_admin(
    BIGINT
)
    SET search_path = pg_catalog, pg_temp;

REVOKE ALL ON FUNCTION public.fn_reporte_estadisticas_admin(
    BIGINT
) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION public.fn_reporte_estadisticas_admin(
    BIGINT
) TO limpiahuancayo_app;

COMMIT;
