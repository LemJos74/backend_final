-- LimpiaHuancayo - Seguridad y permisos de rutinas de reportes v1
-- Requiere 01_esquema.sql, 02_datos_iniciales.sql y 07_reportes_rutinas.sql.
-- Ejecutar como propietario de las rutinas.
--
-- 07 ya crea el procedimiento con SECURITY DEFINER, search_path seguro y
-- permisos restringidos dentro de su propia transaccion. Este script vuelve
-- a aplicar esas propiedades de forma idempotente y sirve como verificacion
-- y endurecimiento posterior.
BEGIN;

ALTER PROCEDURE public.sp_reporte_registrar(
    BIGINT, BIGINT, BIGINT, TEXT, VARCHAR, NUMERIC, NUMERIC, BIGINT
)
    SECURITY DEFINER;

ALTER PROCEDURE public.sp_reporte_registrar(
    BIGINT, BIGINT, BIGINT, TEXT, VARCHAR, NUMERIC, NUMERIC, BIGINT
)
    SET search_path = pg_catalog, pg_temp;

REVOKE ALL ON PROCEDURE public.sp_reporte_registrar(
    BIGINT, BIGINT, BIGINT, TEXT, VARCHAR, NUMERIC, NUMERIC, BIGINT
) FROM PUBLIC;

GRANT EXECUTE ON PROCEDURE public.sp_reporte_registrar(
    BIGINT, BIGINT, BIGINT, TEXT, VARCHAR, NUMERIC, NUMERIC, BIGINT
) TO limpiahuancayo_app;

COMMIT;
