import psycopg2
from decouple import config
import dj_database_url

def get_db_connection():
    """Retorna una conexión a la base de datos usando la URL de configuración."""
    # Obtenemos la URL del .env
    db_url = config('DATABASE_URL')
    
    # Parseamos la URL para extraer los componentes que necesita psycopg2
    db_config = dj_database_url.parse(db_url)
    
    return psycopg2.connect(
        dbname=db_config['NAME'],
        user=db_config['USER'],
        password=db_config['PASSWORD'],
        host=db_config['HOST'],
        port=db_config['PORT'],
        sslmode='require'  # <--- CRÍTICO para conectar a Render desde fuera
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


