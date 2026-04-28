import pandas as pd
import psycopg2
import os
import matplotlib.pyplot as plt
import seaborn as sns
import warnings

# Silenciar advertencias inofensivas de Pandas y Seaborn
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

# =============================================================================
# CONFIGURACIÓN DE RUTAS Y CONEXIÓN
# =============================================================================
OUTPUT_DIR = 'data/reports/businessQuestions/'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Credenciales de tu base de datos PostgreSQL
DB_CONFIG = {
    'dbname': 'proyecto_universidad', 
    'user': 'postgres',           
    'password': '12345',    
    'host': 'localhost',
    'port': '5432'
}

sns.set_theme(style="whitegrid", palette="muted")

def main():
    print("="*70)
    print(" PASO 6.1: GENERACIÓN DE REPORTES - PREGUNTAS DE NEGOCIO")
    print("="*70)
    
    conn = None

    try:
        print("[*] Conectando a PostgreSQL para extraer datos del Data Warehouse...")
        conn = psycopg2.connect(**DB_CONFIG)
        
        # Consulta SQL Ampliada: Añadimos D_Jornada
        query_maestra = """
            SELECT 
                a.numero_identificacion,
                a.edad,
                g.nombre AS genero,
                e.descripcion AS estrato,
                ci.nombre AS ciudad,
                o.descripcion AS ocupacion,
                fi.nombre_financiamiento AS financiamiento,
                c.nombre AS carrera,
                s.semestre AS nivel_semestre,
                m.tipo AS motivo,
                j.tipo AS jornada,
                f.valor_perdida_por_desercion,
                f.id_fecha_desercion
            FROM F_HechoMatricula f
            INNER JOIN D_Alumno a ON f.id_alumno = a.id_alumno
            INNER JOIN D_Genero g ON a.id_genero = g.id_genero
            INNER JOIN D_Estrato e ON a.id_estrato = e.id_estrato
            INNER JOIN D_Ciudad ci ON a.id_ciudad = ci.id_ciudad
            INNER JOIN D_Ocupacion o ON a.id_ocupacion = o.id_ocupacion
            INNER JOIN D_Financiamiento fi ON a.id_financiamiento = fi.id_financiamiento
            INNER JOIN D_Carrera c ON f.id_carrera = c.id_carrera
            INNER JOIN D_Semestre s ON f.id_semestre = s.id_semestre
            INNER JOIN D_Motivo m ON f.id_motivo = m.id_motivo
            INNER JOIN D_Jornada j ON f.id_jornada = j.id_jornada;
        """
        
        df_dw = pd.read_sql_query(query_maestra, conn)
        print(f"[+] Datos extraídos exitosamente. Total de registros analizados: {len(df_dw)}\n")

        # Filtramos un DataFrame exclusivo para estudiantes que DESERTARON
        df_desertores = df_dw[df_dw['id_fecha_desercion'] != 39991231].copy()

        print("[*] Procesando respuestas y generando visualizaciones...")
        reportes_excel = {}

        # ---------------------------------------------------------------------
        # REPORTES ANTERIORES (Carrera, Ciudad, Género, Edad, Estrato)
        # ---------------------------------------------------------------------
        
        # 1. Pérdida por carrera
        perdida_carrera = df_desertores.groupby('carrera')['valor_perdida_por_desercion'].sum().reset_index()
        perdida_carrera = perdida_carrera.sort_values(by='valor_perdida_por_desercion', ascending=False)
        reportes_excel['Perdida_por_Carrera'] = perdida_carrera
        
        plt.figure(figsize=(12, 6))
        sns.barplot(data=perdida_carrera.head(10), x='valor_perdida_por_desercion', y='carrera', hue='carrera', palette='Reds_r', legend=False)
        plt.title('Top 10 Carreras con Mayor Pérdida Financiera por Deserción', fontweight='bold')
        plt.xlabel('Pérdida Económica Proyectada ($)')
        plt.ylabel('Programa Académico')
        plt.gca().xaxis.set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, '01_Negocio_Perdida_Carrera.png'), dpi=300)
        plt.close()

        # 2. Deserción por Ciudad
        desercion_ciudad = df_desertores.groupby('ciudad')['numero_identificacion'].count().reset_index()
        desercion_ciudad.columns = ['Ciudad', 'Cantidad_Desertores']
        desercion_ciudad = desercion_ciudad.sort_values(by='Cantidad_Desertores', ascending=False).head(10)
        reportes_excel['Desercion_por_Ciudad'] = desercion_ciudad
        
        plt.figure(figsize=(10, 6))
        sns.barplot(data=desercion_ciudad, x='Cantidad_Desertores', y='Ciudad', hue='Ciudad', palette='viridis', legend=False)
        plt.title('Top 10 Ciudades con Mayor Deserción', fontweight='bold')
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, '02_Negocio_Desercion_Ciudad.png'), dpi=300)
        plt.close()

        # 3. Deserción por Género
        desercion_genero = df_desertores.groupby('genero')['numero_identificacion'].count().reset_index()
        desercion_genero.columns = ['Genero', 'Cantidad_Desertores']
        reportes_excel['Desercion_por_Genero'] = desercion_genero
        
        plt.figure(figsize=(8, 8))
        plt.pie(desercion_genero['Cantidad_Desertores'], labels=desercion_genero['Genero'], autopct='%1.1f%%', colors=sns.color_palette('pastel'))
        plt.title('Distribución de Deserción por Género', fontweight='bold')
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, '03_Negocio_Desercion_Genero.png'), dpi=300)
        plt.close()

        # 4. Deserción por Edad
        bins = [15, 20, 25, 30, 40, 100]
        labels = ['15-20', '21-25', '26-30', '31-40', '41+']
        df_desertores['rango_edad'] = pd.cut(df_desertores['edad'], bins=bins, labels=labels, right=True)
        desercion_edad = df_desertores.groupby('rango_edad', observed=False)['numero_identificacion'].count().reset_index()
        desercion_edad.columns = ['Rango_Edad', 'Cantidad_Desertores']
        reportes_excel['Desercion_por_Edad'] = desercion_edad
        
        plt.figure(figsize=(10, 5))
        sns.barplot(data=desercion_edad, x='Rango_Edad', y='Cantidad_Desertores', hue='Rango_Edad', palette='magma', legend=False)
        plt.title('Deserción por Rangos de Edad', fontweight='bold')
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, '04_Negocio_Desercion_Edad.png'), dpi=300)
        plt.close()

        # 5. Deserción por Estrato
        desercion_estrato = df_desertores.groupby('estrato')['numero_identificacion'].count().reset_index()
        desercion_estrato.columns = ['Estrato', 'Cantidad_Desertores']
        desercion_estrato = desercion_estrato.sort_values(by='Estrato')
        reportes_excel['Desercion_por_Estrato'] = desercion_estrato
        
        plt.figure(figsize=(10, 5))
        sns.barplot(data=desercion_estrato, x='Estrato', y='Cantidad_Desertores', hue='Estrato', palette='YlOrBr', legend=False)
        plt.title('Prevalencia de Deserción por Estrato Socioeconómico', fontweight='bold')
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, '05_Negocio_Desercion_Estrato.png'), dpi=300)
        plt.close()

        # 6. ¿En qué semestres ocurre mayor deserción?
        desercion_semestre = df_desertores.groupby('nivel_semestre')['numero_identificacion'].count().reset_index()
        desercion_semestre.columns = ['Semestre', 'Cantidad_Desertores']
        reportes_excel['Desercion_por_Semestre'] = desercion_semestre
        
        plt.figure(figsize=(10, 5))
        sns.lineplot(data=desercion_semestre, x='Semestre', y='Cantidad_Desertores', marker='o', color='b', linewidth=2.5)
        plt.title('Curva de Retiro: Volumen de Deserción por Nivel de Semestre', fontweight='bold')
        plt.xticks(desercion_semestre['Semestre'])
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, '06_Negocio_Desercion_Semestre.png'), dpi=300)
        plt.close()

        # 7. ¿Qué ocupación prevalece en los alumnos con deserción?
        desercion_ocupacion = df_desertores.groupby('ocupacion')['numero_identificacion'].count().reset_index()
        desercion_ocupacion.columns = ['Ocupacion', 'Cantidad_Desertores']
        desercion_ocupacion = desercion_ocupacion.sort_values(by='Cantidad_Desertores', ascending=False)
        reportes_excel['Desercion_por_Ocupacion'] = desercion_ocupacion
        
        plt.figure(figsize=(10, 5))
        sns.barplot(data=desercion_ocupacion, x='Cantidad_Desertores', y='Ocupacion', hue='Ocupacion', palette='cubehelix', legend=False)
        plt.title('Ocupación Prevalente en Alumnos Desertores', fontweight='bold')
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, '07_Negocio_Desercion_Ocupacion.png'), dpi=300)
        plt.close()

        # 8. ¿Qué tipo de financiamiento prevalece en los alumnos con deserción?
        desercion_finan = df_desertores.groupby('financiamiento')['numero_identificacion'].count().reset_index()
        desercion_finan.columns = ['Financiamiento', 'Cantidad_Desertores']
        desercion_finan = desercion_finan.sort_values(by='Cantidad_Desertores', ascending=False)
        reportes_excel['Desercion_por_Financiamiento'] = desercion_finan
        
        plt.figure(figsize=(10, 5))
        sns.barplot(data=desercion_finan, x='Financiamiento', y='Cantidad_Desertores', hue='Financiamiento', palette='Set2', legend=False)
        plt.title('Tipo de Financiamiento en Alumnos Desertores', fontweight='bold')
        plt.xticks(rotation=45) # Rota los textos si son muy largos
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, '08_Negocio_Desercion_Financiamiento.png'), dpi=300)
        plt.close()

        # 9. ¿Cuál es el principal motivo de los alumnos con deserción?
        desercion_motivo = df_desertores.groupby('motivo')['numero_identificacion'].count().reset_index()
        desercion_motivo.columns = ['Motivo', 'Cantidad_Desertores']
        desercion_motivo = desercion_motivo.sort_values(by='Cantidad_Desertores', ascending=False)
        reportes_excel['Desercion_por_Motivo'] = desercion_motivo
        
        plt.figure(figsize=(12, 6))
        sns.barplot(data=desercion_motivo, x='Cantidad_Desertores', y='Motivo', hue='Motivo', palette='rocket', legend=False)
        plt.title('Principales Motivos de Deserción', fontweight='bold')
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, '09_Negocio_Desercion_Motivo.png'), dpi=300)
        plt.close()

        # 10. ¿Qué jornada los alumnos tienden a tener mayor deserción?
        desercion_jornada = df_desertores.groupby('jornada')['numero_identificacion'].count().reset_index()
        desercion_jornada.columns = ['Jornada', 'Cantidad_Desertores']
        reportes_excel['Desercion_por_Jornada'] = desercion_jornada
        
        plt.figure(figsize=(8, 8))
        plt.pie(desercion_jornada['Cantidad_Desertores'], labels=desercion_jornada['Jornada'], autopct='%1.1f%%', colors=sns.color_palette('Set3'))
        plt.title('Deserción Comparativa por Tipo de Jornada', fontweight='bold')
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, '10_Negocio_Desercion_Jornada.png'), dpi=300)
        plt.close()

        print("    -> ¡Diez (10) reportes gráficos generados exitosamente en alta resolución!")

        # =====================================================================
        # EXPORTACIÓN A EXCEL (CONSOLIDADO NUMÉRICO)
        # =====================================================================
        print("\n[*] Exportando libro de Excel con los datos crudos consolidados...")
        ruta_excel = os.path.join(OUTPUT_DIR, 'Reporte_01_Preguntas_Negocio.xlsx')
        
        with pd.ExcelWriter(ruta_excel, engine='openpyxl') as writer:
            for nombre_hoja, df_datos in reportes_excel.items():
                df_datos.to_excel(writer, sheet_name=nombre_hoja, index=False)
            
        print(f"[+] ¡Proceso finalizado! Revisa la carpeta: {OUTPUT_DIR}")
        print("="*70)

    except Exception as e:
        print(f"\n[ERROR] Ocurrió un problema: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()