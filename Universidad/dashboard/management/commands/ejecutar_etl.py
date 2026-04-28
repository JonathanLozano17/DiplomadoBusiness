import subprocess
import os
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Ejecuta el pipeline ETL completo'
    
    def handle(self, *args, **options):
        scripts_dir = os.path.join(settings.BASE_DIR, 'scripts')
        
        scripts = [
            '01_excel_to_csv.py',
            '02_estandarizacion.py',
            '03_modelo_dimensional.py',
            '05_carga_postgresql.py',
        ]
        
        for script in scripts:
            script_path = os.path.join(scripts_dir, script)
            self.stdout.write(f'Ejecutando: {script}...')
            result = subprocess.run(['python', script_path], capture_output=True, text=True)
            if result.returncode != 0:
                self.stderr.write(f'Error en {script}: {result.stderr}')
                return
            self.stdout.write(f'Completado: {script}')
        
        self.stdout.write(self.style.SUCCESS('Pipeline ETL completado exitosamente'))