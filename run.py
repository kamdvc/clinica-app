import os
from app import create_app, db
from app import models  # Importa modelos para que Flask-Migrate los detecte
from flask import current_app
import click

# Set Flask environment variables
os.environ['FLASK_ENV'] = 'development'

app = create_app()

def init_db():
    with app.app_context():
        # Importar todos los modelos aquí
        from app.models import Usuario, Paciente, Consulta, SignosVitales, Clinica
        
        # Crear todas las tablas
        db.create_all()
        
        print("Base de datos inicializada.")

@app.cli.command("init-db")
def init_db_command():
    """Inicializar la base de datos."""
    init_db()
    print("Base de datos inicializada!")


@app.cli.command('backup-db')
@click.option('--no-tar', is_flag=True, default=False, help='No crear archivo tar.gz, solo .db')
@click.option('--upload-drive', is_flag=True, default=False, help='Subir a Google Drive si está configurado')
def backup_db_command(no_tar: bool, upload_drive: bool):
    """Crear un respaldo de la base de datos SQLite."""
    from app.utils.backup import run_backup
    include_tar = not no_tar
    result = run_backup(include_tar=include_tar, upload_drive=upload_drive)
    msg = f"Backup OK. Local: {result['local_path']}"
    if result.get('drive_file_id'):
        msg += f" | Drive ID: {result['drive_file_id']}"
    print(msg)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', load_dotenv=True)
