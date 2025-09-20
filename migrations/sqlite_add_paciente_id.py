#!/usr/bin/env python3
"""
Migración SQLite: Agregar campo paciente_id a SignosVitales
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy import text

def migrate_sqlite():
    app = create_app()
    with app.app_context():
        try:
            print("🔧 Iniciando migración SQLite...")
            
            # 1. Agregar columna paciente_id
            db.session.execute(text("ALTER TABLE signos_vitales ADD COLUMN paciente_id INTEGER"))
            print("✅ Columna paciente_id agregada")
            
            # 2. Poblar paciente_id para registros existentes (uniendo con consulta)
            result = db.session.execute(text("""
                UPDATE signos_vitales 
                SET paciente_id = (
                    SELECT paciente_id 
                    FROM consulta 
                    WHERE consulta.id = signos_vitales.consulta_id
                )
                WHERE consulta_id IS NOT NULL
            """))
            db.session.commit()
            print(f"✅ Campo paciente_id poblado para registros existentes")
            
            print("\n🎉 Migración SQLite completada exitosamente!")
            print("Ahora los signos vitales pueden asociarse directamente a pacientes")
            
        except Exception as e:
            print(f"❌ Error en migración: {e}")
            # En SQLite no podemos hacer rollback fácil de ALTER TABLE
            # pero podemos intentar eliminar la columna si falló después
            print("La columna paciente_id puede haberse agregado parcialmente")
            raise e

if __name__ == '__main__':
    migrate_sqlite()
