-- LimpiaHuancayo - Listado administrativo de reportes v1
-- Requiere 01_esquema.sql y 02_datos_iniciales.sql.
-- Ejecutar como propietario de las tablas y rutinas, después de 12.
--
-- La funcion devuelve los reportes de todos los ciudadanos. El rol no se
-- recibe desde el cliente: se resuelve en public.usuarios y public.roles con
-- el identificador del usuario autenticado que FastAPI obtiene del token.
-- Si el usuario no existe, esta inactivo o no es Administrador, la llamada
-- falla con SQLSTATE 42501 y no devuelve filas.
--
-- Los filtros por distrito, tipo y estado son opcionales: cuando llegan NULL
-- no restringen la consulta. La paginacion replica fn_reporte_listar_mios.
--
-- No crea tablas, columnas ni indices. No modifica los scripts 01 a 12.
BEGIN;

CREATE OR REPLACE FUNCTION public.fn_reporte_listar_admin(
    p_admin_id BIGINT,
    p_distrito_id BIGINT DEFAULT NULL,
    p_tipo_id BIGINT DEFAULT NULL,
    p_estado_id BIGINT DEFAULT NULL,
    p_limite INTEGER DEFAULT 20,
    p_desplazamiento INTEGER DEFAULT 0
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
BEGIN
    -- 1. Identidad autenticada: usuario existente, activo y Administrador.
    IF p_admin_id IS NULL OR p_admin_id <= 0 THEN
        RAISE EXCEPTION 'El usuario es obligatorio'
            USING ERRCODE = '22023';
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

    -- 2. Paginacion: obligatoria, acotada y con desplazamiento no negativo.
    IF p_limite IS NULL OR p_limite < 1 OR p_limite > 100
       OR p_desplazamiento IS NULL OR p_desplazamiento < 0 THEN
        RAISE EXCEPTION 'Paginación inválida'
            USING ERRCODE = '22023';
    END IF;

    -- 3. Filtros opcionales: si se envian, deben ser identificadores validos.
    IF (p_distrito_id IS NOT NULL AND p_distrito_id <= 0)
       OR (p_tipo_id IS NOT NULL AND p_tipo_id <= 0)
       OR (p_estado_id IS NOT NULL AND p_estado_id <= 0) THEN
        RAISE EXCEPTION 'Parámetros de consulta inválidos'
            USING ERRCODE = '22023';
    END IF;

    -- 4. Listado sin filtro por usuario: el Administrador ve todos los
    --    reportes. El desempate por id mantiene la paginacion determinista.
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
    ORDER BY r.created_at DESC, r.id DESC
    LIMIT p_limite OFFSET p_desplazamiento;
END;
$$;

-- La funcion se crea ya asegurada dentro de la misma transaccion:
-- no queda ejecutable por PUBLIC entre 13 y 14.
REVOKE ALL ON FUNCTION public.fn_reporte_listar_admin(
    BIGINT, BIGINT, BIGINT, BIGINT, INTEGER, INTEGER
) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION public.fn_reporte_listar_admin(
    BIGINT, BIGINT, BIGINT, BIGINT, INTEGER, INTEGER
) TO limpiahuancayo_app;

COMMIT;
