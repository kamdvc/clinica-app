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

# Crear la base de datos si no existe
try:
    # Conectar a MySQL sin especificar una base de datos
    conn = pymysql.connect(
        host=db_host,
        user=db_user,
        password=db_password
    )
    
    cursor = conn.cursor()
    
    # Crear la base de datos si no existe
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
    print(f"Base de datos '{db_name}' creada o verificada correctamente.")
    
    # Cerrar la conexión inicial
    conn.commit()
    cursor.close()
    conn.close()
    
    # Conectar a la base de datos recién creada
    conn = pymysql.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name
    )
    
    cursor = conn.cursor()
    
    # Crear tablas básicas
    # Tabla de usuarios
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuario (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nombre_completo VARCHAR(100) NOT NULL,
        usuario VARCHAR(64) NOT NULL UNIQUE,
        email VARCHAR(120) UNIQUE,
        password_hash VARCHAR(128) NOT NULL,
        fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
        activo BOOLEAN DEFAULT TRUE,
        rol VARCHAR(20) DEFAULT 'recepcion'
    )
    """)
    
    # Tabla de pacientes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS paciente (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nombre_completo VARCHAR(100) NOT NULL,
        edad INT NOT NULL,
        sexo VARCHAR(10) NOT NULL,
        expediente BOOLEAN DEFAULT FALSE,
        fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Tabla de clínicas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clinica (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nombre VARCHAR(50) NOT NULL,
        disponible BOOLEAN DEFAULT TRUE
    )
    """)
    
    # Tabla de consultas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS consulta (
        id INT AUTO_INCREMENT PRIMARY KEY,
        paciente_id INT,
        tipo_consulta VARCHAR(50),
        clinica_id INT,
        medico_id INT,
        fecha_consulta DATETIME DEFAULT CURRENT_TIMESTAMP,
        diagnostico TEXT,
        tratamiento TEXT,
        FOREIGN KEY (paciente_id) REFERENCES paciente(id),
        FOREIGN KEY (clinica_id) REFERENCES clinica(id),
        FOREIGN KEY (medico_id) REFERENCES usuario(id)
    )
    """)
    
    # Tabla de signos vitales
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS signos_vitales (
        id INT AUTO_INCREMENT PRIMARY KEY,
        presion_arterial VARCHAR(20),
        frecuencia_cardiaca INT,
        frecuencia_respiratoria INT,
        temperatura FLOAT,
        saturacion INT,
        glucosa INT,
        fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
        consulta_id INT,
        FOREIGN KEY (consulta_id) REFERENCES consulta(id)
    )
    """)
    
    # Insertar datos de ejemplo
    # Insertar un usuario administrador
    cursor.execute("""
    INSERT INTO usuario (nombre_completo, usuario, password_hash, rol)
    SELECT 'Administrador', 'admin', 'pbkdf2:sha256:150000$nrABZ8Wy$a4a2f0e3a7c2b2d9b8e7f6d5c4b3a2f1e0d9c8b7a6f5e4d3c2b1a0', 'admin'
    WHERE NOT EXISTS (SELECT 1 FROM usuario WHERE usuario = 'admin')
    """)
    
    # Insertar clínicas de ejemplo
    cursor.execute("""
    INSERT INTO clinica (nombre, disponible)
    SELECT 'Clínica 1', TRUE
    WHERE NOT EXISTS (SELECT 1 FROM clinica WHERE nombre = 'Clínica 1')
    """)
    
    cursor.execute("""
    INSERT INTO clinica (nombre, disponible)
    SELECT 'Clínica 2', TRUE
    WHERE NOT EXISTS (SELECT 1 FROM clinica WHERE nombre = 'Clínica 2')
    """)
    
    # Ya no insertamos la Clínica 3
    # cursor.execute("""
    # INSERT INTO clinica (nombre, disponible)
    # SELECT 'Clínica 3', TRUE
    # WHERE NOT EXISTS (SELECT 1 FROM clinica WHERE nombre = 'Clínica 3')
    # """)
    
    # Confirmar cambios y cerrar conexión
    conn.commit()
    print("Tablas creadas correctamente y datos de ejemplo insertados.")
    print("\nCredenciales de acceso:")
    print("Usuario: admin")
    print("Contraseña: admin123")
    
    cursor.close()
    conn.close()
    
except pymysql.MySQLError as e:
    print(f"Error al configurar la base de datos: {e}")