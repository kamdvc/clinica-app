from app import create_app, db
from app.models import Consulta

def apply_changes():
    app = create_app()
    with app.app_context():
        # Recrear la tabla consulta con los nuevos campos
        db.drop_all()
        db.create_all()
        print("Cambios aplicados exitosamente!")

if __name__ == '__main__':
    apply_changes() 