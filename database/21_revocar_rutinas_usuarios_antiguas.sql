-- LimpiaHuancayo - Revocación de rutinas antiguas de usuarios v1
-- Requiere 01_esquema.sql, 02_datos_iniciales.sql, 03_usuarios_rutinas.sql,
-- 04_permisos_usuarios.sql, 19_usuarios_admin.sql y
-- 20_permisos_usuarios_admin.sql.
-- Ejecutar como propietario de las rutinas, después de 20.
--
-- La API no usa fn_usuario_listar ni sp_usuario_cambiar_estado. Esas rutinas
-- no validan el rol administrativo ni participan del lock de las rutinas
-- nuevas, por lo que se revoca su EXECUTE al rol de aplicación.
--
-- No se eliminan las rutinas ni se modifican sus definiciones.
--
-- La revocación se verifica dentro de la misma transacción:
-- - has_function_privilege() comprueba el permiso efectivo del rol de
--   aplicación, incluidos los permisos heredados por pertenencia a roles.
-- - aclexplode() comprueba que PUBLIC no conserve EXECUTE.
-- Si alguna comprobación falla, se lanza una excepción y la transacción se
-- revierte para no dejar una falsa sensación de seguridad.
--
-- La comprobación cubre permisos directos e heredados. Si el rol de
-- aplicación puede hacer SET ROLE a otro rol con EXECUTE, revisar esa
-- membresía por separado.
BEGIN;

REVOKE EXECUTE ON FUNCTION public.fn_usuario_listar(
    TEXT, BIGINT, BOOLEAN, INTEGER, INTEGER
) FROM PUBLIC;

REVOKE EXECUTE ON FUNCTION public.fn_usuario_listar(
    TEXT, BIGINT, BOOLEAN, INTEGER, INTEGER
) FROM limpiahuancayo_app;

REVOKE EXECUTE ON PROCEDURE public.sp_usuario_cambiar_estado(
    BIGINT, BOOLEAN
) FROM PUBLIC;

REVOKE EXECUTE ON PROCEDURE public.sp_usuario_cambiar_estado(
    BIGINT, BOOLEAN
) FROM limpiahuancayo_app;

DO $$
BEGIN
    IF pg_catalog.has_function_privilege(
        'limpiahuancayo_app',
        'public.fn_usuario_listar(text,bigint,boolean,integer,integer)',
        'EXECUTE'
    ) THEN
        RAISE EXCEPTION
            'La revocación no fue efectiva para fn_usuario_listar: revise permisos heredados'
            USING ERRCODE = '42501';
    END IF;

    IF pg_catalog.has_function_privilege(
        'limpiahuancayo_app',
        'public.sp_usuario_cambiar_estado(bigint,boolean)',
        'EXECUTE'
    ) THEN
        RAISE EXCEPTION
            'La revocación no fue efectiva para sp_usuario_cambiar_estado: revise permisos heredados'
            USING ERRCODE = '42501';
    END IF;

    IF EXISTS (
        SELECT 1
          FROM pg_catalog.pg_proc AS p
         WHERE p.oid =
               'public.fn_usuario_listar(text,bigint,boolean,integer,integer)'::pg_catalog.regprocedure
           AND (
               p.proacl IS NULL
               OR EXISTS (
                   SELECT 1
                     FROM pg_catalog.aclexplode(p.proacl) AS a
                    WHERE a.grantee = 0
                      AND a.privilege_type = 'EXECUTE'
               )
           )
    ) THEN
        RAISE EXCEPTION
            'PUBLIC conserva EXECUTE sobre fn_usuario_listar'
            USING ERRCODE = '42501';
    END IF;

    IF EXISTS (
        SELECT 1
          FROM pg_catalog.pg_proc AS p
         WHERE p.oid =
               'public.sp_usuario_cambiar_estado(bigint,boolean)'::pg_catalog.regprocedure
           AND (
               p.proacl IS NULL
               OR EXISTS (
                   SELECT 1
                     FROM pg_catalog.aclexplode(p.proacl) AS a
                    WHERE a.grantee = 0
                      AND a.privilege_type = 'EXECUTE'
               )
           )
    ) THEN
        RAISE EXCEPTION
            'PUBLIC conserva EXECUTE sobre sp_usuario_cambiar_estado'
            USING ERRCODE = '42501';
    END IF;
END;
$$;

COMMIT;
