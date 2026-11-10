-- LimpiaHuancayo - Administrador inicial
-- Requiere 01_esquema.sql y 02_datos_iniciales.sql.
-- Ejecutar manualmente como propietario de las tablas, no como limpiahuancayo_app.
--
-- Este script no contiene credenciales. Antes de ejecutarlo, defina los
-- parametros en la MISMA sesion de pgAdmin 4 (Query Tool) o de psql:
--
--   SET lh.admin_email  = 'correo-del-administrador';
--   SET lh.admin_nombre = 'Nombre del administrador';
--   SET lh.admin_hash   = '<hash Argon2id generado localmente>';
--
-- No guarde el hash ni la contrasena en este archivo. El hash se genera con
-- backend.core.security.hash_password y se pega solo en la sentencia SET.
--
-- Las sentencias SET con valores reales pueden quedar registradas en el
-- historial de pgAdmin aunque este script ejecute RESET. RESET limpia la
-- variable de la sesion, no el historial del cliente. Use una pestana
-- temporal y borre el historial al terminar.
--
-- Si el bloque falla, la transaccion queda abortada. Ejecute ROLLBACK; en la
-- misma sesion antes de corregir los parametros. No se habra creado nada.
--
-- El script es idempotente:
--   * si el correo ya pertenece a un Administrador, no hace nada;
--   * si el correo pertenece a otro rol, aborta sin modificar la cuenta;
--   * si ya existe cualquier Administrador, no crea otro;
--   * usa un lock de asesoramiento para serializar ejecuciones concurrentes.
--
-- No modifica sp_usuario_registrar ni concede privilegios a la aplicacion.

BEGIN;

DO $$
DECLARE
    v_email TEXT := lower(btrim(current_setting('lh.admin_email', true)));
    v_nombre TEXT := btrim(current_setting('lh.admin_nombre', true));
    v_hash TEXT := btrim(current_setting('lh.admin_hash', true));
    v_rol_existente VARCHAR(30);
    v_rol_id BIGINT;
    v_usuario_id BIGINT;
BEGIN
    IF v_email IS NULL OR v_email = ''
       OR v_email !~ '^[^[:space:]@]+@[^[:space:]@]+$'
       OR char_length(v_email) > 254 THEN
        RAISE EXCEPTION 'Correo de administrador invalido o ausente'
            USING ERRCODE = '22023';
    END IF;

    IF v_nombre IS NULL OR v_nombre = ''
       OR char_length(v_nombre) > 120 THEN
        RAISE EXCEPTION 'Nombre de administrador invalido o ausente'
            USING ERRCODE = '22023';
    END IF;

    IF v_hash IS NULL OR v_hash = ''
       OR v_hash NOT LIKE '$argon2id$%' THEN
        RAISE EXCEPTION 'Hash Argon2id invalido o ausente'
            USING ERRCODE = '22023';
    END IF;

    IF NOT has_table_privilege(current_user, 'public.usuarios', 'INSERT') THEN
        RAISE EXCEPTION 'Ejecute este script como propietario de las tablas'
            USING ERRCODE = '42501';
    END IF;

    -- Serializa dos ejecuciones simultaneas del inicializador. El lock se
    -- libera automaticamente al terminar la transaccion.
    PERFORM pg_advisory_xact_lock(
        hashtext('limpiahuancayo.admin_inicial')::bigint
    );

    -- 1. El correo ya existe: no se modifica ninguna cuenta.
    SELECT r.nombre
      INTO v_rol_existente
      FROM public.usuarios u
      JOIN public.roles r ON r.id = u.rol_id
     WHERE lower(btrim(u.email)) = v_email;

    IF FOUND THEN
        IF v_rol_existente = 'Administrador' THEN
            RAISE NOTICE 'El administrador ya existe; no se crea otro.';
            RETURN;
        END IF;

        RAISE EXCEPTION 'El correo ya pertenece a un usuario; no se modifica'
            USING ERRCODE = '23505';
    END IF;

    -- 2. Ya existe un administrador con otro correo: no se crea otro.
    IF EXISTS (
        SELECT 1
          FROM public.usuarios u
          JOIN public.roles r ON r.id = u.rol_id
         WHERE r.nombre = 'Administrador'
    ) THEN
        RAISE NOTICE 'Ya existe un administrador; no se crea otro.';
        RETURN;
    END IF;

    SELECT id
      INTO v_rol_id
      FROM public.roles
     WHERE nombre = 'Administrador';

    IF v_rol_id IS NULL THEN
        RAISE EXCEPTION 'No existe el rol Administrador'
            USING ERRCODE = 'P0002';
    END IF;

    INSERT INTO public.usuarios (
        nombre,
        email,
        password_hash,
        rol_id,
        activo
    )
    VALUES (
        v_nombre,
        v_email,
        v_hash,
        v_rol_id,
        TRUE
    )
    RETURNING id INTO v_usuario_id;

    RAISE NOTICE 'Administrador inicial creado con id %', v_usuario_id;
END;
$$;

COMMIT;

-- Limpia los parametros de la sesion para no dejarlos disponibles.
RESET lh.admin_email;
RESET lh.admin_nombre;
RESET lh.admin_hash;
