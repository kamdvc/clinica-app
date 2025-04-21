from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
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
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Repetir Contraseña', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrar')
    
    def validate_usuario(self, usuario):
        user = Usuario.query.filter_by(usuario=usuario.data).first()
        if user is not None:
            raise ValidationError('Por favor use un nombre de usuario diferente.')

class ResetPasswordRequestForm(FlaskForm):
    usuario = StringField('Usuario', validators=[DataRequired()])
    submit = SubmitField('Solicitar Restablecimiento de Contraseña')

class ResetPasswordForm(FlaskForm):
    usuario = StringField('Usuario', validators=[DataRequired()])
    password = PasswordField('Nueva Contraseña', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Repetir Contraseña', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Actualizar Contraseña')