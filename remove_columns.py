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
    
    # Eliminar las columnas disponible y ultima_actividad
    cursor.execute("""
    ALTER TABLE usuario
    DROP COLUMN disponible,
    DROP COLUMN ultima_actividad
    """)
    
    print("Columnas eliminadas correctamente de la tabla usuario")
    
    # Confirmar cambios y cerrar conexión
    conn.commit()
    cursor.close()
    conn.close()
    
except pymysql.MySQLError as e:
    print(f"Error al modificar la base de datos: {e}") 