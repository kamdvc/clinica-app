from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

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
    rol = db.Column(db.String(20), default='recepcion')  # recepcion, medico, admin
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<Usuario {self.usuario}>'

class Paciente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre_completo = db.Column(db.String(100), nullable=False)
    edad = db.Column(db.Integer, nullable=False)
    sexo = db.Column(db.String(10), nullable=False)  # Masculino, Femenino
    expediente = db.Column(db.Boolean, default=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    consultas = db.relationship('Consulta', backref='paciente', lazy='dynamic')
    
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
    consulta_id = db.Column(db.Integer, db.ForeignKey('consulta.id'))
    
    def __repr__(self):
        return f'<SignosVitales {self.id}>'

class Consulta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('paciente.id'))
    tipo_consulta = db.Column(db.String(50))  # Primera consulta, Seguimiento, Medicamento
    clinica_id = db.Column(db.Integer, db.ForeignKey('clinica.id'))
    medico_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    fecha_consulta = db.Column(db.DateTime, default=datetime.utcnow)
    diagnostico = db.Column(db.Text)
    tratamiento = db.Column(db.Text)
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