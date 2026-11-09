-- LimpiaHuancayo v1.0 - Catalogos iniciales
BEGIN;
INSERT INTO roles(nombre) VALUES ('Ciudadano'), ('Administrador') ON CONFLICT (nombre) DO NOTHING;
INSERT INTO distritos(nombre) VALUES ('Huancayo'), ('El Tambo'), ('Chilca') ON CONFLICT (nombre) DO NOTHING;
INSERT INTO tipos_reporte(nombre,descripcion) VALUES
 ('Acumulación de basura','Residuos abandonados en calles, parques y espacios públicos'),
 ('Desmonte y escombros','Restos de construcción depositados inadecuadamente'),
 ('Quema de residuos','Quema de basura u otros residuos en espacios abiertos'),
 ('Contenedores desbordados','Contenedores llenos con acumulación de residuos alrededor')
 ON CONFLICT (nombre) DO NOTHING;
INSERT INTO estados_reporte(nombre) VALUES ('Pendiente'), ('En atención'), ('Resuelto'), ('Rechazado') ON CONFLICT (nombre) DO NOTHING;
COMMIT;
