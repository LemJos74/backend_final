-- LimpiaHuancayo - Consulta de reportes del ciudadano v1
-- Requiere 01_esquema.sql y 02_datos_iniciales.sql.
-- Ejecutar como propietario de las tablas y rutinas, después de 08.
--
-- La funcion devuelve exclusivamente los reportes del usuario recibido.
-- La autorizacion del usuario se resuelve en FastAPI; esta funcion solo
-- aplica el filtro por usuario_id y la paginacion.
--
-- No crea tablas ni indices. No modifica los scripts 01 a 08.
BEGIN;

CREATE OR REPLACE FUNCTION public.fn_reporte_listar_mios(
    p_usuario_id BIGINT,
    p_limite INTEGER DEFAULT 20,
    p_desplazamiento INTEGER DEFAULT 0
)
RETURNS TABLE (
    id BIGINT,
    tipo_id BIGINT,
    tipo_nombre VARCHAR(100),
    distrito_id BIGINT,
    distrito_nombre VARCHAR(80),
    estado_id BIGINT,
    estado_nombre VARCHAR(30),
    descripcion TEXT,
    ubicacion VARCHAR(250),
    latitud NUMERIC(10,8),
    longitud NUMERIC(11,8),
    created_at TIMESTAMPTZ
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
BEGIN
    IF p_usuario_id IS NULL OR p_usuario_id <= 0 THEN
        RAISE EXCEPTION 'El usuario es obligatorio'
            USING ERRCODE = '22023';
    END IF;

    IF p_limite IS NULL OR p_limite < 1 OR p_limite > 100
       OR p_desplazamiento IS NULL OR p_desplazamiento < 0 THEN
        RAISE EXCEPTION 'Paginación inválida'
            USING ERRCODE = '22023';
    END IF;

    RETURN QUERY
    SELECT
        r.id,
        r.tipo_id,
        t.nombre,
        r.distrito_id,
        d.nombre,
        r.estado_id,
        e.nombre,
        r.descripcion,
        r.ubicacion,
        r.latitud,
        r.longitud,
        r.created_at
    FROM public.reportes AS r
    JOIN public.tipos_reporte AS t ON t.id = r.tipo_id
    JOIN public.distritos AS d ON d.id = r.distrito_id
    JOIN public.estados_reporte AS e ON e.id = r.estado_id
    WHERE r.usuario_id = p_usuario_id
    ORDER BY r.created_at DESC, r.id DESC
    LIMIT p_limite OFFSET p_desplazamiento;
END;
$$;

-- La funcion se crea ya asegurada dentro de la misma transaccion:
-- no queda ejecutable por PUBLIC entre 09 y 10.
REVOKE ALL ON FUNCTION public.fn_reporte_listar_mios(
    BIGINT, INTEGER, INTEGER
) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION public.fn_reporte_listar_mios(
    BIGINT, INTEGER, INTEGER
) TO limpiahuancayo_app;

COMMIT;
