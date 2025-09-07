from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.reportes import bp
from app.models import Paciente, Consulta, SignosVitales, Clinica
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import re
from collections import Counter

# Definición de sistemas y palabras clave asociadas
SISTEMAS_CORPORALES = {
    'Cardiovascular': ['corazón', 'presión', 'arterial', 'circulación', 'palpitaciones', 'taquicardia', 'bradicardia'],
    'Respiratorio': ['pulmones', 'respiración', 'tos', 'asma', 'bronquitis', 'disnea', 'sibilancias'],
    'Gastrointestinal': ['estómago', 'intestino', 'digestión', 'dolor abdominal', 'náuseas', 'vómitos', 'diarrea', 'estreñimiento'],
    'Neurológico': ['cerebro', 'nervios', 'dolor de cabeza', 'mareos', 'vértigo', 'convulsiones', 'migraña'],
    'Musculoesquelético': ['músculos', 'huesos', 'articulaciones', 'dolor de espalda', 'artritis', 'fractura'],
    'Endocrino': ['diabetes', 'tiroides', 'hormonas', 'metabolismo'],
    'Urinario': ['riñones', 'vejiga', 'infección urinaria', 'dolor al orinar'],
    'Piel y Tegumentos': ['piel', 'dermatitis', 'erupción', 'acné', 'herida', 'quemadura']
}

def analizar_sistemas(texto):
    """Analiza un texto y cuenta las menciones de cada sistema corporal."""
    if not texto:
        return Counter()
    
    # Normalizar texto: minúsculas y sin acentos (simplificado)
    texto_normalizado = texto.lower()
    conteo = Counter()

    for sistema, keywords in SISTEMAS_CORPORALES.items():
        for keyword in keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', texto_normalizado):
                conteo[sistema] += 1
    return conteo

@bp.route('/reportes')
@login_required
def reportes_index():
    return render_template('reportes/index.html', title='Reportes')

@bp.route('/reportes/consultas')
@login_required
def reporte_consultas():
    # Si es médico, limitar a su clínica; admin/supervisor ven todas
    if current_user.rol == 'medico' and current_user.clinica_actual_id:
        consultas = Consulta.query.filter_by(clinica_id=current_user.clinica_actual_id).order_by(Consulta.fecha_consulta.desc()).all()
    else:
        consultas = Consulta.query.order_by(Consulta.fecha_consulta.desc()).all()

    # Conteo del mes actual (sistema ya está en Guatemala)
    now = datetime.now()
    first_of_month = datetime(now.year, now.month, 1)
    next_year = now.year + (1 if now.month == 12 else 0)
    next_month = 1 if now.month == 12 else now.month + 1
    first_next_month = datetime(next_year, next_month, 1)
    total_mes_query = Consulta.query \
        .filter(Consulta.fecha_consulta >= first_of_month) \
        .filter(Consulta.fecha_consulta < first_next_month)
    if current_user.rol == 'medico' and current_user.clinica_actual_id:
        total_mes_query = total_mes_query.filter(Consulta.clinica_id == current_user.clinica_actual_id)
    total_mes_actual = total_mes_query.count()

    return render_template('reportes/consultas.html', title='Reporte de Consultas', consultas=consultas, total_mes_actual=total_mes_actual)

@bp.route('/reportes/pacientes')
@login_required
def reporte_pacientes():
    # Médicos: solo pacientes que han tenido consultas en su clínica
    if current_user.rol == 'medico' and current_user.clinica_actual_id:
        pacientes_ids = db.session.query(Consulta.paciente_id).filter(Consulta.clinica_id == current_user.clinica_actual_id).distinct()
        pacientes = Paciente.query.filter(Paciente.id.in_(pacientes_ids)).order_by(Paciente.nombre_completo).all()
    else:
        pacientes = Paciente.query.order_by(Paciente.nombre_completo).all()
    return render_template('reportes/pacientes.html', title='Reporte de Pacientes', pacientes=pacientes)

@bp.route('/reportes/clinicas')
@login_required
def reporte_clinicas():
    # Médicos: solo su clínica; admin/supervisor todas
    if current_user.rol == 'medico' and current_user.clinica_actual_id:
        clinicas = Clinica.query.filter(Clinica.id == current_user.clinica_actual_id).all()
    else:
        clinicas = Clinica.query.all()
    for clinica in clinicas:
        clinica.total_consultas = Consulta.query.filter_by(clinica_id=clinica.id).count()
    return render_template('reportes/clinicas.html', title='Reporte de Clínicas', clinicas=clinicas)

@bp.route('/reportes/diario')
@login_required
def reporte_diario():
    hoy = datetime.now().date()
    inicio_dia = datetime.combine(hoy, datetime.min.time())
    fin_dia = datetime.combine(hoy, datetime.max.time())
    
    base_q = Consulta.query.filter(
        Consulta.fecha_consulta >= inicio_dia,
        Consulta.fecha_consulta <= fin_dia
    )
    if current_user.rol == 'medico' and current_user.clinica_actual_id:
        base_q = base_q.filter(Consulta.clinica_id == current_user.clinica_actual_id)
    consultas_hoy = base_q.order_by(Consulta.fecha_consulta).all()
    
    return render_template('reportes/diario.html', title='Reporte Diario', consultas=consultas_hoy)

@bp.route('/reportes/estadisticas')
@login_required
def estadisticas_clinicas():
    # Obtener IDs de pacientes según alcance (médico: su clínica; admin/supervisor: global)
    pacientes_ids_q = db.session.query(Consulta.paciente_id)
    if current_user.rol == 'medico' and current_user.clinica_actual_id:
        pacientes_ids_q = pacientes_ids_q.filter(Consulta.clinica_id == current_user.clinica_actual_id)
    pacientes_ids = pacientes_ids_q.distinct().all()
    pacientes_ids = [pid[0] for pid in pacientes_ids if pid[0] is not None]

    # Filtrar pacientes por esos IDs
    masculino = Paciente.query.filter(Paciente.id.in_(pacientes_ids), Paciente.sexo == 'Masculino').count()
    femenino = Paciente.query.filter(Paciente.id.in_(pacientes_ids), Paciente.sexo == 'Femenino').count()

    rangos = [
        (0, 5), (6, 10), (11, 15), (21, 25), (26, 30), (31, 35),
        (36, 40), (41, 45), (46, 50), (51, 55), (56, 60), (61, 65),
        (66, 70), (71, 75), (76, 80), (86, 90)
    ]
    rangos_edad = [f'{r[0]}-{r[1]}' for r in rangos]
    conteo_edades = [
        Paciente.query.filter(Paciente.id.in_(pacientes_ids), Paciente.edad >= r[0], Paciente.edad <= r[1]).count()
        for r in rangos
    ]

    # Diagnósticos según alcance
    diag_q = db.session.query(Consulta.diagnostico)
    if current_user.rol == 'medico' and current_user.clinica_actual_id:
        diag_q = diag_q.filter(Consulta.clinica_id == current_user.clinica_actual_id)
    diagnosticos = diag_q.all()
    conteo_diagnosticos = {}
    for diag in diagnosticos:
        if diag[0]:
            nombre = diag[0].strip().capitalize()
            conteo_diagnosticos[nombre] = conteo_diagnosticos.get(nombre, 0) + 1
    enfermedades_comunes = sorted(conteo_diagnosticos.items(), key=lambda x: x[1], reverse=True)[:10]
    enfermedades_labels = [e[0] for e in enfermedades_comunes]
    enfermedades_casos = [e[1] for e in enfermedades_comunes]

    # Revisión por sistemas según alcance
    rev_q = Consulta.query.filter(Consulta.revision_sistemas.isnot(None))
    if current_user.rol == 'medico' and current_user.clinica_actual_id:
        rev_q = rev_q.filter(Consulta.clinica_id == current_user.clinica_actual_id)
    consultas_con_revision = rev_q.all()
    conteo_total_sistemas = Counter()
    for consulta in consultas_con_revision:
        conteo_total_sistemas.update(analizar_sistemas(consulta.revision_sistemas))

    # Preparar datos para el gráfico
    sistemas_labels = list(conteo_total_sistemas.keys())
    sistemas_casos = list(conteo_total_sistemas.values())

    # Conteo del mes actual según alcance
    now = datetime.now()
    first_of_month = datetime(now.year, now.month, 1)
    next_year = now.year + (1 if now.month == 12 else 0)
    next_month = 1 if now.month == 12 else now.month + 1
    first_next_month = datetime(next_year, next_month, 1)
    total_mes_q = Consulta.query \
        .filter(Consulta.fecha_consulta >= first_of_month) \
        .filter(Consulta.fecha_consulta < first_next_month)
    if current_user.rol == 'medico' and current_user.clinica_actual_id:
        total_mes_q = total_mes_q.filter(Consulta.clinica_id == current_user.clinica_actual_id)
    total_mes_actual = total_mes_q.count()

    return render_template('reportes/estadisticas.html',
        title='Estadísticas Clínicas',
        masculino=masculino,
        femenino=femenino,
        rangos_edad=rangos_edad,
        conteo_edades=conteo_edades,
        enfermedades_labels=enfermedades_labels,
        enfermedades_casos=enfermedades_casos,
        sistemas_labels=sistemas_labels,
        sistemas_casos=sistemas_casos,
        total_mes_actual=total_mes_actual
    )
