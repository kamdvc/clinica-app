from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.pacientes import bp
from app.models import Paciente, Consulta, SignosVitales
from app.pacientes.forms import PacienteForm, SignosVitalesForm, BusquedaPacienteForm

@bp.route('/pacientes', methods=['GET', 'POST'])
@login_required
def pacientes_lista():
    # Vista para el listado de pacientes con búsqueda
    form = BusquedaPacienteForm()
    
    if form.validate_on_submit() or request.method == 'POST':
        termino = form.termino_busqueda.data
        # Buscar por nombre o ID
        pacientes = Paciente.query.filter(
            (Paciente.nombre_completo.ilike(f'%{termino}%')) | 
            (Paciente.id == termino if termino.isdigit() else False)
        ).order_by(Paciente.nombre_completo).all()
    else:
        pacientes = Paciente.query.order_by(Paciente.nombre_completo).all()
    
    return render_template('pacientes/lista.html', title='Pacientes', pacientes=pacientes, form=form)

@bp.route('/pacientes/nuevo', methods=['GET', 'POST'])
@login_required
def paciente_nuevo():
    # Vista para registrar un nuevo paciente
    form = PacienteForm()
    if form.validate_on_submit():
        paciente = Paciente(
            nombre_completo=form.nombre_completo.data,
            edad=form.edad.data,
            sexo=form.sexo.data,
            expediente=form.expediente.data
        )
        db.session.add(paciente)
        db.session.commit()
        flash('Paciente registrado correctamente')
        return redirect(url_for('pacientes.pacientes_lista'))
    return render_template('pacientes/formulario.html', title='Nuevo Paciente', form=form)

@bp.route('/pacientes/<int:paciente_id>', methods=['GET', 'POST'])
@login_required
def paciente_detalle(paciente_id):
    # Vista para ver y editar detalles de un paciente
    paciente = Paciente.query.get_or_404(paciente_id)
    form = PacienteForm(obj=paciente)
    if form.validate_on_submit():
        paciente.nombre_completo = form.nombre_completo.data
        paciente.edad = form.edad.data
        paciente.sexo = form.sexo.data
        paciente.expediente = form.expediente.data
        db.session.commit()
        flash('Información del paciente actualizada')
        return redirect(url_for('pacientes.pacientes_lista'))
    return render_template('pacientes/formulario.html', title='Editar Paciente', form=form, paciente=paciente)

@bp.route('/pacientes/<int:paciente_id>/eliminar', methods=['POST'])
@login_required
def eliminar_paciente(paciente_id):
    # Vista para eliminar un paciente
    paciente = Paciente.query.get_or_404(paciente_id)
    
    # Verificar si el paciente tiene consultas asociadas
    if paciente.consultas.count() > 0:
        flash('No se puede eliminar el paciente porque tiene consultas asociadas', 'danger')
        return redirect(url_for('pacientes.pacientes_lista'))
    
    nombre = paciente.nombre_completo
    db.session.delete(paciente)
    db.session.commit()
    flash(f'Paciente {nombre} eliminado correctamente', 'success')
    return redirect(url_for('pacientes.pacientes_lista'))

@bp.route('/pacientes/<int:paciente_id>/signos_vitales', methods=['GET', 'POST'])
@login_required
def registrar_signos_vitales(paciente_id):
    # Vista para registrar signos vitales de un paciente
    paciente = Paciente.query.get_or_404(paciente_id)
    form = SignosVitalesForm()
    if form.validate_on_submit():
        # Verificar si hay una consulta activa para este paciente
        consulta = Consulta.query.filter_by(paciente_id=paciente_id).order_by(Consulta.fecha_consulta.desc()).first()
        
        if not consulta:
            flash('No hay una consulta activa para este paciente')
            return redirect(url_for('pacientes.paciente_detalle', paciente_id=paciente_id))
        
        signos_vitales = SignosVitales(
            presion_arterial=form.presion_arterial.data,
            frecuencia_cardiaca=form.frecuencia_cardiaca.data,
            frecuencia_respiratoria=form.frecuencia_respiratoria.data,
            temperatura=form.temperatura.data,
            saturacion=form.saturacion.data,
            glucosa=form.glucosa.data,
            consulta_id=consulta.id
        )
        db.session.add(signos_vitales)
        db.session.commit()
        flash('Signos vitales registrados correctamente')
        return redirect(url_for('main.consulta', consulta_id=consulta.id))
    
    return render_template('pacientes/signos_vitales.html', title='Registrar Signos Vitales', form=form, paciente=paciente)