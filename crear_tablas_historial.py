#!/usr/bin/env python3
"""
Script para crear las tablas de historial en la base de datos existente.
Ejecutar desde el directorio raíz del proyecto: python crear_tablas_historial.py
"""

import sqlite3
import os
from datetime import datetime

def crear_tablas_historial():
    # Buscar el archivo de base de datos
    db_files = ['app.db', 'clinica.db', 'database.db']
    db_path = None
    
    for db_file in db_files:
        if os.path.exists(db_file):
            db_path = db_file
            break
    
    if not db_path:
        print("No se encontró el archivo de base de datos. Archivos buscados:", db_files)
        print("Por favor, verifica que estés en el directorio correcto del proyecto.")
        return False
    
    print(f"Conectando a la base de datos: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar si las tablas ya existen
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='historial_roles'")
        tabla_roles_existe = cursor.fetchone() is not None
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='historial_asignacion_clinica'")
        tabla_clinicas_existe = cursor.fetchone() is not None
        
        if tabla_roles_existe and tabla_clinicas_existe:
            print("Las tablas de historial ya existen en la base de datos.")
            return True
        
        print("Creando tablas de historial...")
        
        # Crear tabla historial_roles
        if not tabla_roles_existe:
            cursor.execute('''
                CREATE TABLE historial_roles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin_id INTEGER NOT NULL,
                    usuario_id INTEGER NOT NULL,
                    rol_anterior VARCHAR(50),
                    rol_nuevo VARCHAR(50),
                    fecha_cambio DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (admin_id) REFERENCES usuario (id),
                    FOREIGN KEY (usuario_id) REFERENCES usuario (id)
                )
            ''')
            print("✓ Tabla 'historial_roles' creada exitosamente.")
        else:
            print("✓ Tabla 'historial_roles' ya existe.")
        
        # Crear tabla historial_asignacion_clinica
        if not tabla_clinicas_existe:
            cursor.execute('''
                CREATE TABLE historial_asignacion_clinica (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin_id INTEGER NOT NULL,
                    medico_id INTEGER NOT NULL,
                    clinica_anterior_id INTEGER,
                    clinica_nueva_id INTEGER,
                    fecha_cambio DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (admin_id) REFERENCES usuario (id),
                    FOREIGN KEY (medico_id) REFERENCES usuario (id),
                    FOREIGN KEY (clinica_anterior_id) REFERENCES clinica (id),
                    FOREIGN KEY (clinica_nueva_id) REFERENCES clinica (id)
                )
            ''')
            print("✓ Tabla 'historial_asignacion_clinica' creada exitosamente.")
        else:
            print("✓ Tabla 'historial_asignacion_clinica' ya existe.")
        
        # Confirmar los cambios
        conn.commit()
        
        # Verificar que las tablas se crearon correctamente
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name='historial_roles' OR name='historial_asignacion_clinica')")
        tablas_creadas = cursor.fetchall()
        
        print(f"\nTablas verificadas en la base de datos: {[tabla[0] for tabla in tablas_creadas]}")
        print("\n✅ ¡Migración completada exitosamente!")
        print("\nAhora puedes reiniciar tu aplicación Flask y la página de historial debería funcionar correctamente.")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Error al crear las tablas: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("=== Creación de Tablas de Historial ===")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 40)
    
    exito = crear_tablas_historial()
    
    if exito:
        print("\n🎉 Proceso completado exitosamente.")
        print("\nPasos siguientes:")
        print("1. Reinicia tu aplicación Flask")
        print("2. Navega a 'Historial de Cambios' en el menú")
        print("3. Haz algunos cambios de roles o asignaciones de clínicas para probar el sistema")
    else:
        print("\n❌ El proceso falló. Revisa los errores anteriores.")

