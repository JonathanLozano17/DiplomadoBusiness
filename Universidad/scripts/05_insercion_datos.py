import psycopg2
import os

# =============================================================================
# CONFIGURACIÓN DE RUTAS Y BASE DE DATOS
# =============================================================================
INPUT_DIR = 'data/processed/dimensional/'

# Credenciales de la base de datos PostgreSQL
DB_CONFIG = {
    'dbname': 'proyecto_universidad', 
    'user': 'postgres',           
    'password': '1717',    
    'host': 'localhost',
    'port': '5432'
}

# ORDEN ESTRICTO DE INSERCIÓN (Para respetar las Llaves Foráneas)
TABLAS = [
    'd_genero', 'd_estrato', 'd_ciudad', 'd_ocupacion', 
    'd_financiamiento', 'd_jornada', 'd_motivo', 'd_carrera',
    'd_fecha', 'd_semestre', 'd_alumno', 'f_hechomatricula'
]

def main():
    print("="*60)
    print(" PASO 5: CARGA MASIVA DE DATOS A POSTGRESQL (COPY)")
    print("="*60)
    
    conn = None
    try:
        # Conectar a la base de datos
        print("[*] Conectando a la base de datos PostgreSQL...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("[+] Conexión exitosa.\n")
        
        # Iterar sobre las tablas en el orden correcto
        for tabla in TABLAS:
            # Los CSV se guardaron con mayúsculas en el script 3 (Ej: D_Genero.csv)
            # Adaptamos el nombre de la tabla SQL al nombre del archivo
            archivo_csv = f"{tabla.title().replace('_H', '_h').replace('_M', '_m').replace('_C', '_c')}.csv"
            if tabla == 'f_hechomatricula':
                archivo_csv = 'F_HechoMatricula.csv'
            elif tabla.startswith('d_'):
                archivo_csv = f"D_{tabla[2:].capitalize()}.csv"
                
            ruta_csv = os.path.join(INPUT_DIR, archivo_csv)
            
            if not os.path.exists(ruta_csv):
                print(f"[!] ADVERTENCIA: No se encontró el archivo {ruta_csv}")
                continue
                
            print(f"[*] Cargando {archivo_csv} en la tabla {tabla}...")
            
            # El comando copy_expert ejecuta el COPY desde el lado del cliente (Python)
            # Esto soluciona por completo el error "Permission denied" de Postgres
            with open(ruta_csv, 'r', encoding='utf-8') as f:
                # Omitir el id_hecho en la tabla de hechos porque es SERIAL
                if tabla == 'f_hechomatricula':
                    columnas = "(id_alumno, id_carrera, id_semestre, id_motivo, id_jornada, id_fecha_inicio_estudios, id_fecha_desercion, id_fecha_inicio_semestre, id_fecha_final_semestre, promedio_semestral, cantidad_materias_perdidas, valor_perdida_por_desercion, valor_deuda, id_fecha_creacion, id_fecha_actualizacion, activo)"
                    sql = f"COPY {tabla}{columnas} FROM STDIN WITH CSV HEADER DELIMITER ','"
                else:
                    sql = f"COPY {tabla} FROM STDIN WITH CSV HEADER DELIMITER ','"
                
                cursor.copy_expert(sql, f)
                conn.commit()
                print(f"    -> ¡Datos insertados exitosamente en {tabla}!")
                
        print("\n[+] ¡PROCESO ETL DE CARGA FINALIZADO CON ÉXITO!")
        print("="*60)

    except Exception as e:
        print(f"\n[ERROR] Ocurrió un problema: {e}")
        if conn:
            conn.rollback() # Si hay error, deshace los cambios a medias
    finally:
        if conn:
            cursor.close()
            conn.close()
            print("[*] Conexión a la base de datos cerrada.")

if __name__ == "__main__":
    main()