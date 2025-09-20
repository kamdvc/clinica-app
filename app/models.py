from datetime import datetime, timedelta
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from flask import current_app
from app import db, login_manager
import random
import string

@login_manager.user_loader
def load_user(id):
    return Usuario.query.get(int(id))

class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre_completo = db.Column(db.String(100), nullable=False)
    usuario = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=True)
    password_hash = db.Column(db.String(128), nullable=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    activo = db.Column(db.Boolean, default=True)
    rol = db.Column(db.String(20), default='medico')  # medico, medico_supervisor, admin
    clinica_actual_id = db.Column(db.Integer, db.ForeignKey('clinica.id'))  # Para médicos: indica en qué clínica están atendiendo
    clinica_actual = db.relationship('Clinica', foreign_keys=[clinica_actual_id])
    consultas = db.relationship('Consulta', backref='medico', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_reset_password_token(self, expires_in=1800):  # 30 minutos por defecto
        """Genera un token seguro para reset de contraseña que expira en 'expires_in' segundos"""
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps({'reset_password': self.id}, salt='password-reset-salt')
    
    @staticmethod
    def verify_reset_password_token(token, expires_in=1800):
        """Verifica un token de reset de contraseña y retorna el usuario si es válido"""
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            # max_age en segundos (30 minutos = 1800 segundos)
            data = s.loads(token, salt='password-reset-salt', max_age=expires_in)
        except:
            return None
        return Usuario.query.get(data['reset_password'])
    
    def __repr__(self):
        return f'<Usuario {self.usuario}>'

class Paciente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre_completo = db.Column(db.String(100), nullable=False)
    edad = db.Column(db.Integer, nullable=False)
    sexo = db.Column(db.String(10), nullable=False)  # Masculino, Femenino
    expediente = db.Column(db.Boolean, default=False)
    direccion = db.Column(db.String(200))
    telefono = db.Column(db.String(20))
    dni = db.Column(db.String(20), unique=True, nullable=True)
    fecha_nacimiento = db.Column(db.Date)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    # Campos de datos generales
    estado_civil = db.Column(db.String(50))
    religion = db.Column(db.String(50))
    escolaridad = db.Column(db.String(50))
    ocupacion = db.Column(db.String(100))
    procedencia = db.Column(db.String(100))
    numero_expediente = db.Column(db.String(50))
    consultas = db.relationship('Consulta', backref='paciente', lazy='dynamic')
    signos_vitales_iniciales = db.relationship('SignosVitales', foreign_keys='SignosVitales.paciente_id', backref='paciente_inicial', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'nombre_completo': self.nombre_completo,
            'edad': self.edad,
            'genero': self.sexo,
            'dni': self.dni
        }

    def __repr__(self):
        return f'<Paciente {self.nombre_completo}>'

class SignosVitales(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    presion_arterial = db.Column(db.String(20))
    frecuencia_cardiaca = db.Column(db.Integer)
    frecuencia_respiratoria = db.Column(db.Integer)
    temperatura = db.Column(db.Float)
    saturacion = db.Column(db.Integer)
    glucosa = db.Column(db.Integer)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    paciente_id = db.Column(db.Integer, db.ForeignKey('paciente.id'), nullable=True)  # Para signos iniciales sin consulta
    consulta_id = db.Column(db.Integer, db.ForeignKey('consulta.id'), nullable=True)  # Ahora es opcional
    
    def to_dict(self):
        return {
            'presion_arterial': self.presion_arterial,
            'frecuencia_cardiaca': self.frecuencia_cardiaca,
            'frecuencia_respiratoria': self.frecuencia_respiratoria,
            'temperatura': self.temperatura,
            'saturacion': self.saturacion,
            'glucosa': self.glucosa
        }

    def __repr__(self):
        return f'<SignosVitales {self.id}>'

class Consulta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('paciente.id'))
    tipo_consulta = db.Column(db.String(50))  # Primera consulta, Seguimiento, Medicamento
    clinica_id = db.Column(db.Integer, db.ForeignKey('clinica.id'))
    medico_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    fecha_consulta = db.Column(db.DateTime, default=datetime.utcnow)
    estado = db.Column(db.String(20), default='en_progreso')  # en_progreso, completada
    
    # Campos de motivo de consulta
    motivo_consulta = db.Column(db.Text)
    historia_enfermedad = db.Column(db.Text)
    revision_sistemas = db.Column(db.Text)
    
    # Antecedentes gineco-obstetricos
    gestas = db.Column(db.String(10))
    partos = db.Column(db.String(10))
    abortos = db.Column(db.String(10))
    hijos_vivos = db.Column(db.String(10))
    hijos_muertos = db.Column(db.String(10))
    fecha_ultima_regla = db.Column(db.Date)
    antecedentes = db.Column(db.Text)
    
    # Examen físico
    presion_arterial = db.Column(db.String(20))
    frecuencia_respiratoria = db.Column(db.String(10))
    temperatura = db.Column(db.String(10))
    peso = db.Column(db.String(10))
    talla = db.Column(db.String(10))
    frecuencia_cardiaca = db.Column(db.String(10))
    saturacion_oxigeno = db.Column(db.String(10))
    imc = db.Column(db.String(10))
    
    # Campos existentes
    diagnostico = db.Column(db.Text)
    laboratorio = db.Column(db.Text)  # Exámenes de laboratorio
    tratamiento = db.Column(db.Text)  # Medicamentos recetados
    indicaciones = db.Column(db.Text)  # Indicaciones adicionales para el paciente
    signos_vitales = db.relationship('SignosVitales', backref='consulta', uselist=False)
    
    def __repr__(self):
        return f'<Consulta {self.id}>'

class Clinica(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    disponible = db.Column(db.Boolean, default=True)
    consultas = db.relationship('Consulta', backref='clinica', lazy='dynamic')
    
    def __repr__(self):
        return f'<Clinica {self.nombre}>'

class HistorialRoles(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    rol_anterior = db.Column(db.String(50))
    rol_nuevo = db.Column(db.String(50))
    fecha_cambio = db.Column(db.DateTime, default=datetime.utcnow)

    admin = db.relationship('Usuario', foreign_keys=[admin_id], backref='cambios_realizados')
    usuario = db.relationship('Usuario', foreign_keys=[usuario_id], backref='historial_roles')

    def __repr__(self):
        return f'<HistorialRoles {self.id}>'

class HistorialAsignacionClinica(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    medico_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    clinica_anterior_id = db.Column(db.Integer, db.ForeignKey('clinica.id'), nullable=True)
    clinica_nueva_id = db.Column(db.Integer, db.ForeignKey('clinica.id'), nullable=True)
    fecha_cambio = db.Column(db.DateTime, default=datetime.utcnow)

    admin = db.relationship('Usuario', foreign_keys=[admin_id])
    medico = db.relationship('Usuario', foreign_keys=[medico_id])
    clinica_anterior = db.relationship('Clinica', foreign_keys=[clinica_anterior_id])
    clinica_nueva = db.relationship('Clinica', foreign_keys=[clinica_nueva_id])

    def __repr__(self):
        return f'<HistorialAsignacionClinica {self.id}>'

class CodigoVerificacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    codigo = db.Column(db.String(6), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # 'password_change' o 'email_verification'
    intentos = db.Column(db.Integer, default=0)
    usado = db.Column(db.Boolean, default=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_expiracion = db.Column(db.DateTime, nullable=False)
    
    usuario = db.relationship('Usuario', backref='codigos_verificacion')
    
    @staticmethod
    def generar_codigo():
        """Genera un código de 6 dígitos"""
        return ''.join(random.choices(string.digits, k=6))
    
    @staticmethod
    def crear_codigo_verificacion(usuario_id, tipo='password_change', duracion_minutos=15):
        """Crea un nuevo código de verificación"""
        # Invalidar códigos anteriores del mismo tipo para este usuario
        CodigoVerificacion.query.filter_by(
            usuario_id=usuario_id, 
            tipo=tipo, 
            usado=False
        ).update({'usado': True})
        
        codigo = CodigoVerificacion.generar_codigo()
        expiracion = datetime.utcnow() + timedelta(minutes=duracion_minutos)
        
        nuevo_codigo = CodigoVerificacion(
            usuario_id=usuario_id,
            codigo=codigo,
            tipo=tipo,
            fecha_expiracion=expiracion
        )
        
        db.session.add(nuevo_codigo)
        db.session.commit()
        
        return nuevo_codigo
    
    def es_valido(self):
        """Verifica si el código es válido"""
        return (not self.usado and 
                self.intentos < 3 and 
                datetime.utcnow() < self.fecha_expiracion)
    
    def incrementar_intento(self):
        """Incrementa el contador de intentos"""
        self.intentos += 1
        if self.intentos >= 3:
            self.usado = True
        db.session.commit()
    
    def marcar_como_usado(self):
        """Marca el código como usado"""
        self.usado = True
        db.session.commit()
    
    def __repr__(self):
        return f'<CodigoVerificacion {self.codigo}>'


class VerificationCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    code = db.Column(db.String(4), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def is_expired(self):
        """Check if the verification code is expired (valid for 30 minutes)."""
        return datetime.utcnow() > self.timestamp + timedelta(minutes=30)