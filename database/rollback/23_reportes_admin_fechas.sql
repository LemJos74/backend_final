-- Revertir primero la aplicación a la versión que llama a la función de 13.
BEGIN;

DROP FUNCTION public.fn_reporte_listar_admin_por_fecha(
    BIGINT, BIGINT, BIGINT, BIGINT, INTEGER, INTEGER, DATE, DATE
) RESTRICT;

COMMIT;
