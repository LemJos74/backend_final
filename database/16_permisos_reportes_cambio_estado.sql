-- LimpiaHuancayo - Seguridad y permisos del cambio de estado v1
-- Requiere 01_esquema.sql, 02_datos_iniciales.sql y 15_reportes_cambio_estado.sql.
-- Ejecutar como propietario de las rutinas.
--
-- 15 ya crea el procedimiento con SECURITY DEFINER, search_path seguro y
-- permisos restringidos dentro de su propia transaccion. Este script vuelve a
-- aplicar esas propiedades de forma idempotente y sirve como verificacion y
-- endurecimiento posterior.
--
-- ALTER/REVOKE/GRANT usan solo la firma de los parametros IN. Los parametros
-- OUT no forman parte de los argumentos de identidad de la rutina, aunque el
-- CALL si deba recibirlos como NULL.
BEGIN;

ALTER PROCEDURE public.sp_reporte_cambiar_estado(
    BIGINT, BIGINT, BIGINT, TEXT
)
    SECURITY DEFINER;

ALTER PROCEDURE public.sp_reporte_cambiar_estado(
    BIGINT, BIGINT, BIGINT, TEXT
)
    SET search_path = pg_catalog, pg_temp;

REVOKE ALL ON PROCEDURE public.sp_reporte_cambiar_estado(
    BIGINT, BIGINT, BIGINT, TEXT
) FROM PUBLIC;

GRANT EXECUTE ON PROCEDURE public.sp_reporte_cambiar_estado(
    BIGINT, BIGINT, BIGINT, TEXT
) TO limpiahuancayo_app;

COMMIT;
