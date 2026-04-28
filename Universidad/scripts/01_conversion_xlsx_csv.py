import pandas as pd
import os

# =============================================================================
# CONFIGURACIÓN DE RUTAS
# =============================================================================
# Subimos un nivel (..) desde 'scripts' para entrar a 'data/input'
# Ruta Excel dataset
INPUT_EXCEL = 'data/input/Dataset_Historico_60000_Final_Corregido.xlsx'
# Ruta a guardar Csv a generar con que nombre
OUTPUT_CSV  = 'data/processed/Dataset_Historico_60000_Final_Corregido.csv'

# Funcion principal
def main():
    print("="*50)
    print(" PASO 1: CONVERSIÓN DE EXCEL A CSV")
    print("="*50)
    
    # 1. Verificar si el archivo origen existe
    if not os.path.exists(INPUT_EXCEL):
        print(f"[ERROR] No se encontró el archivo Excel en la ruta: {INPUT_EXCEL}")
        print("Asegúrate de que el nombre del archivo y la carpeta sean correctos.")
        return

    try:
        # 2. Leer el archivo Excel
        print(f"[*] Leyendo el archivo Excel... (Esto puede tardar unos segundos)")
        df = pd.read_excel(INPUT_EXCEL)
        print(f"[+] Archivo leído exitosamente. Contiene {len(df)} registros y {len(df.columns)} columnas.")
        
        # 3. Convertir y guardar como CSV
        print(f"[*] Convirtiendo y guardando como archivo CSV...")
        # Usamos index=False para que Pandas no agregue una columna extra con los números de fila
        # Usamos encoding='utf-8' para no perder de momento tildes o caracteres especiales
        df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8')
        
        print(f"[+] ¡Éxito! Archivo CSV generado en: {OUTPUT_CSV}")
        print("="*50)
        
    except Exception as e:
        print(f"[ERROR] Ocurrió un problema durante la ejecución: {e}")

if __name__ == "__main__":
    main()