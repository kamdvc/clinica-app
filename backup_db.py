import os
import shutil
from datetime import datetime
from pathlib import Path

def create_backup():
    # Crear directorio de respaldos si no existe
    backup_dir = Path('backups')
    backup_dir.mkdir(exist_ok=True)
    
    # Verificar si existe la base de datos
    db_file = Path('app.db')
    if not db_file.exists():
        print("No se encontró la base de datos app.db")
        return
    
    # Crear nombre del archivo de respaldo con fecha
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = backup_dir / f'app_backup_{timestamp}.db'
    
    # Copiar la base de datos
    shutil.copy2('app.db', backup_file)
    print(f"Respaldo creado exitosamente: {backup_file}")

def restore_latest_backup():
    backup_dir = Path('backups')
    if not backup_dir.exists() or not backup_dir.is_dir():
        print("No se encontró el directorio de respaldos")
        return
    
    # Buscar el respaldo más reciente
    backups = list(backup_dir.glob('app_backup_*.db'))
    if not backups:
        print("No se encontraron respaldos")
        return
    
    latest_backup = max(backups, key=lambda x: x.stat().st_mtime)
    
    # Verificar si hay una base de datos actual
    db_file = Path('app.db')
    if db_file.exists():
        # Hacer respaldo de la base actual antes de restaurar
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        current_backup = backup_dir / f'app_before_restore_{timestamp}.db'
        shutil.copy2('app.db', current_backup)
        print(f"Se creó respaldo de la base de datos actual: {current_backup}")
    
    # Restaurar el respaldo más reciente
    shutil.copy2(latest_backup, 'app.db')
    print(f"Base de datos restaurada desde: {latest_backup}")

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'restore':
        restore_latest_backup()
    else:
        create_backup() 