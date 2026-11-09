
import os

import psycopg
from dotenv import load_dotenv

load_dotenv()

try:
    with psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        connect_timeout=5,
    ) as conexion:

        with conexion.cursor() as cursor:

            # Verificar la identidad de la conexión
            cursor.execute(
                "SELECT current_user, current_database()"
            )

            usuario, base_datos = cursor.fetchone()

            print("Conexión exitosa")
            print("Usuario:", usuario)
            print("Base de datos:", base_datos)

            # Consultar una función almacenada
            cursor.execute(
                "SELECT * FROM public.fn_tipo_reporte_listar()"
            )

            categorias = cursor.fetchall()

            print("\nCategorías disponibles:")

            for categoria in categorias:
                print(categoria)

except psycopg.Error as error:
    print("Error de PostgreSQL:", error)
