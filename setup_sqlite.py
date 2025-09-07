from app import create_app, db
from app.models import Usuario, Clinica
from werkzeug.security import generate_password_hash
from pathlib import Path

def init_db():
    app = create_app()
    
    with app.app_context():
        # Crear todas las tablas
        db.create_all()
        
        # Verificar si ya existe el usuario admin
        admin = Usuario.query.filter_by(usuario='admin').first()
        if not admin:
            # Crear usuario administrador
            admin = Usuario(
                nombre_completo='Administrador',
                usuario='admin',
                password_hash=generate_password_hash('M3d1c@lC1!n1c#2025$Adm9&'),
                rol='admin',
                activo=True
            )
            db.session.add(admin)
            
            # Crear clínicas iniciales
            clinica1 = Clinica(nombre='Clínica 1', disponible=True)
            clinica2 = Clinica(nombre='Clínica 2', disponible=True)
            db.session.add(clinica1)
            db.session.add(clinica2)
            
            db.session.commit()
            print("Base de datos inicializada con:")
            print("Usuario administrador creado:")
            print("Usuario: admin")
            print("Contraseña: M3d1c@lC1!n1c#2025$Adm9&")
            print("\nClínicas creadas:")
            print("- Clínica 1")
            print("- Clínica 2")
        else:
            print("La base de datos ya está inicializada")
            
if __name__ == '__main__':
    # Mostrar la ubicación de la base de datos
    data_dir = Path(Path.home()) / 'ClinicaData'
    db_path = data_dir / 'clinica.db'
    print(f"La base de datos se guardará en: {db_path}")
    
    # Inicializar la base de datos
    init_db() 