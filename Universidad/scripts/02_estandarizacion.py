import pandas as pd
import numpy as np
import unicodedata
import re
import os

# =============================================================================
# CONFIGURACIÓN DE RUTAS
# =============================================================================
# Ruta del insumo CSV a estandarizar
INPUT_CSV  = 'data/processed/Dataset_Historico_60000_Final_Corregido.csv'
# Ruta a postular el CSV estandarizado
OUTPUT_CSV = 'data/processed/dataset_estandarizado.csv'

# =============================================================================
# FUNCIONES DE TRANSFORMACIÓN
# =============================================================================
def limpiar_texto(texto, es_direccion=False):
    """
    Estandariza campos de texto: a minúscula, cambia Ñ, sin tildes.
    Si es dirección, conserva los caracteres especiales como # y -.
    """
    # Con Pandas, detecta valores nulo y los devuelve tal cual
    if pd.isna(texto):
        return texto
    
    # Pasar a minuscula y quitar espacios
    texto = str(texto).strip().lower()
    
    #Reemplazar la 'ñ' por la 'n'
    texto = texto.replace('ñ', 'n')
    
    # Quitar tildes, descomponiendo la letra con tilde en dos caracteres separados para luego eliminar la tilde.
    texto = ''.join((c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn'))
    
    # Si NO es dirección, quitamos los caracteres especiales con un regex
    # (secuencia de caracteres que forma un patrón de búsqueda. Sirve para encontrar, extraer o reemplazar partes de un texto.)
    if not es_direccion:
        texto = re.sub(r'[^a-z0-9\s]', '', texto)
    
    return texto

# =============================================================================
# PROCESO PRINCIPAL
# =============================================================================
def main():
    print("="*50)
    print(" PASO 2: ESTANDARIZACIÓN, DEDUPLICACIÓN Y LIMPIEZA DE DATOS")
    print("="*50)
    
    # Valida la existencia del archivo CSV a estandarizar
    if not os.path.exists(INPUT_CSV):
        print(f"[ERROR] No se encontró el archivo origen en: {INPUT_CSV}")
        return

    # Lectura del archivo insumo CSV
    print(f"[*] Leyendo archivo crudo: {INPUT_CSV}")
    df = pd.read_csv(INPUT_CSV)
    total_inicial = len(df)
    
    print("[*] Aplicando reglas de estandarización...")
    
    # Arreglo específico para el Teléfono (quitar el .0 que pone Pandas)
    if 'Telefono' in df.columns:
        # Convertimos a string y borramos el '.0' del final 
        df['Telefono'] = df['Telefono'].astype(str).str.replace(r'\.0$', '', regex=True)
        # Reemplazar la cadena 'nan' por un nulo real de numpy para que la imputación funcione
        df['Telefono'] = df['Telefono'].replace('nan', pd.NA)

    # 1. CALIDAD DE DATOS: IDENTIFICAR ANOMALÍAS
    print("[*] Identificando anomalías lógicas (Edades o valores irreales)...")
    # Volvemos nulos los valores absurdos para que esa fila pierda "puntaje" en la deduplicación con un Boolean Indexing
    
    # Busca todas las filas donde la edad sea menor a 14 o mayor a 60, y en la columna 'Edad' les asigna NaN
    df.loc[(df['Edad'] < 14) | (df['Edad'] > 60), 'Edad'] = np.nan
    # Busca todas las filas donde el valor del semestre sea igual o menor a 0, y les asigna NaN
    df.loc[df['ValorSemestre'] <= 0, 'ValorSemestre'] = np.nan

    # 2. IMPUTACIÓN HISTÓRICA
    print("[*] Rescatando datos faltantes (Imputación por Identificación)...")
    # Columnas que no cambian de un semestre a otro para una misma persona
    columnas_estaticas = ['NombreAlumno', 'Telefono', 'Direccion', 'Ciudad', 
                          'Genero', 'FechaNacimiento', 'TipoIdentificacion']
    
    # Rellenamos nulos hacia adelante y hacia atrás basados en el historial del mismo estudiante
    
    # Agrupa los datos por estudian te (Identificacion), si le falta otros dato (ciudad u otro), busca
    # en sus otros semestres y rellena el dato faltante hacia adelante y hacia atras
    # Utiliza una funcion lambda (una sola linea)
    df[columnas_estaticas] = df.groupby('Identificacion')[columnas_estaticas].transform(lambda x: x.ffill().bfill())

    # 3. DEDUPLICACIÓN INTELIGENTE
    print("[*] Aplicando deduplicación inteligente...")
    # Contamos cuántos datos VÁLIDOS (no nulos) tiene cada fila y se asigna en una nueva columna
    df['datos_validos'] = df.notna().sum(axis=1)
    
    # Ordenamos: primero por estudiante, luego semestre y finalmente por la fila que tenga más datos válidos
    df = df.sort_values(by=['Identificacion', 'Semestre', 'datos_validos'], ascending=[True, True, False])
    
    # Eliminamos duplicados conservando solo el primer registro (el más completo)
    df = df.drop_duplicates(subset=['Identificacion', 'Semestre'], keep='first')
    df = df.drop(columns=['datos_validos']) # Borramos la columna temporal
    
    total_final = len(df)
    print(f"    -> Registros eliminados (Basura duplicada): {total_inicial - total_final}")

    # 4. LIMPIEZA DE TEXTOS
    print("[*] Aplicando reglas de estandarización de texto (Minúsculas, sin tildes)...")
    
    columnas_fecha = ['FechaInicioEstudios', 'FechaDesercion', 'FechaInicioSemestre', 
                      'FechaFinalSemestre', 'FechaNacimiento']
    columnas_numericas = ['Edad', 'Estrato', 'Semestre'] 
    columnas_financieras_academicas = ['Promedio', 'ValorSemestre']
    
    # Filtrar las columnas del DataFrame por el tipo de dato de texto
    columnas_texto = df.select_dtypes(include=['object', 'string']).columns.tolist()
    
    # Mediante un list comprehension, itera sobre las listas de columnas de texto y crea una lista nueva omitiendo
    # las que son de fecha
    columnas_texto = [col for col in columnas_texto if col not in columnas_fecha]

    for col in columnas_texto:
        if col == 'Direccion':
            # Le decimos a la función que es dirección para que no borre el # y el -
            df[col] = df[col].apply(lambda x: limpiar_texto(x, es_direccion=True))
        else:
            df[col] = df[col].apply(lambda x: limpiar_texto(x, es_direccion=False))
    
    # 5. MANEJO DE NULOS (Residuales)
    print("[*] Manejando valores nulos y vacíos residuales...")
    
    # Para las columnas con fecha con valores nulos le asigna el valor "3999-12-31" predeterminado para 
    # detectar aquellos alumnos que no han desertado 
    for col in columnas_fecha:
        if col in df.columns:
            df[col] = df[col].fillna('3999-12-31')
    
    # Para las columnas de texto, se les asigna el valor 'sin definir'        
    for col in columnas_texto:
        df[col] = df[col].fillna('sin definir')
        df[col] = df[col].replace('', 'sin definir')
    
    # Para las columnas numericas enteras, se les asigna el valor '-1'
    for col in columnas_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df[col] = df[col].fillna(-1).astype(int)

    # Para las columnas numericas decimales, se les asigna el valor '0.0'
    for col in columnas_financieras_academicas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

    # 6. EXPORTAR
    print(f"[*] Guardando dataset estandarizado...")
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8')
    
    print(f"[+] ¡Éxito! Archivo estandarizado generado en: {OUTPUT_CSV}")
    print(f"[+] Total de registros finales listos para el modelo dimensional: {total_final}")
    print("="*50)

if __name__ == "__main__":
    main()