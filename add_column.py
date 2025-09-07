import pymysql
import os
from dotenv import load_dotenv

# Cargar variables de entorno
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

# Obtener credenciales de la base de datos
db_user = 'root'
db_password = 'Beder123.'
db_host = 'localhost'
db_name = 'clinica_db'

try:
    # Conectar a la base de datos
    conn = pymysql.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name
    )
    
    cursor = conn.cursor()
    
    # Verificar si la columna ya existe
    cursor.execute("""
    SELECT COUNT(*)
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = %s
    AND TABLE_NAME = 'usuario'
    AND COLUMN_NAME = 'clinica_actual_id'
    """, (db_name,))
    
    if cursor.fetchone()[0] == 0:
        # Agregar la columna clinica_actual_id
        cursor.execute("""
        ALTER TABLE usuario
        ADD COLUMN clinica_actual_id INT,
        ADD FOREIGN KEY (clinica_actual_id) REFERENCES clinica(id)
        """)
        print("Columna clinica_actual_id agregada correctamente a la tabla usuario")
    else:
        print("La columna clinica_actual_id ya existe en la tabla usuario")
    
    # Confirmar cambios y cerrar conexión
    conn.commit()
    cursor.close()
    conn.close()
    
except pymysql.MySQLError as e:
    print(f"Error al modificar la base de datos: {e}") 