#!/usr/bin/env python3
"""
Migración para SQLite: agrega la columna 'estado' a la tabla 'consulta' si no existe
y actualiza sus valores en base a la información disponible (diagnóstico + tratamiento).
"""

import os
import sys

# Asegurar que el directorio raíz del proyecto esté en sys.path para poder importar 'app'
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from app import create_app, db
from sqlalchemy import text
from sqlalchemy.exc import OperationalError


def column_exists(table_name: str, column_name: str) -> bool:
    result = db.session.execute(text(f"PRAGMA table_info({table_name})"))
    for row in result.fetchall():
        # row: (cid, name, type, notnull, dflt_value, pk)
        if str(row[1]) == column_name:
            return True
    return False


def run():
    app = create_app()
    with app.app_context():
        try:
            # Verificar si ya existe
            if column_exists('consulta', 'estado'):
                print("Campo 'estado' ya existe en 'consulta'. Nada que hacer.")
                return

            # Agregar columna 'estado'
            print("Agregando columna 'estado' a 'consulta'...")
            db.session.execute(text("ALTER TABLE consulta ADD COLUMN estado VARCHAR(20)"))

            # Inicializar valores por defecto
            print("Inicializando valores de 'estado'...")
            # Marcar como completada cuando hay diagnóstico y tratamiento no vacíos
            db.session.execute(text(
                """
                UPDATE consulta
                SET estado = 'completada'
                WHERE COALESCE(TRIM(diagnostico), '') <> ''
                  AND COALESCE(TRIM(tratamiento), '') <> ''
                """
            ))

            # El resto, en_progreso
            db.session.execute(text(
                """
                UPDATE consulta
                SET estado = 'en_progreso'
                WHERE estado IS NULL OR TRIM(estado) = ''
                """
            ))

            db.session.commit()
            # Verificación
            if column_exists('consulta', 'estado'):
                print("✅ Migración completada: columna 'estado' agregada y poblada")
            else:
                print("❌ No se encontró la columna 'estado' tras la migración")

        except OperationalError as e:
            db.session.rollback()
            print(f"❌ Error operacional al migrar: {e}")
            raise
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error al migrar: {e}")
            raise


if __name__ == '__main__':
    run()


