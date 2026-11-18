-- LimpiaHuancayo - Cambio de estado de reportes v1
-- Requiere 01_esquema.sql y 02_datos_iniciales.sql.
-- Ejecutar como propietario de las tablas y rutinas, después de 14.
--
-- Solo un Administrador activo puede cambiar el estado de un reporte. El rol
-- se resuelve en la base de datos con el identificador autenticado que FastAPI
-- obtiene del token: nunca se recibe un rol desde el cliente.
--
-- Transiciones permitidas:
--   Pendiente   -> En atención
--   Pendiente   -> Rechazado
--   En atención -> Resuelto
--   En atención -> Rechazado
-- Resuelto y Rechazado son estados finales: no admiten nuevas transiciones.
--
-- La justificación es obligatoria al rechazar y opcional en el resto de
-- cambios. Si se envía, sobrescribe observacion_admin; si no se envía, se
-- conserva el valor anterior.
--
-- Los cuatro parámetros OUT se devuelven como fila del CALL. PostgreSQL exige
-- suministrar argumentos para los OUT en la llamada (se pasan como NULL y no
-- se evalúan), aunque la firma de GRANT/REVOKE/ALTER solo incluye los IN.
--
-- No crea tablas, columnas ni indices. No modifica los scripts 01 a 14.
BEGIN;

CREATE OR REPLACE PROCEDURE public.sp_reporte_cambiar_estado(
    IN  p_admin_id BIGINT,
    IN  p_reporte_id BIGINT,
    IN  p_nuevo_estado_id BIGINT,
    IN  p_justificacion TEXT,
    OUT p_estado_id BIGINT,
    OUT p_estado_nombre VARCHAR(30),
    OUT p_observacion_admin TEXT,
    OUT p_updated_at TIMESTAMPTZ
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
    v_rol_nombre VARCHAR(30);
    v_estado_actual VARCHAR(30);
    v_estado_nuevo VARCHAR(30);
    v_justificacion TEXT;
BEGIN
    -- 1. Parámetros obligatorios.
    IF p_admin_id IS NULL OR p_admin_id <= 0 THEN
        RAISE EXCEPTION 'El usuario es obligatorio'
            USING ERRCODE = '22023';
    END IF;

    IF p_reporte_id IS NULL OR p_reporte_id <= 0 THEN
        RAISE EXCEPTION 'El reporte es obligatorio'
            USING ERRCODE = '22023';
    END IF;

    IF p_nuevo_estado_id IS NULL OR p_nuevo_estado_id <= 0 THEN
        RAISE EXCEPTION 'El estado es obligatorio'
            USING ERRCODE = '22023';
    END IF;

    -- 2. Identidad autenticada: usuario existente, activo y Administrador.
    SELECT ro.nombre
      INTO v_rol_nombre
      FROM public.usuarios AS u
      JOIN public.roles AS ro ON ro.id = u.rol_id
     WHERE u.id = p_admin_id
       AND u.activo = TRUE;

    IF v_rol_nombre IS DISTINCT FROM 'Administrador' THEN
        RAISE EXCEPTION 'Usuario no autorizado para cambiar el estado'
            USING ERRCODE = '42501';
    END IF;

    -- 3. Justificación: recortada, opcional y con máximo de 2000 caracteres.
    v_justificacion := NULLIF(btrim(p_justificacion), '');

    IF v_justificacion IS NOT NULL
       AND char_length(v_justificacion) > 2000 THEN
        RAISE EXCEPTION 'La justificación no puede superar los 2000 caracteres'
            USING ERRCODE = '22023';
    END IF;

    -- 4. El estado destino debe existir.
    SELECT e.nombre
      INTO v_estado_nuevo
      FROM public.estados_reporte AS e
     WHERE e.id = p_nuevo_estado_id;

    IF v_estado_nuevo IS NULL THEN
        RAISE EXCEPTION 'El estado de reporte no existe'
            USING ERRCODE = '22023';
    END IF;

    -- 5. Rechazar exige justificación.
    IF v_estado_nuevo = 'Rechazado' AND v_justificacion IS NULL THEN
        RAISE EXCEPTION 'La justificación es obligatoria al rechazar un reporte'
            USING ERRCODE = '23502';
    END IF;

    -- 6. Estado actual con bloqueo de fila: dos administradores concurrentes
    --    no pueden validar la misma transición al mismo tiempo.
    SELECT e.nombre
      INTO v_estado_actual
      FROM public.reportes AS r
      JOIN public.estados_reporte AS e ON e.id = r.estado_id
     WHERE r.id = p_reporte_id
       FOR UPDATE OF r;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Reporte no encontrado'
            USING ERRCODE = 'P0002';
    END IF;

    -- 7. Tabla explícita de transiciones permitidas. Resuelto y Rechazado son
    --    finales: no figuran como origen, así que cualquier salida desde ellos
    --    falla aquí.
    IF NOT EXISTS (
        SELECT 1
          FROM (VALUES
                    ('Pendiente',   'En atención'),
                    ('Pendiente',   'Rechazado'),
                    ('En atención', 'Resuelto'),
                    ('En atención', 'Rechazado')
               ) AS t(origen, destino)
         WHERE t.origen = v_estado_actual
           AND t.destino = v_estado_nuevo
    ) THEN
        RAISE EXCEPTION 'Transición de estado no permitida'
            USING ERRCODE = '55000';
    END IF;

    -- 8. Actualización del estado, la observación administrativa y updated_at.
    UPDATE public.reportes
       SET estado_id = p_nuevo_estado_id,
           observacion_admin = COALESCE(v_justificacion, observacion_admin),
           updated_at = now()
     WHERE id = p_reporte_id
    RETURNING estado_id, observacion_admin, updated_at
         INTO p_estado_id, p_observacion_admin, p_updated_at;

    p_estado_nombre := v_estado_nuevo;
END;
$$;

-- La firma de seguridad incluye solo los parámetros IN: los OUT no forman
-- parte de los argumentos de identidad de la rutina.
-- El procedimiento se crea ya asegurado dentro de la misma transacción:
-- no queda ejecutable por PUBLIC entre 15 y 16.
REVOKE ALL ON PROCEDURE public.sp_reporte_cambiar_estado(
    BIGINT, BIGINT, BIGINT, TEXT
) FROM PUBLIC;

GRANT EXECUTE ON PROCEDURE public.sp_reporte_cambiar_estado(
    BIGINT, BIGINT, BIGINT, TEXT
) TO limpiahuancayo_app;

COMMIT;
