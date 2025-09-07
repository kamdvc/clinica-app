import os
import shutil
import sqlite3
import tarfile
from datetime import datetime
from pathlib import Path

from flask import current_app


def _get_backup_dir() -> Path:
    backup_dir_env = current_app.config.get('BACKUP_DIR')
    if backup_dir_env:
        backup_dir = Path(backup_dir_env)
    else:
        # Default next to DB file or under user home
        db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
        if db_uri.startswith('sqlite:///'):
            db_path = Path(db_uri.replace('sqlite:///', ''))
            backup_dir = db_path.parent / 'backups'
        else:
            backup_dir = Path.home() / 'ClinicaData' / 'backups'
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


def _sqlite_online_backup(src_path: Path, dst_path: Path) -> None:
    source = sqlite3.connect(str(src_path))
    try:
        dest = sqlite3.connect(str(dst_path))
        try:
            source.backup(dest)
        finally:
            dest.close()
    finally:
        source.close()


def create_sqlite_backup(include_tar: bool = True) -> Path:
    db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if not db_uri.startswith('sqlite:///'):
        raise RuntimeError('Solo se soporta backup de SQLite en esta implementación.')

    db_path = Path(db_uri.replace('sqlite:///', ''))
    if not db_path.exists():
        raise FileNotFoundError(f'No se encontró la base de datos en {db_path}')

    backup_dir = _get_backup_dir()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_name = f'backup_{timestamp}'
    sqlite_backup_path = backup_dir / f'{base_name}.db'

    # Online backup (safe while app is running)
    _sqlite_online_backup(db_path, sqlite_backup_path)

    if not include_tar:
        return sqlite_backup_path

    # Package as tar.gz
    tar_path = backup_dir / f'{base_name}.tar.gz'
    with tarfile.open(tar_path, 'w:gz') as tar:
        tar.add(sqlite_backup_path, arcname=sqlite_backup_path.name)

    return tar_path


def upload_to_google_drive(file_path: Path) -> str:
    """
    Subir a Google Drive usando una cuenta de servicio.
    Requiere variables de entorno:
      - GDRIVE_SERVICE_ACCOUNT_JSON: ruta al JSON de la cuenta de servicio
      - GDRIVE_FOLDER_ID: carpeta destino en Drive

    Nota: Para simplificar la instalación en este entorno, dejamos un stub
    que intenta usar pydrive2 si está disponible, y si no, registra una advertencia.
    """
    service_json = os.environ.get('GDRIVE_SERVICE_ACCOUNT_JSON')
    folder_id = os.environ.get('GDRIVE_FOLDER_ID')
    if not service_json or not folder_id:
        # No configurado; retornar vacío
        return ''

    try:
        from pydrive2.drive import GoogleDrive
        from pydrive2.auth import GoogleAuth

        # Configurar GoogleAuth con credenciales de servicio
        gauth = GoogleAuth(settings={
            'client_config_backend': 'service',
            'service_config': {
                'client_json_file_path': service_json,
                'scope': ['https://www.googleapis.com/auth/drive.file']
            }
        })
        gauth.ServiceAuth()
        drive = GoogleDrive(gauth)

        drive_file = drive.CreateFile({'parents': [{'id': folder_id}], 'title': file_path.name})
        drive_file.SetContentFile(str(file_path))
        drive_file.Upload()
        return drive_file.get('id') or ''
    except Exception:
        return ''


def run_backup(include_tar: bool = True, upload_drive: bool = False) -> dict:
    result = {
        'ok': False,
        'local_path': '',
        'drive_file_id': ''
    }
    path = create_sqlite_backup(include_tar=include_tar)
    result['local_path'] = str(path)
    if upload_drive:
        drive_id = upload_to_google_drive(path)
        result['drive_file_id'] = drive_id
    result['ok'] = True
    return result


