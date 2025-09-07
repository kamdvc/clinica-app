from app import create_app, db
from app.models import Paciente
from sqlalchemy import text

def add_columns():
    app = create_app()
    with app.app_context():
        # Crear las nuevas columnas
        with db.engine.connect() as conn:
            conn.execute(text('ALTER TABLE paciente ADD COLUMN estado_civil VARCHAR(50)'))
            conn.execute(text('ALTER TABLE paciente ADD COLUMN religion VARCHAR(50)'))
            conn.execute(text('ALTER TABLE paciente ADD COLUMN escolaridad VARCHAR(50)'))
            conn.execute(text('ALTER TABLE paciente ADD COLUMN ocupacion VARCHAR(100)'))
            conn.execute(text('ALTER TABLE paciente ADD COLUMN procedencia VARCHAR(100)'))
            conn.execute(text('ALTER TABLE paciente ADD COLUMN numero_expediente VARCHAR(50)'))
            conn.commit()
            
        print("Columnas agregadas exitosamente")

if __name__ == '__main__':
    add_columns() 