from app import create_app, db
from app.models import Usuario
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # Eliminar usuario admin si existe
    admin = Usuario.query.filter_by(usuario='admin').first()
    if admin:
        db.session.delete(admin)
        db.session.commit()
        print("Usuario admin eliminado.")
    
    # Crear nuevo usuario admin
    admin = Usuario(
        nombre_completo='Administrador',
        usuario='admin',
        rol='admin'
    )
    admin.set_password('M3d1c@lC1!n1c#2025$Adm9&')
    db.session.add(admin)
    db.session.commit()
    print("Nuevo usuario admin creado con éxito.")
    print("\nCredenciales de acceso:")
    print("Usuario: admin")
    print("Contraseña: M3d1c@lC1!n1c#2025$Adm9&") 