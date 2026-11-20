-- LimpiaHuancayo - Estadisticas administrativas de reportes v1
-- Requiere 01_esquema.sql y 02_datos_iniciales.sql.
-- Ejecutar como propietario de las tablas y rutinas, después de 16.
--
-- Una sola funcion devuelve todos los indicadores en una misma consulta, de
-- modo que los conteos comparten un unico snapshot y son coherentes entre si.
-- El rol no se recibe desde el cliente: se resuelve en public.usuarios y
-- public.roles con el identificador autenticado que FastAPI obtiene del token.
--
-- Formato largo: una fila por indicador, identificada por la columna seccion.
--   resumen   -> total de reportes registrados (clave_id y clave_nombre NULL)
--   estado    -> una fila por estado del catalogo, incluso con total 0
--   distrito  -> solo distritos con al menos un reporte
--   categoria -> solo tipos de reporte con al menos un reporte
--
-- Coherencia: la suma de cada distribucion coincide con el total porque
-- reportes.estado_id, distrito_id y tipo_id son NOT NULL y tienen clave
-- foranea contra los catalogos.
--
-- No crea tablas, columnas ni indices. No modifica los scripts 01 a 16.
BEGIN;

CREATE OR REPLACE FUNCTION public.fn_reporte_estadisticas_admin(
    p_admin_id BIGINT
)
RETURNS TABLE (
    seccion TEXT,
    clave_id BIGINT,
    clave_nombre TEXT,
    total BIGINT
)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
    v_rol_nombre VARCHAR(30);
BEGIN
    -- 1. Parametro obligatorio.
    IF p_admin_id IS NULL OR p_admin_id <= 0 THEN
        RAISE EXCEPTION 'El usuario es obligatorio'
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
        RAISE EXCEPTION 'Usuario no autorizado para consultar estadísticas'
            USING ERRCODE = '42501';
    END IF;

    -- 3. Indicadores en una sola sentencia: el UNION ALL se evalua sobre el
    --    mismo snapshot, de modo que un reporte insertado durante la consulta
    --    no puede descuadrar el total frente a las distribuciones.
    RETURN QUERY
    WITH datos AS (
        SELECT
            'resumen'::TEXT AS seccion,
            NULL::BIGINT AS clave_id,
            NULL::TEXT AS clave_nombre,
            COUNT(*) AS total
          FROM public.reportes

        UNION ALL

        SELECT
            'estado'::TEXT,
            e.id,
            e.nombre::TEXT,
            COUNT(r.id)
          FROM public.estados_reporte AS e
          LEFT JOIN public.reportes AS r ON r.estado_id = e.id
         GROUP BY e.id, e.nombre

        UNION ALL

        SELECT
            'distrito'::TEXT,
            d.id,
            d.nombre::TEXT,
            COUNT(r.id)
          FROM public.reportes AS r
          JOIN public.distritos AS d ON d.id = r.distrito_id
         GROUP BY d.id, d.nombre

        UNION ALL

        SELECT
            'categoria'::TEXT,
            t.id,
            t.nombre::TEXT,
            COUNT(r.id)
          FROM public.reportes AS r
          JOIN public.tipos_reporte AS t ON t.id = r.tipo_id
         GROUP BY t.id, t.nombre
    )
    SELECT datos.seccion, datos.clave_id, datos.clave_nombre, datos.total
      FROM datos
     ORDER BY
        CASE datos.seccion
            WHEN 'resumen'   THEN 1
            WHEN 'estado'    THEN 2
            WHEN 'distrito'  THEN 3
            ELSE 4
        END,
        datos.clave_id;
END;
$$;

-- La funcion se crea ya asegurada dentro de la misma transaccion:
-- no queda ejecutable por PUBLIC entre 17 y 18.
REVOKE ALL ON FUNCTION public.fn_reporte_estadisticas_admin(
    BIGINT
) FROM PUBLIC;

GRANT EXECUTE ON FUNCTION public.fn_reporte_estadisticas_admin(
    BIGINT
) TO limpiahuancayo_app;

COMMIT;
