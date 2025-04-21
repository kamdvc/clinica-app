from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, BooleanField, FloatField, SubmitField, SearchField
from wtforms.validators import DataRequired, NumberRange, Optional

class PacienteForm(FlaskForm):
    nombre_completo = StringField('Nombre Completo', validators=[DataRequired()])
    edad = IntegerField('Edad', validators=[DataRequired(), NumberRange(min=0, max=120)])
    sexo = SelectField('Sexo', choices=[('', 'Seleccionar'), ('Masculino', 'Masculino'), ('Femenino', 'Femenino')], validators=[DataRequired()])
    expediente = BooleanField('Tiene Expediente')
    submit = SubmitField('Guardar')

class BusquedaPacienteForm(FlaskForm):
    termino_busqueda = StringField('Buscar por nombre o ID', validators=[DataRequired()])
    submit = SubmitField('Buscar')

class SignosVitalesForm(FlaskForm):
    presion_arterial = StringField('Presión Arterial (mmHg)', validators=[DataRequired()])
    frecuencia_cardiaca = IntegerField('Frecuencia Cardíaca (lpm)', validators=[DataRequired(), NumberRange(min=30, max=250)])
    frecuencia_respiratoria = IntegerField('Frecuencia Respiratoria (rpm)', validators=[DataRequired(), NumberRange(min=8, max=60)])
    temperatura = FloatField('Temperatura (°C)', validators=[DataRequired(), NumberRange(min=34.0, max=42.0)])
    saturacion = IntegerField('Saturación de Oxígeno (%)', validators=[DataRequired(), NumberRange(min=50, max=100)])
    glucosa = IntegerField('Glucosa (mg/dl)', validators=[Optional(), NumberRange(min=20, max=600)])
    submit = SubmitField('Registrar')