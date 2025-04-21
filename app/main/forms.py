from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional

class DiagnosticoForm(FlaskForm):
    descripcion = TextAreaField('Descripción del Diagnóstico', validators=[DataRequired()])
    laboratorio = TextAreaField('Resultados de Laboratorio', validators=[Optional()])
    submit = SubmitField('Guardar Diagnóstico')

class RecetaForm(FlaskForm):
    medicamentos = TextAreaField('Medicamentos', validators=[DataRequired()])
    indicaciones = TextAreaField('Indicaciones', validators=[DataRequired()])
    submit = SubmitField('Guardar Receta')

class ConsultaForm(FlaskForm):
    tipo_consulta = SelectField('Tipo de Consulta', 
                              choices=[('Primera', 'Primera Consulta'), 
                                      ('Seguimiento', 'Consulta de Seguimiento'),
                                      ('Medicamento', 'Solicitud de Medicamento')],
                              validators=[DataRequired()])
    paciente_id = SelectField('Paciente', coerce=int, validators=[DataRequired()])
    clinica_id = SelectField('Clínica', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Iniciar Consulta')