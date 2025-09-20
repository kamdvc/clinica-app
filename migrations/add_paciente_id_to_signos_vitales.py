#!/usr/bin/env python3
"""
Migración: Agregar campo paciente_id a SignosVitales y hacer consulta_id nullable
Esto permite tener signos vitales iniciales sin contaminar reportes de consultas.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import SignosVitales
from sqlalchemy import text

def migrate_database():
    app = create_app()
    with app.app_context():
        try:
            # 1. Agregar columna paciente_id (nullable inicialmente)
            db.engine.execute(text(
                "ALTER TABLE signos_vitales ADD COLUMN paciente_id INTEGER"
            ))
            print("✅ Campo paciente_id agregado")
            
            # 2. Hacer consulta_id nullable
            db.engine.execute(text(
                "ALTER TABLE signos_vitales MODIFY COLUMN consulta_id INTEGER NULL"
            ))
            print("✅ Campo consulta_id ahora es nullable")
            
            # 3. Poblar paciente_id para registros existentes
            db.engine.execute(text("""
                UPDATE signos_vitales sv
                JOIN consulta c ON sv.consulta_id = c.id
                SET sv.paciente_id = c.paciente_id
                WHERE sv.consulta_id IS NOT NULL
            """))
            print("✅ Campo paciente_id poblado para registros existentes")
            
            # 4. Agregar foreign key constraint
            db.engine.execute(text(
                "ALTER TABLE signos_vitales ADD FOREIGN KEY (paciente_id) REFERENCES paciente(id)"
            ))
            print("✅ Foreign key constraint agregado")
            
            print("\n🎉 Migración completada exitosamente!")
            print("Ahora los signos vitales pueden existir sin consulta (no contaminan reportes)")
            
        except Exception as e:
            print(f"❌ Error en migración: {e}")
            print("Revertiendo cambios...")
            try:
                # Intentar revertir cambios si es posible
                db.engine.execute(text("ALTER TABLE signos_vitales DROP COLUMN paciente_id"))
            except:
                pass
            raise e

if __name__ == '__main__':
    migrate_database()

