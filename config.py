import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# Crear directorio para datos persistentes
data_dir = Path(os.path.expanduser('~')) / 'ClinicaData'
data_dir.mkdir(exist_ok=True)

class Config:
    SECRET_KEY = 'dev-secret-key-change-in-production'
    # Guardar la base de datos en un directorio persistente
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + str(data_dir / 'clinica.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Configuración CSRF
    WTF_CSRF_ENABLED = True
    
    # Configuración de Flask-Mail
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@clinica.com')
    
    # OAuth Google
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
    OAUTHLIB_INSECURE_TRANSPORT = '1'  # quitar en producción

    # Directorio de backups
    BACKUP_DIR = os.environ.get('BACKUP_DIR', str(data_dir / 'backups'))

    # reCAPTCHA (opcional)
    RECAPTCHA_SECRET_KEY = os.environ.get('RECAPTCHA_SECRET_KEY', '')