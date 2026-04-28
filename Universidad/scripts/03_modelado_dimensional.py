import pandas as pd
import os
from datetime import datetime

# =============================================================================
# CONFIGURACIÓN DE RUTAS
# =============================================================================
# Ruta archivo CSV estandarizado
INPUT_CSV = 'data/processed/dataset_estandarizado.csv'

# Ruta a almarcenar los CSV de las dimensiones y la fact
OUTPUT_DIR = 'data/processed/dimensional/'

# Fecha de ejecución actual para los campos id_fecha_creacion / actualizacion
FECHA_PROCESO = int(datetime.now().strftime('%Y%m%d'))

# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================
def crear_dimension_simple(df, col_origen, nombre_id, nombre_desc):
    """Crea un DataFrame de dimensión simple extrayendo valores únicos y ordenándolos."""
    
    # Elimina filas repetidas y valores nulos, dejando valores unicos
    # Agregamos .sort_values(by=col_origen) para que se ordenen de menor a mayor o alfabéticamente
    unicos = df[[col_origen]].drop_duplicates().dropna().sort_values(by=col_origen).reset_index(drop=True)
    # Nuevo indice autoincremental
    unicos[nombre_id] = unicos.index + 1 # Autoincremental desde 1
    # El nombre del campo
    unicos = unicos.rename(columns={col_origen: nombre_desc})
    return unicos[[nombre_id, nombre_desc]]

def fecha_a_id(serie_fechas):
    """Convierte una serie de fechas YYYY-MM-DD a un ID entero YYYYMMDD"""
    return serie_fechas.str.replace('-', '').astype(int)

# =============================================================================
# PROCESO PRINCIPAL
# =============================================================================
def main():
    print("="*60)
    print(" PASO 3: DESCOMPOSICIÓN AL MODELO DIMENSIONAL")
    print("="*60)
    
    # Verificar la existencia del archivo CSV estandarizado 
    if not os.path.exists(INPUT_CSV):
        print(f"[ERROR] No se encontró: {INPUT_CSV}")
        return

    # Crear carpeta de salida si no existe
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("[*] Cargando dataset estandarizado...")
    df = pd.read_csv(INPUT_CSV)
    
    # Asegurarnos de que Mora sea un booleano para los cálculos financieros
    if 'Mora' in df.columns:
        df['Mora'] = df['Mora'].astype(str).str.lower().map({'true': True, 'false': False, '1': True, '0': False}).fillna(False)

    print("[*] Generando Dimensiones...")

    # 1. DIMENSIONES SIMPLES
    # Se utiliza la funcion creada con anterioridad para dimensiones simples 
    dim_genero = crear_dimension_simple(df, 'Genero', 'id_genero', 'nombre')
    dim_estrato = crear_dimension_simple(df, 'Estrato', 'id_estrato', 'descripcion')
    dim_ciudad = crear_dimension_simple(df, 'Ciudad', 'id_ciudad', 'nombre')
    dim_ocupacion = crear_dimension_simple(df, 'Ocupacion', 'id_ocupacion', 'descripcion')
    dim_financiamiento = crear_dimension_simple(df, 'Financiamiento', 'id_financiamiento', 'nombre_financiamiento')
    dim_jornada = crear_dimension_simple(df, 'Jornada', 'id_jornada', 'tipo')
    dim_motivo = crear_dimension_simple(df, 'Motivo', 'id_motivo', 'tipo')
    dim_carrera = crear_dimension_simple(df, 'Carrera', 'id_carrera', 'nombre')

    # 2. DIMENSIÓN FECHA (Consolidada)
    print("    -> Construyendo Dimensión Fecha...")
    columnas_fecha = ['FechaInicioEstudios', 'FechaDesercion', 'FechaInicioSemestre', 'FechaFinalSemestre', 'FechaNacimiento']
    # Toma las columnas de fechas y las concatena para encontrar todas las fechas posibles
    fechas_unicas = pd.concat([df[col] for col in columnas_fecha if col in df.columns]).dropna().unique()
    # Convierte el arreglo en una estructura de tabla con nombre de columna 
    dim_fecha = pd.DataFrame({'fecha_str': fechas_unicas})
    dim_fecha['id_fecha'] = fecha_a_id(dim_fecha['fecha_str'])
    
    # Extraer partes de la fecha
    # Convierte el texto de la fecha a un formato especial de "Tiempo"
    fechas_dt = pd.to_datetime(dim_fecha['fecha_str'])
    # Se extraen el año, el mes y el día sin necesidad de hacer fórmulas complejas de texto.
    dim_fecha['anio'] = fechas_dt.dt.year
    dim_fecha['mes'] = fechas_dt.dt.month
    dim_fecha['dia'] = fechas_dt.dt.day
    dim_fecha = dim_fecha[['id_fecha', 'anio', 'mes', 'dia']].drop_duplicates().sort_values('id_fecha')

    # 3. DIMENSIÓN SEMESTRE
    # Se crea un registro único por cada combinación que exista
    print("    -> Construyendo Dimensión Semestre...")
    
    dim_semestre = df[['Semestre', 'ValorSemestre']].drop_duplicates().reset_index(drop=True)
    dim_semestre['id_semestre'] = dim_semestre.index + 1
    dim_semestre = dim_semestre.rename(columns={'Semestre': 'semestre', 'ValorSemestre': 'valor'})
    dim_semestre['activo'] = True
    dim_semestre['id_fecha_creacion'] = FECHA_PROCESO
    dim_semestre['id_fecha_actualizacion'] = FECHA_PROCESO
    dim_semestre = dim_semestre[['id_semestre', 'semestre', 'valor', 'activo', 'id_fecha_creacion', 'id_fecha_actualizacion']]

    # 4. DIMENSIÓN ALUMNO
    print("    -> Construyendo Dimensión Alumno (Con Historial SCD2)...")
    
    # Ordenamos el dataset original por estudiante y cronológicamente por semestre
    df_ordenado = df.sort_values(by=['Identificacion', 'Semestre'])
    
    # Columnas que definen el "perfil" sociodemográfico del alumno en un momento dado
    cols_perfil = ['Identificacion', 'TipoIdentificacion', 'NombreAlumno', 'Telefono', 
                   'Direccion', 'Edad', 'Genero', 'Estrato', 'Ciudad', 'Ocupacion', 
                   'Financiamiento', 'FechaNacimiento']
    
    # Extraemos todas las versiones únicas que ha tenido cada estudiante
    # Al estar previamente ordenado por semestre, Pandas conserva el orden cronológico
    df_alumno_unico = df_ordenado[cols_perfil].drop_duplicates().reset_index(drop=True)
    
    # Generamos el nuevo ID Subrogado (Cada versión del estudiante tiene un ID distinto)
    df_alumno_unico['id_alumno_temp'] = df_alumno_unico.index + 1
    
    # Mapear los IDs de las otras dimensiones hacia esta tabla temporal
    df_alumno_unico = df_alumno_unico.merge(dim_genero, left_on='Genero', right_on='nombre', how='left')
    df_alumno_unico = df_alumno_unico.merge(dim_estrato, left_on='Estrato', right_on='descripcion', how='left')
    df_alumno_unico = df_alumno_unico.merge(dim_ciudad, left_on='Ciudad', right_on='nombre', how='left')
    df_alumno_unico = df_alumno_unico.merge(dim_ocupacion, left_on='Ocupacion', right_on='descripcion', how='left')
    df_alumno_unico = df_alumno_unico.merge(dim_financiamiento, left_on='Financiamiento', right_on='nombre_financiamiento', how='left')
    
    # Construir la estructura final de D_Alumno
    dim_alumno = pd.DataFrame()
    dim_alumno['id_alumno'] = df_alumno_unico['id_alumno_temp']
    dim_alumno['tipo_identificacion'] = df_alumno_unico['TipoIdentificacion'].values
    dim_alumno['numero_identificacion'] = df_alumno_unico['Identificacion'].values
    dim_alumno['nombre'] = df_alumno_unico['NombreAlumno'].values
    dim_alumno['telefono'] = df_alumno_unico['Telefono'].values
    dim_alumno['direccion'] = df_alumno_unico['Direccion'].values
    dim_alumno['edad'] = df_alumno_unico['Edad'].values
    dim_alumno['id_genero'] = df_alumno_unico['id_genero'].values
    dim_alumno['id_estrato'] = df_alumno_unico['id_estrato'].values
    dim_alumno['id_ciudad'] = df_alumno_unico['id_ciudad'].values
    dim_alumno['id_ocupacion'] = df_alumno_unico['id_ocupacion'].values
    dim_alumno['id_financiamiento'] = df_alumno_unico['id_financiamiento'].values
    dim_alumno['id_fecha_nacimiento'] = fecha_a_id(df_alumno_unico['FechaNacimiento']).values
    dim_alumno['id_fecha_creacion'] = FECHA_PROCESO
    dim_alumno['id_fecha_actualizacion'] = FECHA_PROCESO
    
    # Determinar el estado "Activo": La última aparición cronológica de cada Identificación es la versión actual
    dim_alumno['activo'] = False # Por defecto todas son antiguas (False)
    # Extraemos los índices de las últimas versiones de cada cédula
    indices_activos = df_alumno_unico.drop_duplicates(subset=['Identificacion'], keep='last').index
    # A esos índices les ponemos True
    dim_alumno.loc[indices_activos, 'activo'] = True

    # 5. TABLA DE HECHOS (FACT TABLE)
    print("[*] Construyendo Tabla de Hechos (F_HechoMatricula)...")
    fact = df.copy()
    
    # Cruzar con D_Alumno por el perfil demográfico completo para traer el ID histórico exacto de ese semestre
    # Usamos el df_alumno_unico temporal que aún tiene las columnas de texto originales para hacer match
    fact = fact.merge(df_alumno_unico[['id_alumno_temp'] + cols_perfil], on=cols_perfil, how='left')
    fact = fact.rename(columns={'id_alumno_temp': 'id_alumno'})
    
    # Cruzar con el resto de dimensiones
    fact = fact.merge(dim_carrera, left_on='Carrera', right_on='nombre', how='left')
    fact = fact.merge(dim_motivo, left_on='Motivo', right_on='tipo', how='left')
    fact = fact.merge(dim_jornada, left_on='Jornada', right_on='tipo', how='left')
    fact = fact.merge(dim_semestre, left_on=['Semestre', 'ValorSemestre'], right_on=['semestre', 'valor'], how='left')

    # =========================================================================
    # LÓGICA DE NEGOCIO AVANZADA: DEUDA Y PÉRDIDA POR DESERCIÓN
    # =========================================================================
    print("    -> Calculando KPIs Financieros (Deuda Histórica y Pérdida Futura)...")
    
    # Ordenamos estrictamente por estudiante y semestre para que el cálculo histórico tenga sentido
    fact = fact.sort_values(by=['Identificacion', 'Semestre']).reset_index(drop=True)

    # A. CALCULAR VALOR DEUDA (Acumulativa con reinicio)
    def calcular_deuda_historica(df_grupo):
        deuda_acumulada = 0.0
        lista_deudas = []
        # Iteramos sobre el estado de Mora y el Valor del semestre de ese estudiante
        for mora, valor in zip(df_grupo['Mora'], df_grupo['ValorSemestre']):
            if mora == True:
                deuda_acumulada += valor  # Si no pagó, se suma a la deuda que traía
            else:
                deuda_acumulada = 0.0     # Si pagó (Mora=False), se pone al día y la deuda cae a 0
            lista_deudas.append(deuda_acumulada)
            
        df_grupo['valor_deuda'] = lista_deudas
        return df_grupo

    # Aplicamos la función agrupando por cada estudiante
    fact = fact.groupby('Identificacion', group_keys=False).apply(calcular_deuda_historica)

    # B. CALCULAR PÉRDIDA POR DESERCIÓN (Costo de oportunidad)
    def calcular_perdida(row):
        # Si NO desertó, la pérdida es cero
        if row['FechaDesercion'] == '3999-12-31':
            return 0.0
            
        # Si SÍ desertó, calculamos los semestres que le faltaban (asumiendo 10 semestres de carrera)
        semestre_actual = row['Semestre']
        valor_actual = row['ValorSemestre']
        
        semestres_faltantes = 10 - semestre_actual
        valor_futuro_perdido = 0.0
        
        # Proyección del 5% adicional por cada semestre faltante
        if semestres_faltantes > 0:
            for i in range(1, semestres_faltantes + 1):
                valor_futuro_perdido += valor_actual * (1.05 ** i)
                
        # La pérdida total para la U es la deuda que dejó
        return valor_futuro_perdido

    # Aplicamos la fórmula fila por fila
    fact['valor_perdida_por_desercion'] = fact.apply(calcular_perdida, axis=1)

    # =========================================================================
    # Construir el DataFrame Final de Hechos
    f_hechomatricula = pd.DataFrame({
        'id_alumno': fact['id_alumno'],
        'id_carrera': fact['id_carrera'],
        'id_semestre': fact['id_semestre'],
        'id_motivo': fact['id_motivo'],
        'id_jornada': fact['id_jornada'],
        'id_fecha_inicio_estudios': fecha_a_id(fact['FechaInicioEstudios']),
        'id_fecha_desercion': fecha_a_id(fact['FechaDesercion']),
        'id_fecha_inicio_semestre': fecha_a_id(fact['FechaInicioSemestre']),
        'id_fecha_final_semestre': fecha_a_id(fact['FechaFinalSemestre']),
        'promedio_semestral': fact['Promedio'],
        'cantidad_materias_perdidas': fact['CantidadMateriasPerdidas'],
        'valor_perdida_por_desercion': fact['valor_perdida_por_desercion'].round(2), # Redondear a 2 decimales
        'valor_deuda': fact['valor_deuda'].round(2),
        'id_fecha_creacion': FECHA_PROCESO,
        'id_fecha_actualizacion': FECHA_PROCESO,
        'activo': True
    })

    # 6. EXPORTAR TODAS LAS TABLAS
    print("[*] Exportando tablas a CSV...")
    dimensiones = {
        'D_Genero.csv': dim_genero,
        'D_Estrato.csv': dim_estrato,
        'D_Ciudad.csv': dim_ciudad,
        'D_Ocupacion.csv': dim_ocupacion,
        'D_Financiamiento.csv': dim_financiamiento,
        'D_Fecha.csv': dim_fecha,
        'D_Jornada.csv': dim_jornada,
        'D_Motivo.csv': dim_motivo,
        'D_Semestre.csv': dim_semestre,
        'D_Carrera.csv': dim_carrera,
        'D_Alumno.csv': dim_alumno,
        'F_HechoMatricula.csv': f_hechomatricula
    }

    for nombre_archivo, dataframe in dimensiones.items():
        ruta = os.path.join(OUTPUT_DIR, nombre_archivo)
        # Convertimos las llaves foraneas y primarias a enteros (por si Pandas las volvió float por algún nulo)
        for col in dataframe.columns:
            if col.startswith('id_') and dataframe[col].dtype == 'float64':
                dataframe[col] = dataframe[col].fillna(0).astype(int)
                
        dataframe.to_csv(ruta, index=False, encoding='utf-8')
        print(f"    -> Exportado: {nombre_archivo} ({len(dataframe)} filas)")

    print("="*60)
    print(f"[+] ¡Proceso Exitoso! Todos los archivos listos en: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()