-- LimpiaHuancayo - Rutinas de reportes v1
-- Requiere 01_esquema.sql y 02_datos_iniciales.sql.
-- Ejecutar como propietario de las tablas y rutinas.
--
-- Esta primera fase solo implementa el registro de reportes ciudadanos.
-- No hay funciones de listado, detalle ni cambio de estado en este script.
--
-- El procedimiento inserta siempre:
--   * estado_id = id de 'Pendiente';
--   * imagen_path = NULL;
--   * observacion_admin = NULL.
--
-- No existe deduplicacion de solicitudes: cada llamada valida crea un
-- reporte nuevo. Un reintento del cliente puede crear otro reporte.
BEGIN;

CREATE OR REPLACE PROCEDURE public.sp_reporte_registrar(
    IN p_usuario_id BIGINT,
    IN p_distrito_id BIGINT,
    IN p_tipo_id BIGINT,
    IN p_descripcion TEXT,
    IN p_ubicacion VARCHAR,
    IN p_latitud NUMERIC,
    IN p_longitud NUMERIC,
    INOUT p_reporte_id BIGINT DEFAULT NULL
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
    v_rol_nombre VARCHAR(30);
    v_estado_id BIGINT;
BEGIN
    -- 1. El usuario debe existir, estar activo y ser Ciudadano.
    IF p_usuario_id IS NULL OR p_usuario_id <= 0 THEN
        RAISE EXCEPTION 'El usuario es obligatorio'
            USING ERRCODE = '22023';
    END IF;

    SELECT r.nombre
      INTO v_rol_nombre
      FROM public.usuarios AS u
      JOIN public.roles AS r ON r.id = u.rol_id
     WHERE u.id = p_usuario_id
       AND u.activo = TRUE;

    IF v_rol_nombre IS DISTINCT FROM 'Ciudadano' THEN
        RAISE EXCEPTION 'Usuario no autorizado para registrar reportes'
            USING ERRCODE = '42501';
    END IF;

    -- 2. El distrito debe existir.
    IF p_distrito_id IS NULL OR p_distrito_id <= 0 THEN
        RAISE EXCEPTION 'El distrito es obligatorio'
            USING ERRCODE = '22023';
    END IF;

    IF NOT EXISTS (
        SELECT 1
          FROM public.distritos AS d
         WHERE d.id = p_distrito_id
    ) THEN
        RAISE EXCEPTION 'El distrito no existe'
            USING ERRCODE = '23503';
    END IF;

    -- 3. El tipo de reporte debe existir.
    IF p_tipo_id IS NULL OR p_tipo_id <= 0 THEN
        RAISE EXCEPTION 'El tipo de reporte es obligatorio'
            USING ERRCODE = '22023';
    END IF;

    IF NOT EXISTS (
        SELECT 1
          FROM public.tipos_reporte AS t
         WHERE t.id = p_tipo_id
    ) THEN
        RAISE EXCEPTION 'El tipo de reporte no existe'
            USING ERRCODE = '23503';
    END IF;

    -- 4. Descripcion: obligatoria, recortada y con maximo de 2000 caracteres.
    IF p_descripcion IS NULL OR btrim(p_descripcion) = '' THEN
        RAISE EXCEPTION 'La descripción es obligatoria'
            USING ERRCODE = '22023';
    END IF;

    IF char_length(btrim(p_descripcion)) > 2000 THEN
        RAISE EXCEPTION 'La descripción no puede superar los 2000 caracteres'
            USING ERRCODE = '22023';
    END IF;

    -- 5. Ubicacion: obligatoria, recortada y con maximo de 250 caracteres.
    IF p_ubicacion IS NULL OR btrim(p_ubicacion) = '' THEN
        RAISE EXCEPTION 'La ubicación es obligatoria'
            USING ERRCODE = '22023';
    END IF;

    IF char_length(btrim(p_ubicacion)) > 250 THEN
        RAISE EXCEPTION 'La ubicación no puede superar los 250 caracteres'
            USING ERRCODE = '22023';
    END IF;

    -- 6. Coordenadas: obligatorias, finitas, dentro de rango y con maximo
    --    de 8 decimales. No se permite que PostgreSQL redondee en silencio.
    IF p_latitud IS NULL OR p_longitud IS NULL THEN
        RAISE EXCEPTION 'La latitud y la longitud son obligatorias'
            USING ERRCODE = '22023';
    END IF;

    IF p_latitud::text IN ('NaN', 'Infinity', '-Infinity')
       OR p_longitud::text IN ('NaN', 'Infinity', '-Infinity') THEN
        RAISE EXCEPTION 'Las coordenadas deben ser finitas'
            USING ERRCODE = '22023';
    END IF;

    IF p_latitud < -90 OR p_latitud > 90 THEN
        RAISE EXCEPTION 'La latitud debe estar entre -90 y 90'
            USING ERRCODE = '22023';
    END IF;

    IF p_longitud < -180 OR p_longitud > 180 THEN
        RAISE EXCEPTION 'La longitud debe estar entre -180 y 180'
            USING ERRCODE = '22023';
    END IF;

    IF scale(p_latitud) > 8 OR scale(p_longitud) > 8 THEN
        RAISE EXCEPTION 'Las coordenadas admiten como máximo 8 decimales'
            USING ERRCODE = '22023';
    END IF;

    -- 7. El estado inicial siempre es Pendiente.
    SELECT e.id
      INTO v_estado_id
      FROM public.estados_reporte AS e
     WHERE e.nombre = 'Pendiente';

    IF v_estado_id IS NULL THEN
        RAISE EXCEPTION 'No existe el estado Pendiente'
            USING ERRCODE = 'P0002';
    END IF;

    -- 8. Inserción del reporte. No se aceptan imagen ni observacion admin.
    INSERT INTO public.reportes (
        usuario_id,
        distrito_id,
        tipo_id,
        estado_id,
        descripcion,
        ubicacion,
        latitud,
        longitud,
        imagen_path,
        observacion_admin
    )
    VALUES (
        p_usuario_id,
        p_distrito_id,
        p_tipo_id,
        v_estado_id,
        btrim(p_descripcion),
        btrim(p_ubicacion),
        p_latitud,
        p_longitud,
        NULL,
        NULL
    )
    RETURNING id INTO p_reporte_id;
END;
$$;

-- El procedimiento se crea ya asegurado dentro de la misma transaccion:
-- no queda ejecutable por PUBLIC entre 07 y 08.
REVOKE ALL ON PROCEDURE public.sp_reporte_registrar(
    BIGINT, BIGINT, BIGINT, TEXT, VARCHAR, NUMERIC, NUMERIC, BIGINT
) FROM PUBLIC;

GRANT EXECUTE ON PROCEDURE public.sp_reporte_registrar(
    BIGINT, BIGINT, BIGINT, TEXT, VARCHAR, NUMERIC, NUMERIC, BIGINT
) TO limpiahuancayo_app;

COMMIT;
