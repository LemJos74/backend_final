
-- =====================================================
-- LIMPIAHUANCAYO
-- 05_catalogos_consulta.sql
-- Consultas de catálogos mediante funciones almacenadas
-- =====================================================

BEGIN;

-- =====================================================
-- 1. LISTAR DISTRITOS
-- =====================================================

CREATE OR REPLACE FUNCTION public.fn_distrito_listar()
RETURNS TABLE (
    id BIGINT,
    nombre VARCHAR(80)
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
    SELECT d.id, d.nombre
    FROM public.distritos AS d
    ORDER BY d.nombre;
$$;


-- =====================================================
-- 2. LISTAR TIPOS DE REPORTE
-- =====================================================

CREATE OR REPLACE FUNCTION public.fn_tipo_reporte_listar()
RETURNS TABLE (
    id BIGINT,
    nombre VARCHAR(100),
    descripcion VARCHAR(300)
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
    SELECT
        t.id,
        t.nombre,
        t.descripcion
    FROM public.tipos_reporte AS t
    ORDER BY t.id;
$$;


-- =====================================================
-- 3. LISTAR ESTADOS DE REPORTE
-- =====================================================

CREATE OR REPLACE FUNCTION public.fn_estado_reporte_listar()
RETURNS TABLE (
    id BIGINT,
    nombre VARCHAR(30)
)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
    SELECT e.id, e.nombre
    FROM public.estados_reporte AS e
    ORDER BY e.id;
$$;


-- =====================================================
-- 4. CONFIGURAR PERMISOS
-- =====================================================

REVOKE ALL ON FUNCTION public.fn_distrito_listar()
FROM PUBLIC;

REVOKE ALL ON FUNCTION public.fn_tipo_reporte_listar()
FROM PUBLIC;

REVOKE ALL ON FUNCTION public.fn_estado_reporte_listar()
FROM PUBLIC;

GRANT EXECUTE ON FUNCTION public.fn_distrito_listar()
TO limpiahuancayo_app;

GRANT EXECUTE ON FUNCTION public.fn_tipo_reporte_listar()
TO limpiahuancayo_app;

GRANT EXECUTE ON FUNCTION public.fn_estado_reporte_listar()
TO limpiahuancayo_app;

COMMIT;
