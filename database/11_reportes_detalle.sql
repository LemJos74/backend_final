-- LimpiaHuancayo - Detalle individual de reportes v1
-- Requiere 01_esquema.sql y 02_datos_iniciales.sql.
-- Ejecutar como propietario de las tablas y rutinas, después de 10.
--
-- La funcion resuelve el rol actual desde public.usuarios y public.roles.
-- Un Ciudadano activo solo obtiene sus propios reportes; un Administrador
-- activo puede obtener cualquiera. Un usuario inexistente, inactivo o con
-- un rol no autorizado no obtiene filas.
--
-- No crea tablas ni indices. No modifica los scripts 01 a 10.
BEGIN;

CREATE OR REPLACE FUNCTION public.fn_reporte_obtener(
    p_reporte_id BIGINT,
    p_usuario_id BIGINT
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
    imagen_path TEXT,
    observacion_admin TEXT,
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
    IF p_reporte_id IS NULL OR p_reporte_id <= 0
       OR p_usuario_id IS NULL OR p_usuario_id <= 0 THEN
        RAISE EXCEPTION 'Parámetros de consulta inválidos'
            USING ERRCODE = '22023';
    END IF;

    -- El rol no se recibe desde el cliente: se resuelve con el usuario
    -- autenticado que FastAPI obtiene del token y recarga desde PostgreSQL.
    SELECT ro.nombre
      INTO v_rol_nombre
      FROM public.usuarios AS u
      JOIN public.roles AS ro ON ro.id = u.rol_id
     WHERE u.id = p_usuario_id
       AND u.activo = TRUE;

    IF v_rol_nombre IS NULL
       OR v_rol_nombre NOT IN ('Ciudadano', 'Administrador') THEN
        RETURN;
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
        r.imagen_path,
        r.observacion_admin,
        r.created_at,
        r.updated_at
    FROM public.reportes AS r
    JOIN public.tipos_reporte AS t ON t.id = r.tipo_id
    JOIN public.distritos AS d ON d.id = r.distrito_id
    JOIN public.estados_reporte AS e ON e.id = r.estado_id
    WHERE r.id = p_reporte_id
      AND (
          v_rol_nombre = 'Administrador'
          OR r.usuario_id = p_usuario_id
      )
    LIMIT 1;
END;
$$;

-- La funcion se crea ya asegurada dentro de la misma transaccion:
-- no queda ejecutable por PUBLIC entre 11 y 12.
REVOKE ALL ON FUNCTION public.fn_reporte_obtener(
    BIGINT, BIGINT
) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION public.fn_reporte_obtener(
    BIGINT, BIGINT
) TO limpiahuancayo_app;

COMMIT;
