from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
from app.models import Usuario

class LoginForm(FlaskForm):
    usuario = StringField('Usuario', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember_me = BooleanField('Recordarme')
    submit = SubmitField('Acceder')

class RegistrationForm(FlaskForm):
    nombre_completo = StringField('Nombre Completo', validators=[DataRequired()])
    usuario = StringField('Usuario', validators=[DataRequired()])
    email = StringField('Correo Electrónico', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Repetir Contraseña', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrar')
    
    def validate_usuario(self, usuario):
        user = Usuario.query.filter_by(usuario=usuario.data).first()
        if user is not None:
            raise ValidationError('Por favor use un nombre de usuario diferente.')
    def validate_email(self, email):
        user = Usuario.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Este correo ya está registrado.')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Correo Electrónico', validators=[DataRequired(), Email()])
    submit = SubmitField('Solicitar Restablecimiento de Contraseña')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Nueva Contraseña', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Repetir Contraseña', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Actualizar Contraseña')

class ChangeRoleForm(FlaskForm):
    usuario = StringField('Usuario', validators=[DataRequired()])
    rol = SelectField('Rol', choices=[
        ('medico', 'Médico'),
        ('medico_supervisor', 'Médico Supervisor'),
        ('admin', 'Administrador')
    ], validators=[DataRequired()])
    submit = SubmitField('Cambiar Rol')

class SolicitarCambioPasswordForm(FlaskForm):
    email = StringField('Correo Electrónico', validators=[DataRequired(), Email()])
    submit = SubmitField('Enviar Código de Verificación')

class VerificarCodigoForm(FlaskForm):
    codigo = StringField('Código de Verificación', validators=[
        DataRequired(), 
        Length(min=6, max=6, message='El código debe tener exactamente 6 dígitos')
    ])
    submit = SubmitField('Verificar Código')

class CambiarPasswordConCodigoForm(FlaskForm):
    codigo = StringField('Código de Verificación', validators=[
        DataRequired(), 
        Length(min=6, max=6, message='El código debe tener exactamente 6 dígitos')
    ])
    password = PasswordField('Nueva Contraseña', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Confirmar Nueva Contraseña', validators=[
        DataRequired(), 
        EqualTo('password', message='Las contraseñas deben coincidir')
    ])
    submit = SubmitField('Cambiar Contraseña')

class VerificationCodeForm(FlaskForm):
    email = StringField('Correo Electrónico', validators=[DataRequired(), Email()])
    code = StringField('Código de Verificación', validators=[DataRequired(), Length(min=4, max=4)])
    submit = SubmitField('Verificar Código')