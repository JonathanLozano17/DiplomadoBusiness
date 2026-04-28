import psycopg2
from decouple import config

def get_db_connection():
    """Retorna una conexión a la base de datos PostgreSQL."""
    return psycopg2.connect(
        dbname=config('DB_NAME'),
        user=config('DB_USER'),
        password=config('DB_PASSWORD'),
        host=config('DB_HOST'),
        port=config('DB_PORT')
    )

def ejecutar_query(query, params=None):
    """Ejecuta una consulta SQL y retorna los resultados como lista de diccionarios."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            columnas = [desc[0] for desc in cur.description]
            resultados = [dict(zip(columnas, fila)) for fila in cur.fetchall()]
        return resultados
    finally:
        conn.close()


