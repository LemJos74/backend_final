-- LimpiaHuancayo - Administración de usuarios v1
-- Requiere 01_esquema.sql, 02_datos_iniciales.sql, 03_usuarios_rutinas.sql
-- y 04_permisos_usuarios.sql.
-- Ejecutar como propietario de las tablas y rutinas, después de 18.
--
-- Solo un Administrador activo puede listar usuarios y cambiar su estado.
-- El rol se resuelve en la base de datos con el identificador autenticado que
-- FastAPI obtiene del token: nunca se recibe un rol desde el cliente.
--
-- El listado no devuelve contraseñas ni hashes. Los filtros por búsqueda,
-- rol y estado son opcionales. La búsqueda trata % y _ como texto literal.
--
-- El cambio de estado impide la autodesactivación y protege al último
-- administrador activo. Los cambios de estado se serializan con un lock de
-- asesoramiento para evitar que dos administradores se desactiven a la vez.
-- Cambiar al mismo estado es una operación idempotente que no actualiza
-- updated_at. No se elimina ningún usuario ni sus reportes.
--
-- No crea tablas, columnas ni índices. No modifica los scripts 01 a 18.
BEGIN;

CREATE OR REPLACE FUNCTION public.fn_usuario_listar_admin(
    p_admin_id BIGINT,
    p_busqueda TEXT DEFAULT NULL,
    p_rol_nombre VARCHAR DEFAULT NULL,
    p_activo BOOLEAN DEFAULT NULL,
    p_limite INTEGER DEFAULT 20,
    p_desplazamiento INTEGER DEFAULT 0
)
RETURNS TABLE (
    id BIGINT,
    nombre VARCHAR(120),
    email VARCHAR(254),
    rol_id BIGINT,
    rol_nombre VARCHAR(30),
    activo BOOLEAN,
    created_at TIMESTAMPTZ
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
    v_rol_admin VARCHAR(30);
    v_busqueda TEXT;
    v_rol_nombre TEXT;
BEGIN
    -- 1. Identidad autenticada: usuario existente, activo y Administrador.
    IF p_admin_id IS NULL OR p_admin_id <= 0 THEN
        RAISE EXCEPTION 'El usuario es obligatorio'
            USING ERRCODE = '22023';
    END IF;

    SELECT r.nombre
      INTO v_rol_admin
      FROM public.usuarios AS u
      JOIN public.roles AS r ON r.id = u.rol_id
     WHERE u.id = p_admin_id
       AND u.activo = TRUE;

    IF v_rol_admin IS DISTINCT FROM 'Administrador' THEN
        RAISE EXCEPTION 'Usuario no autorizado para consultar usuarios'
            USING ERRCODE = '42501';
    END IF;

    -- 2. Paginación obligatoria, acotada y con desplazamiento no negativo.
    IF p_limite IS NULL OR p_limite < 1 OR p_limite > 100
       OR p_desplazamiento IS NULL OR p_desplazamiento < 0 THEN
        RAISE EXCEPTION 'Paginación inválida'
            USING ERRCODE = '22023';
    END IF;

    -- 3. Búsqueda opcional: recortada, acotada y con comodines literales.
    v_busqueda := NULLIF(btrim(p_busqueda), '');

    IF v_busqueda IS NOT NULL THEN
        IF char_length(v_busqueda) > 254 THEN
            RAISE EXCEPTION 'La búsqueda no puede superar los 254 caracteres'
                USING ERRCODE = '22023';
        END IF;

        v_busqueda := replace(
            replace(
                replace(v_busqueda, E'\\', E'\\\\'),
                '%',
                E'\\%'
            ),
            '_',
            E'\\_'
        );
    END IF;

    -- 4. Rol opcional: debe existir en el catálogo de roles.
    v_rol_nombre := NULLIF(btrim(p_rol_nombre), '');

    IF v_rol_nombre IS NOT NULL
       AND NOT EXISTS (
           SELECT 1
             FROM public.roles AS r
            WHERE r.nombre = v_rol_nombre
       ) THEN
        RAISE EXCEPTION 'El rol no existe'
            USING ERRCODE = '22023';
    END IF;

    -- 5. Listado determinista. El desempate por id mantiene la paginación
    --    estable cuando varios usuarios comparten created_at.
    RETURN QUERY
    SELECT
        u.id,
        u.nombre,
        u.email,
        u.rol_id,
        r.nombre,
        u.activo,
        u.created_at
      FROM public.usuarios AS u
      JOIN public.roles AS r ON r.id = u.rol_id
     WHERE (
               v_busqueda IS NULL
               OR u.nombre ILIKE ('%' || v_busqueda || '%') ESCAPE E'\\'
               OR u.email ILIKE ('%' || v_busqueda || '%') ESCAPE E'\\'
           )
       AND (v_rol_nombre IS NULL OR r.nombre = v_rol_nombre)
       AND (p_activo IS NULL OR u.activo = p_activo)
     ORDER BY u.created_at DESC, u.id DESC
     LIMIT p_limite OFFSET p_desplazamiento;
END;
$$;

CREATE OR REPLACE PROCEDURE public.sp_usuario_cambiar_estado_admin(
    IN  p_admin_id BIGINT,
    IN  p_usuario_id BIGINT,
    IN  p_activo BOOLEAN,
    OUT p_id BIGINT,
    OUT p_activo_resultado BOOLEAN,
    OUT p_updated_at TIMESTAMPTZ
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
    v_rol_admin VARCHAR(30);
    v_rol_objetivo VARCHAR(30);
    v_activo_actual BOOLEAN;
    v_updated_at TIMESTAMPTZ;
    v_administradores_activos BIGINT;
BEGIN
    -- 1. Parámetros obligatorios.
    IF p_admin_id IS NULL OR p_admin_id <= 0 THEN
        RAISE EXCEPTION 'El usuario administrador es obligatorio'
            USING ERRCODE = '22023';
    END IF;

    IF p_usuario_id IS NULL OR p_usuario_id <= 0 THEN
        RAISE EXCEPTION 'El usuario es obligatorio'
            USING ERRCODE = '22023';
    END IF;

    IF p_activo IS NULL THEN
        RAISE EXCEPTION 'El estado es obligatorio'
            USING ERRCODE = '22023';
    END IF;

    -- 2. Serializa todos los cambios de estado. Se adquiere antes de
    --    revalidar al administrador para que una desactivación concurrente
    --    del solicitante sea visible.
    PERFORM pg_advisory_xact_lock(
        hashtext('limpiahuancayo.usuarios.estado')::bigint
    );

    -- 3. Identidad autenticada: usuario existente, activo y Administrador.
    SELECT r.nombre
      INTO v_rol_admin
      FROM public.usuarios AS u
      JOIN public.roles AS r ON r.id = u.rol_id
     WHERE u.id = p_admin_id
       AND u.activo = TRUE;

    IF v_rol_admin IS DISTINCT FROM 'Administrador' THEN
        RAISE EXCEPTION 'Usuario no autorizado para cambiar el estado'
            USING ERRCODE = '42501';
    END IF;

    -- 4. Usuario objetivo con bloqueo de fila.
    SELECT r.nombre, u.activo, u.updated_at
      INTO v_rol_objetivo, v_activo_actual, v_updated_at
      FROM public.usuarios AS u
      JOIN public.roles AS r ON r.id = u.rol_id
     WHERE u.id = p_usuario_id
       FOR UPDATE OF u;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Usuario no encontrado'
            USING ERRCODE = 'P0002';
    END IF;

    -- 5. Un administrador no puede desactivar su propia cuenta.
    IF p_activo = FALSE AND p_usuario_id = p_admin_id THEN
        RAISE EXCEPTION 'No puede desactivar su propia cuenta'
            USING ERRCODE = '23514';
    END IF;

    -- 6. No se puede dejar el sistema sin administradores activos.
    --    Con la autodesactivación prohibida esta comprobación es una
    --    defensa en profundidad; la concurrencia se resuelve con el lock
    --    y la revalidación del solicitante.
    IF p_activo = FALSE
       AND v_rol_objetivo = 'Administrador'
       AND v_activo_actual = TRUE THEN
        SELECT count(*)
          INTO v_administradores_activos
          FROM public.usuarios AS u
          JOIN public.roles AS r ON r.id = u.rol_id
         WHERE r.nombre = 'Administrador'
           AND u.activo = TRUE;

        IF v_administradores_activos <= 1 THEN
            RAISE EXCEPTION 'No se puede desactivar al último administrador activo'
                USING ERRCODE = '55000';
        END IF;
    END IF;

    -- 7. Idempotencia: el mismo estado no modifica updated_at.
    IF v_activo_actual = p_activo THEN
        p_id := p_usuario_id;
        p_activo_resultado := v_activo_actual;
        p_updated_at := v_updated_at;
        RETURN;
    END IF;

    -- 8. Actualización del estado y updated_at.
    UPDATE public.usuarios
       SET activo = p_activo,
           updated_at = now()
     WHERE id = p_usuario_id
    RETURNING id, activo, updated_at
         INTO p_id, p_activo_resultado, p_updated_at;
END;
$$;

-- Las rutinas se crean ya aseguradas dentro de la misma transacción:
-- no quedan ejecutables por PUBLIC entre 19 y 20.
REVOKE ALL ON FUNCTION public.fn_usuario_listar_admin(
    BIGINT, TEXT, VARCHAR, BOOLEAN, INTEGER, INTEGER
) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION public.fn_usuario_listar_admin(
    BIGINT, TEXT, VARCHAR, BOOLEAN, INTEGER, INTEGER
) TO limpiahuancayo_app;

-- La firma de seguridad incluye solo los parámetros IN: los OUT no forman
-- parte de los argumentos de identidad de la rutina.
REVOKE ALL ON PROCEDURE public.sp_usuario_cambiar_estado_admin(
    BIGINT, BIGINT, BOOLEAN
) FROM PUBLIC;

GRANT EXECUTE ON PROCEDURE public.sp_usuario_cambiar_estado_admin(
    BIGINT, BIGINT, BOOLEAN
) TO limpiahuancayo_app;

COMMIT;
