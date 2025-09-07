#!/usr/bin/env python3
"""
Script para aplicar la migración del campo estado a la tabla consulta
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy import text

def apply_estado_migration():
    """Aplica la migración del campo estado"""
    app = create_app()
    
    with app.app_context():
        try:
            print("Aplicando migración: agregar campo 'estado' a tabla consulta...")
            
            # Leer el archivo SQL de migración
            migration_file = os.path.join(os.path.dirname(__file__), 'add_estado_to_consulta.sql')
            with open(migration_file, 'r', encoding='utf-8') as f:
                sql_commands = f.read()
            
            # Dividir los comandos SQL (separados por punto y coma)
            commands = [cmd.strip() for cmd in sql_commands.split(';') if cmd.strip() and not cmd.strip().startswith('--')]
            
            for command in commands:
                if command:
                    print(f"Ejecutando: {command[:50]}...")
                    db.session.execute(text(command))
            
            db.session.commit()
            print("✅ Migración aplicada exitosamente")
            
            # Verificar que la migración se aplicó correctamente
            try:
                result = db.session.execute(text("SELECT COUNT(*) as total FROM consulta WHERE estado IS NOT NULL"))
                total_updated = result.fetchone()[0]
                print(f"✅ {total_updated} consultas actualizadas con campo 'estado'")
            except Exception as e:
                print(f"⚠️  No se pudo verificar la migración, pero probablemente se aplicó correctamente: {str(e)}")
                # Intentar una verificación alternativa
                try:
                    result = db.session.execute(text("PRAGMA table_info(consulta)"))
                    columns = [row[1] for row in result.fetchall()]
                    if 'estado' in columns:
                        print("✅ Campo 'estado' encontrado en la tabla consulta")
                    else:
                        print("❌ Campo 'estado' no encontrado en la tabla consulta")
                except Exception as e2:
                    print(f"⚠️  No se pudo verificar la estructura de la tabla: {str(e2)}")
            
        except Exception as e:
            print(f"❌ Error al aplicar migración: {str(e)}")
            db.session.rollback()
            raise
        finally:
            db.session.close()

if __name__ == '__main__':
    apply_estado_migration()
