from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.reportes import bp
from app.models import Paciente, Consulta, SignosVitales, Clinica
from datetime import datetime, timedelta

@bp.route('/reportes')
@login_required
def reportes_index():
    # Vista principal para el módulo de reportes
    return render_template('reportes/index.html', title='Reportes')

@bp.route('/reportes/consultas')
@login_required
def reporte_consultas():
    # Reporte de consultas realizadas
    consultas = Consulta.query.order_by(Consulta.fecha_consulta.desc()).all()
    return render_template('reportes/consultas.html', title='Reporte de Consultas', consultas=consultas)

@bp.route('/reportes/pacientes')
@login_required
def reporte_pacientes():
    # Reporte de pacientes atendidos
    pacientes = Paciente.query.order_by(Paciente.nombre_completo).all()
    return render_template('reportes/pacientes.html', title='Reporte de Pacientes', pacientes=pacientes)

@bp.route('/reportes/clinicas')
@login_required
def reporte_clinicas():
    # Reporte de uso de clínicas
    clinicas = Clinica.query.all()
    # Contar consultas por clínica
    for clinica in clinicas:
        clinica.total_consultas = Consulta.query.filter_by(clinica_id=clinica.id).count()
    
    return render_template('reportes/clinicas.html', title='Reporte de Clínicas', clinicas=clinicas)

@bp.route('/reportes/diario')
@login_required
def reporte_diario():
    # Reporte de consultas del día actual
    hoy = datetime.now().date()
    inicio_dia = datetime.combine(hoy, datetime.min.time())
    fin_dia = datetime.combine(hoy, datetime.max.time())
    
    consultas_hoy = Consulta.query.filter(
        Consulta.fecha_consulta >= inicio_dia,
        Consulta.fecha_consulta <= fin_dia
    ).order_by(Consulta.fecha_consulta).all()
    
    return render_template('reportes/diario.html', title='Reporte Diario', consultas=consultas_hoy)

@bp.route('/reportes/estadisticas')
@login_required
def estadisticas_clinicas():
    # Mostrar estadísticas clínicas
    return render_template('reportes/estadisticas.html', title='Estadísticas Clínicas')
    
    return render_template('reportes/diario.html', 
                          title='Reporte Diario', 
                          consultas=consultas_hoy, 
                          fecha=hoy)