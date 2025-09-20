from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.pacientes import bp
from app.models import Paciente, Consulta, SignosVitales
from sqlalchemy import func
from app.pacientes.forms import PacienteForm, SignosVitalesForm, BusquedaPacienteForm

@bp.route('/pacientes', methods=['GET', 'POST'])
@login_required
def pacientes_lista():
    # Bloquear usuarios pendientes
    if current_user.rol in ['pendiente', None]:
        flash('Tu cuenta aún no ha sido aprobada por un administrador.', 'warning')
        return redirect(url_for('auth.espera_aprobacion'))
    # Vista para el listado de pacientes con búsqueda
    form = BusquedaPacienteForm()
    
    # Importar la función corregida
    from app.main.routes import filtered_pacientes_query
    
    if form.validate_on_submit() or request.method == 'POST':
        termino = (form.termino_busqueda.data or '').strip()
        # Usar la función corregida que permite ver pacientes recién registrados
        base_q = filtered_pacientes_query()
        pacientes = base_q.filter(
            (Paciente.nombre_completo.ilike(f'%{termino}%')) |
            (Paciente.id == int(termino) if termino.isdigit() else False)
        ).order_by(Paciente.nombre_completo).all()
    else:
        # Usar la función corregida para listado completo
        pacientes = filtered_pacientes_query().order_by(Paciente.nombre_completo).all()
    
    return render_template('pacientes/lista.html', title='Pacientes', pacientes=pacientes, form=form)

@bp.route('/pacientes/nuevo', methods=['GET', 'POST'])
@login_required
def paciente_nuevo():
    if current_user.rol in ['pendiente', None]:
        flash('Tu cuenta aún no ha sido aprobada por un administrador.', 'warning')
        return redirect(url_for('auth.espera_aprobacion'))
    # Vista para registrar un nuevo paciente
    form = PacienteForm()
    if form.validate_on_submit():
        paciente = Paciente(
            nombre_completo=form.nombre_completo.data,
            edad=form.edad.data,
            sexo=form.sexo.data,
            direccion=form.direccion.data,
            telefono=form.telefono.data,
            expediente=form.expediente.data,
            estado_civil=form.estado_civil.data,
            religion=form.religion.data,
            escolaridad=form.escolaridad.data,
            ocupacion=form.ocupacion.data,
            procedencia=form.procedencia.data,
            numero_expediente=form.numero_expediente.data
        )
        db.session.add(paciente)
        db.session.commit()
        flash('Paciente registrado correctamente')
        return redirect(url_for('pacientes.pacientes_lista'))
    return render_template('pacientes/formulario.html', title='Nuevo Paciente', form=form)

@bp.route('/pacientes/<int:paciente_id>', methods=['GET', 'POST'])
@login_required
def paciente_detalle(paciente_id):
    if current_user.rol in ['pendiente', None]:
        flash('Tu cuenta aún no ha sido aprobada por un administrador.', 'warning')
        return redirect(url_for('auth.espera_aprobacion'))
    # Vista para ver y editar detalles de un paciente
    paciente = Paciente.query.get_or_404(paciente_id)
    # Restringir acceso por clínica para médicos
    if current_user.rol == 'medico' and current_user.clinica_actual_id:
        pertenece = db.session.query(func.count(Consulta.id)).filter(
            Consulta.paciente_id == paciente.id,
            Consulta.clinica_id == current_user.clinica_actual_id
        ).scalar()
        if not pertenece:
            flash('No tiene acceso a este paciente (otra clínica).', 'error')
            return redirect(url_for('pacientes.pacientes_lista'))
    form = PacienteForm(obj=paciente)
    if form.validate_on_submit():
        paciente.nombre_completo = form.nombre_completo.data
        paciente.edad = form.edad.data
        paciente.sexo = form.sexo.data
        paciente.direccion = form.direccion.data
        paciente.telefono = form.telefono.data
        paciente.expediente = form.expediente.data
        paciente.estado_civil = form.estado_civil.data
        paciente.religion = form.religion.data
        paciente.escolaridad = form.escolaridad.data
        paciente.ocupacion = form.ocupacion.data
        paciente.procedencia = form.procedencia.data
        paciente.numero_expediente = form.numero_expediente.data
        db.session.commit()
        flash('Información del paciente actualizada')
        return redirect(url_for('pacientes.pacientes_lista'))
    return render_template('pacientes/formulario.html', title='Editar Paciente', form=form, paciente=paciente)

@bp.route('/pacientes/<int:paciente_id>/eliminar', methods=['POST'])
@login_required
def eliminar_paciente(paciente_id):
    if current_user.rol not in ['admin', 'medico_supervisor']:
        flash('No tiene permiso para eliminar pacientes.', 'danger')
        return redirect(url_for('pacientes.pacientes_lista'))

    paciente = Paciente.query.get_or_404(paciente_id)
    
    try:
        # Eliminar Signos Vitales y Consultas asociadas
        for consulta in paciente.consultas:
            if consulta.signos_vitales:
                db.session.delete(consulta.signos_vitales)
            db.session.delete(consulta)
        
        nombre = paciente.nombre_completo
        db.session.delete(paciente)
        db.session.commit()
        flash(f'Paciente {nombre} y todos sus registros han sido eliminados correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el paciente: {str(e)}', 'danger')

    return redirect(url_for('pacientes.pacientes_lista'))


@bp.route('/pacientes/<int:paciente_id>/signos_vitales', methods=['GET', 'POST'])
@login_required
def registrar_signos_vitales(paciente_id):
    if current_user.rol in ['pendiente', None]:
        flash('Tu cuenta aún no ha sido aprobada por un administrador.', 'warning')
        return redirect(url_for('auth.espera_aprobacion'))
    # Vista para registrar signos vitales de un paciente
    paciente = Paciente.query.get_or_404(paciente_id)
    form = SignosVitalesForm()
    if form.validate_on_submit():
        # Verificar si hay una consulta activa para este paciente
        consulta_q = Consulta.query.filter_by(paciente_id=paciente_id)
        if current_user.rol == 'medico' and current_user.clinica_actual_id:
            consulta_q = consulta_q.filter(Consulta.clinica_id == current_user.clinica_actual_id)
        consulta = consulta_q.order_by(Consulta.fecha_consulta.desc()).first()
        
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