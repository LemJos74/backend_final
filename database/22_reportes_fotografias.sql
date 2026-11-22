-- Ejecutar como propietario de las rutinas, después de 21.
BEGIN;

CREATE PROCEDURE public.sp_reporte_registrar_con_fotografia(
    IN p_usuario_id BIGINT,
    IN p_distrito_id BIGINT,
    IN p_tipo_id BIGINT,
    IN p_descripcion TEXT,
    IN p_ubicacion VARCHAR,
    IN p_latitud NUMERIC,
    IN p_longitud NUMERIC,
    IN p_imagen_path TEXT,
    INOUT p_reporte_id BIGINT
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
BEGIN
    IF p_imagen_path IS NULL
       OR p_imagen_path COLLATE "C" !~ '^[0-9a-f]{32}[.]jpg$' THEN
        RAISE EXCEPTION 'La clave de la fotografía no es válida'
            USING ERRCODE = '22023';
    END IF;

    p_reporte_id := NULL;
    CALL public.sp_reporte_registrar(
        p_usuario_id, p_distrito_id, p_tipo_id, p_descripcion,
        p_ubicacion, p_latitud, p_longitud, p_reporte_id
    );

    UPDATE public.reportes
    SET imagen_path = p_imagen_path
    WHERE id = p_reporte_id
      AND usuario_id = p_usuario_id
      AND imagen_path IS NULL;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'No se pudo asociar la fotografía al reporte'
            USING ERRCODE = 'P0002';
    END IF;
END;
$$;

REVOKE ALL ON PROCEDURE public.sp_reporte_registrar_con_fotografia(
    BIGINT, BIGINT, BIGINT, TEXT, VARCHAR, NUMERIC, NUMERIC, TEXT, BIGINT
) FROM PUBLIC;

GRANT EXECUTE ON PROCEDURE public.sp_reporte_registrar_con_fotografia(
    BIGINT, BIGINT, BIGINT, TEXT, VARCHAR, NUMERIC, NUMERIC, TEXT, BIGINT
) TO limpiahuancayo_app;

COMMIT;
