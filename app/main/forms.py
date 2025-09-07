from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Optional

class DiagnosticoForm(FlaskForm):
    descripcion = TextAreaField('Descripción del Diagnóstico', validators=[DataRequired()])
    laboratorio = TextAreaField('Exámenes de Laboratorio')
    submit = SubmitField('Guardar Diagnóstico')

class RecetaForm(FlaskForm):
    medicamentos = TextAreaField('Medicamentos', validators=[DataRequired()])
    indicaciones = TextAreaField('Indicaciones', validators=[DataRequired()])
    submit = SubmitField('Guardar Receta')

class ConsultaForm(FlaskForm):
    paciente_id = HiddenField('ID del Paciente', validators=[DataRequired()])
    tipo_consulta = SelectField('Tipo de Consulta', choices=[
        ('Consulta médica', 'Consulta médica'),
        ('Consulta pediátrica', 'Consulta pediátrica'),
        ('Consulta ginecológica', 'Consulta ginecológica'),
        ('Curación', 'Curación')
    ], validators=[DataRequired()])
    clinica_id = SelectField('Clínica', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Iniciar Consulta')

class MotivoConsultaForm(FlaskForm):
    motivo_consulta = TextAreaField('Motivo de Consulta', validators=[DataRequired()])
    historia_enfermedad = TextAreaField('Historia de la Enfermedad')
    revision_sistemas = TextAreaField('Revisión por Sistemas')
    submit = SubmitField('Guardar')

class BusquedaPacienteForm(FlaskForm):
    query = StringField('Buscar Paciente', render_kw={"placeholder": "Nombre o ID"})
    submit = SubmitField('Buscar')