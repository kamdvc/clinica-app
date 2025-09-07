from app import create_app, db
from app.models import Usuario
from werkzeug.security import generate_password_hash

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
        db.session.commit()
        print("Usuario administrador creado:")
        print("Usuario: admin")
        print("Contraseña: M3d1c@lC1!n1c#2025$Adm9&")
    else:
        print("El usuario administrador ya existe")

print("Base de datos inicializada correctamente") 