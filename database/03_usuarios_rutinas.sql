-- LimpiaHuancayo - Rutinas de usuarios v1
-- Requiere 01_esquema.sql y 02_datos_iniciales.sql
-- Ejecutar conectado a la base limpiahuancayo como propietario de las tablas.
BEGIN;

CREATE OR REPLACE PROCEDURE public.sp_usuario_registrar(
    IN p_nombre VARCHAR,
    IN p_email VARCHAR,
    IN p_password_hash TEXT,
    INOUT p_usuario_id BIGINT DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_rol_id BIGINT;
BEGIN
    IF NULLIF(btrim(p_nombre), '') IS NULL THEN
        RAISE EXCEPTION 'El nombre es obligatorio' USING ERRCODE = '22023';
    END IF;
    IF NULLIF(btrim(p_email), '') IS NULL OR position('@' IN p_email) = 0 THEN
        RAISE EXCEPTION 'El correo electrónico no es válido' USING ERRCODE = '22023';
    END IF;
    IF NULLIF(btrim(p_password_hash), '') IS NULL THEN
        RAISE EXCEPTION 'El hash de contraseña es obligatorio' USING ERRCODE = '22023';
    END IF;

    SELECT id INTO v_rol_id FROM public.roles WHERE nombre = 'Ciudadano';
    IF v_rol_id IS NULL THEN
        RAISE EXCEPTION 'No existe el rol Ciudadano' USING ERRCODE = '23503';
    END IF;

    INSERT INTO public.usuarios (nombre, email, password_hash, rol_id)
    VALUES (btrim(p_nombre), lower(btrim(p_email)), p_password_hash, v_rol_id)
    RETURNING id INTO p_usuario_id;
END;
$$;

CREATE OR REPLACE FUNCTION public.fn_usuario_obtener_por_email(p_email TEXT)
RETURNS TABLE (
    id BIGINT, nombre VARCHAR, email VARCHAR, password_hash TEXT,
    rol_id BIGINT, rol_nombre VARCHAR, activo BOOLEAN,
    created_at TIMESTAMPTZ, updated_at TIMESTAMPTZ
)
LANGUAGE sql STABLE
AS $$
    SELECT u.id, u.nombre, u.email, u.password_hash,
           u.rol_id, r.nombre, u.activo, u.created_at, u.updated_at
    FROM public.usuarios u
    JOIN public.roles r ON r.id = u.rol_id
    WHERE lower(btrim(u.email)) = lower(btrim(p_email))
$$;

CREATE OR REPLACE FUNCTION public.fn_usuario_obtener_por_id(p_usuario_id BIGINT)
RETURNS TABLE (
    id BIGINT, nombre VARCHAR, email VARCHAR,
    rol_id BIGINT, rol_nombre VARCHAR, activo BOOLEAN,
    created_at TIMESTAMPTZ, updated_at TIMESTAMPTZ
)
LANGUAGE sql STABLE
AS $$
    SELECT u.id, u.nombre, u.email, u.rol_id, r.nombre,
           u.activo, u.created_at, u.updated_at
    FROM public.usuarios u
    JOIN public.roles r ON r.id = u.rol_id
    WHERE u.id = p_usuario_id
$$;

CREATE OR REPLACE PROCEDURE public.sp_usuario_actualizar_perfil(
    IN p_usuario_id BIGINT,
    IN p_nombre VARCHAR
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF NULLIF(btrim(p_nombre), '') IS NULL THEN
        RAISE EXCEPTION 'El nombre es obligatorio' USING ERRCODE = '22023';
    END IF;
    UPDATE public.usuarios
    SET nombre = btrim(p_nombre), updated_at = now()
    WHERE id = p_usuario_id AND activo = TRUE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Usuario no encontrado o inactivo' USING ERRCODE = 'P0002';
    END IF;
END;
$$;

CREATE OR REPLACE FUNCTION public.fn_usuario_listar(
    p_busqueda TEXT DEFAULT NULL,
    p_rol_id BIGINT DEFAULT NULL,
    p_activo BOOLEAN DEFAULT NULL,
    p_limite INTEGER DEFAULT 20,
    p_desplazamiento INTEGER DEFAULT 0
)
RETURNS TABLE (
    id BIGINT, nombre VARCHAR, email VARCHAR,
    rol_id BIGINT, rol_nombre VARCHAR, activo BOOLEAN,
    created_at TIMESTAMPTZ
)
LANGUAGE plpgsql STABLE
AS $$
BEGIN
    IF p_limite IS NULL OR p_limite < 1 OR p_limite > 100
       OR p_desplazamiento IS NULL OR p_desplazamiento < 0 THEN
        RAISE EXCEPTION 'Paginación inválida' USING ERRCODE = '22023';
    END IF;
    RETURN QUERY
    SELECT u.id, u.nombre, u.email, u.rol_id, r.nombre, u.activo, u.created_at
    FROM public.usuarios u
    JOIN public.roles r ON r.id = u.rol_id
    WHERE (p_busqueda IS NULL OR u.nombre ILIKE '%' || p_busqueda || '%'
           OR u.email ILIKE '%' || p_busqueda || '%')
      AND (p_rol_id IS NULL OR u.rol_id = p_rol_id)
      AND (p_activo IS NULL OR u.activo = p_activo)
    ORDER BY u.created_at DESC, u.id DESC
    LIMIT p_limite OFFSET p_desplazamiento;
END;
$$;

CREATE OR REPLACE PROCEDURE public.sp_usuario_cambiar_estado(
    IN p_usuario_id BIGINT,
    IN p_activo BOOLEAN
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF p_activo IS NULL THEN
        RAISE EXCEPTION 'El estado es obligatorio' USING ERRCODE = '22023';
    END IF;
    UPDATE public.usuarios
    SET activo = p_activo, updated_at = now()
    WHERE id = p_usuario_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Usuario no encontrado' USING ERRCODE = 'P0002';
    END IF;
END;
$$;

-- La función que devuelve el hash es exclusivamente para el backend.
-- Revocar acceso público por defecto y conceder EXECUTE solo al rol de aplicación.
REVOKE ALL ON PROCEDURE public.sp_usuario_registrar(VARCHAR, VARCHAR, TEXT, BIGINT) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.fn_usuario_obtener_por_email(TEXT) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.fn_usuario_obtener_por_id(BIGINT) FROM PUBLIC;
REVOKE ALL ON PROCEDURE public.sp_usuario_actualizar_perfil(BIGINT, VARCHAR) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.fn_usuario_listar(TEXT, BIGINT, BOOLEAN, INTEGER, INTEGER) FROM PUBLIC;
REVOKE ALL ON PROCEDURE public.sp_usuario_cambiar_estado(BIGINT, BOOLEAN) FROM PUBLIC;

COMMIT;
