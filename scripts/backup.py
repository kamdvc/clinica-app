import os
import shutil
import datetime
from pathlib import Path
import sys

# Agrega el directorio raíz del proyecto al sys.path
# para que podamos importar módulos de la aplicación como 'config'.
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from config import Config
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

def authenticate_gdrive():
    """
    Autentica con Google Drive usando un flujo de servidor web local.
    """
    gauth = GoogleAuth()
    # Intenta cargar credenciales guardadas
    gauth.LoadCredentialsFile(project_root / "credentials.json")
    if gauth.credentials is None:
        # Autentica si no hay credenciales o están inválidas
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        # Refresca las credenciales si han expirado
        gauth.Refresh()
    else:
        # Inicializa las credenciales si ya estaban autorizadas
        gauth.Authorize()
    
    # Guarda las credenciales actualizadas para futuros usos
    gauth.SaveCredentialsFile(project_root / "credentials.json")
    
    return GoogleDrive(gauth)

def upload_to_drive(drive, file_path, folder_name="ClinicaBackups"):
    """
    Sube un archivo a una carpeta específica en Google Drive.
    """
    try:
        # Busca la carpeta de backups
        folder_query = f"title='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        folder_list = drive.ListFile({'q': folder_query}).GetList()
        
        if not folder_list:
            # Crea la carpeta si no existe
            print(f"La carpeta '{folder_name}' no existe, creándola...")
            folder_metadata = {
                'title': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = drive.CreateFile(folder_metadata)
            folder.Upload()
            folder_id = folder['id']
        else:
            folder_id = folder_list[0]['id']

        # Sube el archivo de backup a la carpeta
        file_name = os.path.basename(file_path)
        gfile = drive.CreateFile({'title': file_name, 'parents': [{'id': folder_id}]})
        gfile.SetContentFile(file_path)
        gfile.Upload()
        print(f"Archivo '{file_name}' subido exitosamente a la carpeta '{folder_name}' en Google Drive.")
    
    except Exception as e:
        print(f"Error al subir el archivo a Google Drive: {e}")


def create_backup():
    """
    Crea una copia de seguridad de la base de datos SQLite y la sube a Google Drive.
    """
    # Extrae la ruta del archivo de la base de datos desde la URI de conexión.
    db_uri = Config.SQLALCHEMY_DATABASE_URI
    if not db_uri.startswith('sqlite:///'):
        print("Error: El script de backup actualmente solo soporta bases de datos SQLite.")
        return

    db_path_str = db_uri.replace('sqlite:///', '')
    db_path = Path(db_path_str)

    if not db_path.exists():
        print(f"Error: No se encontró la base de datos en '{db_path}'.")
        return

    # Define el directorio de backups y el nombre del archivo.
    backup_dir = Path(Config.BACKUP_DIR)
    backup_dir.mkdir(parents=True, exist_ok=True)  # Asegura que el directorio exista

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_filename = f"backup_{timestamp}.db"
    backup_path = backup_dir / backup_filename

    backup_file_path = None
    try:
        # Copia el archivo de la base de datos al directorio de backups.
        shutil.copy2(db_path, backup_path)
        backup_file_path = backup_path
        print(f"Copia de seguridad creada exitosamente en '{backup_path}'.")
    except Exception as e:
        print(f"Error al crear la copia de seguridad: {e}")
        return # No continuar si la copia local falla

    if backup_file_path:
        print("Iniciando subida a Google Drive...")
        drive = authenticate_gdrive()
        upload_to_drive(drive, backup_file_path)


if __name__ == "__main__":
    create_backup()
