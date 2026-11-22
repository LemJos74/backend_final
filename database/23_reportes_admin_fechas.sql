-- Ejecutar como propietario después de 22. Conserva la función de 13.
BEGIN;

CREATE FUNCTION public.fn_reporte_listar_admin_por_fecha(
    p_admin_id BIGINT,
    p_distrito_id BIGINT,
    p_tipo_id BIGINT,
    p_estado_id BIGINT,
    p_limite INTEGER,
    p_desplazamiento INTEGER,
    p_fecha_desde DATE,
    p_fecha_hasta DATE
)
RETURNS TABLE (
    id BIGINT,
    usuario_id BIGINT,
    usuario_nombre VARCHAR(120),
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
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
    v_rol_nombre VARCHAR(30);
    v_desde TIMESTAMPTZ;
    v_hasta_exclusiva TIMESTAMPTZ;
BEGIN
    IF p_admin_id IS NULL OR p_admin_id <= 0 THEN
        RAISE EXCEPTION 'El usuario es obligatorio' USING ERRCODE = '22023';
    END IF;

    SELECT ro.nombre
      INTO v_rol_nombre
      FROM public.usuarios AS u
      JOIN public.roles AS ro ON ro.id = u.rol_id
     WHERE u.id = p_admin_id
       AND u.activo = TRUE;

    IF v_rol_nombre IS DISTINCT FROM 'Administrador' THEN
        RAISE EXCEPTION 'Usuario no autorizado para consultar reportes'
            USING ERRCODE = '42501';
    END IF;

    IF p_limite IS NULL OR p_limite < 1 OR p_limite > 100
       OR p_desplazamiento IS NULL OR p_desplazamiento < 0 THEN
        RAISE EXCEPTION 'Paginación inválida' USING ERRCODE = '22023';
    END IF;

    IF (p_distrito_id IS NOT NULL AND p_distrito_id <= 0)
       OR (p_tipo_id IS NOT NULL AND p_tipo_id <= 0)
       OR (p_estado_id IS NOT NULL AND p_estado_id <= 0) THEN
        RAISE EXCEPTION 'Parámetros de consulta inválidos'
            USING ERRCODE = '22023';
    END IF;

    IF p_fecha_desde NOT BETWEEN DATE '0001-01-01' AND DATE '9999-12-31'
       OR p_fecha_hasta NOT BETWEEN DATE '0001-01-01' AND DATE '9999-12-31'
       OR p_fecha_desde > p_fecha_hasta THEN
        RAISE EXCEPTION 'Rango de fechas inválido' USING ERRCODE = '22023';
    END IF;

    v_desde := p_fecha_desde::timestamp AT TIME ZONE 'America/Lima';
    v_hasta_exclusiva := (p_fecha_hasta + 1)::timestamp AT TIME ZONE 'America/Lima';

    RETURN QUERY
    SELECT
        r.id,
        r.usuario_id,
        u.nombre,
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
        r.created_at,
        r.updated_at
    FROM public.reportes AS r
    JOIN public.usuarios AS u ON u.id = r.usuario_id
    JOIN public.tipos_reporte AS t ON t.id = r.tipo_id
    JOIN public.distritos AS d ON d.id = r.distrito_id
    JOIN public.estados_reporte AS e ON e.id = r.estado_id
    WHERE (p_distrito_id IS NULL OR r.distrito_id = p_distrito_id)
      AND (p_tipo_id IS NULL OR r.tipo_id = p_tipo_id)
      AND (p_estado_id IS NULL OR r.estado_id = p_estado_id)
      AND (v_desde IS NULL OR r.created_at >= v_desde)
      AND (v_hasta_exclusiva IS NULL OR r.created_at < v_hasta_exclusiva)
    ORDER BY r.created_at DESC, r.id DESC
    LIMIT p_limite OFFSET p_desplazamiento;
END;
$$;

REVOKE ALL ON FUNCTION public.fn_reporte_listar_admin_por_fecha(
    BIGINT, BIGINT, BIGINT, BIGINT, INTEGER, INTEGER, DATE, DATE
) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION public.fn_reporte_listar_admin_por_fecha(
    BIGINT, BIGINT, BIGINT, BIGINT, INTEGER, INTEGER, DATE, DATE
) TO limpiahuancayo_app;

COMMIT;
