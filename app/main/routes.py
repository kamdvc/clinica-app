from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.main import bp
from app.models import Clinica, Paciente, Consulta, SignosVitales
from app.main.forms import DiagnosticoForm, RecetaForm, ConsultaForm
from app.pacientes.forms import BusquedaPacienteForm, SignosVitalesForm
from datetime import datetime

@bp.route('/')
@bp.route('/index')
@login_required
def index():
    # Redirigir a la página de recepción
    return redirect(url_for('main.recepcion'))

@bp.route('/recepcion', methods=['GET', 'POST'])
@login_required
def recepcion():
    # Vista para el módulo de recepción
    pacientes = Paciente.query.all()
    # Obtener todas las clínicas con su estado actual de disponibilidad
    clinicas = Clinica.query.all()
    
    if request.method == 'POST':
        # Datos del paciente
        nombre_completo = request.form.get('nombre_completo')
        edad = request.form.get('edad')
        sexo = request.form.get('sexo')
        direccion = request.form.get('direccion')
        telefono = request.form.get('telefono')
        
        # Nuevos campos
        expediente = True if request.form.get('expediente') == 'Si' else False
        tipo_consulta = request.form.get('tipo_consulta')
        
        # Signos vitales
        presion_arterial = request.form.get('presion_arterial')
        frecuencia_cardiaca = request.form.get('frec_cardiaca')
        frecuencia_respiratoria = request.form.get('frec_respiratoria')
        temperatura = request.form.get('temperatura')
        saturacion = request.form.get('saturacion')
        glucosa = request.form.get('glucosa')
        
        if nombre_completo and edad and sexo:
            # Crear paciente
            paciente = Paciente(
                nombre_completo=nombre_completo,
                edad=edad,
                sexo=sexo,
                expediente=expediente,
                direccion=direccion,
                telefono=telefono
            )
            db.session.add(paciente)
            db.session.commit()
            
            # Si hay una clínica disponible, crear consulta
            clinica_disponible = Clinica.query.filter_by(disponible=True).first()
            if clinica_disponible and tipo_consulta:
                consulta = Consulta(
                    paciente_id=paciente.id,
                    tipo_consulta=tipo_consulta,
                    clinica_id=clinica_disponible.id
                )
                db.session.add(consulta)
                db.session.commit()
                
                # Registrar signos vitales si se proporcionaron
                if presion_arterial or frecuencia_cardiaca or temperatura:
                    signos_vitales = SignosVitales(
                        presion_arterial=presion_arterial,
                        frecuencia_cardiaca=frecuencia_cardiaca,
                        frecuencia_respiratoria=frecuencia_respiratoria,
                        temperatura=temperatura,
                        saturacion=saturacion,
                        glucosa=glucosa,
                        consulta_id=consulta.id
                    )
                    db.session.add(signos_vitales)
                    db.session.commit()
            
            flash('Paciente registrado correctamente')
            return redirect(url_for('main.recepcion'))
    
    # Pasar None como valor predeterminado para tipo_consulta
    return render_template('main/recepcion.html', title='Recepción', pacientes=pacientes, clinicas=clinicas, tipo_consulta=None)

@bp.route('/clinicas')
@login_required
def clinicas():
    clinicas = Clinica.query.all()
    return render_template('main/clinicas.html', title='Estado de Clínicas', clinicas=clinicas)

@bp.route('/actualizar_estado_clinica/<int:clinica_id>', methods=['GET', 'POST'])
@login_required
def actualizar_estado_clinica(clinica_id):
    if current_user.rol != 'medico':
        flash('No tienes permiso para realizar esta acción', 'error')
        return redirect(url_for('main.clinicas'))
    
    # Obtener la clínica seleccionada
    clinica = Clinica.query.get_or_404(clinica_id)
    
    # Verificar si es una redirección desde una consulta
    redirect_to = request.args.get('redirect_to')
    consulta_id = request.args.get('consulta_id')
    
    if redirect_to and consulta_id:
        # Estamos en el flujo de consulta médica
        consulta = Consulta.query.get_or_404(consulta_id)
        
        # Marcar todas las clínicas como disponibles primero
        todas_clinicas = Clinica.query.all()
        for c in todas_clinicas:
            c.disponible = True
        
        # Actualizar la clínica de la consulta y marcarla como ocupada
        consulta.clinica_id = clinica_id
        clinica.disponible = False
        
        # Asignar el médico actual a la consulta
        consulta.medico_id = current_user.id
        
        db.session.commit()
        
        flash(f'Consulta actualizada a {clinica.nombre}', 'success')
        
        # Redirigir de vuelta a la página de consulta
        if redirect_to == 'consulta_diagnostico':
            return redirect(url_for('main.consulta_diagnostico', consulta_id=consulta_id))
        elif redirect_to == 'consulta_receta':
            return redirect(url_for('main.consulta_receta', consulta_id=consulta_id))
    else:
        # Flujo normal de actualización de estado
        nuevo_estado = request.form.get('estado') == '1'
        
        # Si estamos marcando una clínica como ocupada, marcar las demás como disponibles
        if not nuevo_estado:
            todas_clinicas = Clinica.query.all()
            for c in todas_clinicas:
                c.disponible = True
        
        clinica.disponible = nuevo_estado
        db.session.commit()
        
        flash(f'Estado de la clínica actualizado correctamente', 'success')
        return redirect(url_for('main.clinicas'))

@bp.route('/dashboard')
@login_required
def dashboard():
    # Panel de control con estadísticas
    total_pacientes = Paciente.query.count()
    total_consultas = Consulta.query.count()
    clinicas_disponibles = Clinica.query.filter_by(disponible=True).count()
    
    return render_template('main/dashboard.html', 
                          title='Panel de Control',
                          total_pacientes=total_pacientes,
                          total_consultas=total_consultas,
                          clinicas_disponibles=clinicas_disponibles)

@bp.route('/consultas', methods=['GET', 'POST'])
@login_required
def consultas():
    # Vista para el módulo de consultas médicas
    # Obtener todas las clínicas con su estado actual de disponibilidad
    clinicas = Clinica.query.all()
    
    # Crear formulario de búsqueda
    form = BusquedaPacienteForm()
    
    # Variables para el paciente seleccionado
    paciente_seleccionado = None
    consulta_actual = None
    signos_vitales_form = None
    pacientes = []
    
    if form.validate_on_submit():
        termino = form.termino_busqueda.data
        # Buscar por nombre o ID
        pacientes = Paciente.query.filter(
            (Paciente.nombre_completo.ilike(f'%{termino}%')) | 
            (Paciente.id == termino if termino.isdigit() else False)
        ).order_by(Paciente.nombre_completo).all()
        
        # Si solo hay un resultado, seleccionarlo automáticamente
        if len(pacientes) == 1:
            paciente_seleccionado = pacientes[0]
            # Obtener la última consulta del paciente si existe
            consulta_actual = Consulta.query.filter_by(paciente_id=paciente_seleccionado.id).order_by(Consulta.fecha_consulta.desc()).first()
            # Crear formulario de signos vitales
            signos_vitales_form = SignosVitalesForm()
            if consulta_actual and consulta_actual.signos_vitales:
                # Prellenar el formulario con los datos existentes
                signos_vitales_form.presion_arterial.data = consulta_actual.signos_vitales.presion_arterial
                signos_vitales_form.frecuencia_cardiaca.data = consulta_actual.signos_vitales.frecuencia_cardiaca
                signos_vitales_form.frecuencia_respiratoria.data = consulta_actual.signos_vitales.frecuencia_respiratoria
                signos_vitales_form.temperatura.data = consulta_actual.signos_vitales.temperatura
                signos_vitales_form.saturacion.data = consulta_actual.signos_vitales.saturacion
                signos_vitales_form.glucosa.data = consulta_actual.signos_vitales.glucosa
        
        # Si hay un paciente_id en la URL, obtener ese paciente
        paciente_id = request.args.get('paciente_id', None)
        if paciente_id and paciente_id.isdigit():
            paciente_seleccionado = Paciente.query.get(int(paciente_id))
            # Obtener la última consulta del paciente si existe
            consulta_actual = Consulta.query.filter_by(paciente_id=paciente_seleccionado.id).order_by(Consulta.fecha_consulta.desc()).first()
            # Crear formulario de signos vitales
            signos_vitales_form = SignosVitalesForm()
            if consulta_actual and consulta_actual.signos_vitales:
                # Prellenar el formulario con los datos existentes
                signos_vitales_form.presion_arterial.data = consulta_actual.signos_vitales.presion_arterial
                signos_vitales_form.frecuencia_cardiaca.data = consulta_actual.signos_vitales.frecuencia_cardiaca
                signos_vitales_form.frecuencia_respiratoria.data = consulta_actual.signos_vitales.frecuencia_respiratoria
                signos_vitales_form.temperatura.data = consulta_actual.signos_vitales.temperatura
                signos_vitales_form.saturacion.data = consulta_actual.signos_vitales.saturacion
                signos_vitales_form.glucosa.data = consulta_actual.signos_vitales.glucosa
    else:
        # Si hay un paciente_id en la URL, obtener ese paciente
        paciente_id = request.args.get('paciente_id', None)
        if paciente_id and paciente_id.isdigit():
            paciente_seleccionado = Paciente.query.get(int(paciente_id))
            # Obtener la última consulta del paciente si existe
            consulta_actual = Consulta.query.filter_by(paciente_id=paciente_seleccionado.id).order_by(Consulta.fecha_consulta.desc()).first()
            # Crear formulario de signos vitales
            signos_vitales_form = SignosVitalesForm()
            if consulta_actual and consulta_actual.signos_vitales:
                # Prellenar el formulario con los datos existentes
                signos_vitales_form.presion_arterial.data = consulta_actual.signos_vitales.presion_arterial
                signos_vitales_form.frecuencia_cardiaca.data = consulta_actual.signos_vitales.frecuencia_cardiaca
                signos_vitales_form.frecuencia_respiratoria.data = consulta_actual.signos_vitales.frecuencia_respiratoria
                signos_vitales_form.temperatura.data = consulta_actual.signos_vitales.temperatura
                signos_vitales_form.saturacion.data = consulta_actual.signos_vitales.saturacion
                signos_vitales_form.glucosa.data = consulta_actual.signos_vitales.glucosa
    
    return render_template('main/consultas.html', title='Consultas Médicas', 
                          clinicas=clinicas, form=form, pacientes=pacientes,
                          paciente=paciente_seleccionado, consulta=consulta_actual,
                          signos_vitales_form=signos_vitales_form)

@bp.route('/consulta/<int:consulta_id>')
@login_required
def consulta(consulta_id):
    # Vista para una consulta específica
    consulta = Consulta.query.get_or_404(consulta_id)
    return render_template('main/consulta.html', title='Consulta Médica', consulta=consulta, paciente=consulta.paciente)

@bp.route('/consulta/<int:consulta_id>/diagnostico', methods=['GET', 'POST'])
@login_required
def consulta_diagnostico(consulta_id):
    # Vista para el diagnóstico de una consulta
    consulta = Consulta.query.get_or_404(consulta_id)
    form = DiagnosticoForm()
    
    if form.validate_on_submit():
        consulta.diagnostico = form.descripcion.data
        consulta.laboratorio = form.laboratorio.data
        db.session.commit()
        flash('Diagnóstico guardado correctamente')
        return redirect(url_for('main.consulta_receta', consulta_id=consulta_id))
        
    return render_template('main/consulta_diagnostico.html', 
                          title='Diagnóstico', 
                          consulta=consulta, 
                          paciente=consulta.paciente,
                          form=form)

@bp.route('/consulta/<int:consulta_id>/receta', methods=['GET', 'POST'])
@login_required
def consulta_receta(consulta_id):
    # Vista para la receta de una consulta
    consulta = Consulta.query.get_or_404(consulta_id)
    form = RecetaForm()
    
    if form.validate_on_submit():
        consulta.tratamiento = form.medicamentos.data + '\n\nIndicaciones:\n' + form.indicaciones.data
        db.session.commit()
        flash('Receta guardada correctamente')
        return redirect(url_for('main.informe_medico', consulta_id=consulta_id))
        
    return render_template('main/consulta_receta.html', 
                          title='Receta Médica', 
                          consulta=consulta, 
                          paciente=consulta.paciente,
                          form=form)

@bp.route('/reportes')
@login_required
def reportes():
    # Vista para el módulo de reportes
    return render_template('main/reportes.html', title='Reportes')

@bp.route('/informe_medico/<int:consulta_id>')
@login_required
def informe_medico(consulta_id):
    # Vista para generar un informe médico
    consulta = Consulta.query.get_or_404(consulta_id)
    return render_template('main/informe_medico.html', title='Informe Médico', consulta=consulta, paciente=consulta.paciente)

@bp.route('/api/pacientes/buscar')
@login_required
def buscar_pacientes():
    # API para buscar pacientes por nombre o ID
    from flask import jsonify
    query = request.args.get('q', '')
    
    if not query or len(query.strip()) < 2:
        return jsonify([])
    
    # Buscar por ID si es un número
    if query.isdigit():
        paciente = Paciente.query.get(int(query))
        if paciente:
            return jsonify([{
                'id': paciente.id,
                'nombre_completo': paciente.nombre_completo,
                'edad': paciente.edad,
                'sexo': paciente.sexo
            }])
    
    # Buscar por nombre (parcial)
    pacientes = Paciente.query.filter(Paciente.nombre_completo.ilike(f'%{query}%')).limit(10).all()
    
    # Formatear resultados
    resultados = [{
        'id': p.id,
        'nombre_completo': p.nombre_completo,
        'edad': p.edad,
        'sexo': p.sexo
    } for p in pacientes]
    
    return jsonify(resultados)

@bp.route('/obtener_signos_vitales/<int:paciente_id>', methods=['GET'])
@login_required
def obtener_signos_vitales(paciente_id):
    # Endpoint para obtener los signos vitales de un paciente mediante AJAX
    from flask import jsonify
    paciente = Paciente.query.get_or_404(paciente_id)
    
    # Obtener la última consulta del paciente
    consulta = Consulta.query.filter_by(paciente_id=paciente_id).order_by(Consulta.fecha_consulta.desc()).first()
    
    # Preparar la respuesta
    respuesta = {
        'paciente': {
            'id': paciente.id,
            'nombre_completo': paciente.nombre_completo,
            'edad': paciente.edad,
            'sexo': paciente.sexo
        },
        'signos_vitales': None
    }
    
    # Si hay consulta y tiene signos vitales, incluirlos en la respuesta
    if consulta and consulta.signos_vitales:
        respuesta['signos_vitales'] = {
            'presion_arterial': consulta.signos_vitales.presion_arterial,
            'frecuencia_cardiaca': consulta.signos_vitales.frecuencia_cardiaca,
            'frecuencia_respiratoria': consulta.signos_vitales.frecuencia_respiratoria,
            'temperatura': consulta.signos_vitales.temperatura,
            'saturacion': consulta.signos_vitales.saturacion,
            'glucosa': consulta.signos_vitales.glucosa
        }
    
    return jsonify(respuesta)

@bp.route('/actualizar_signos_vitales/<int:paciente_id>', methods=['GET', 'POST'])
@login_required
def actualizar_signos_vitales(paciente_id):
    # Vista para actualizar los signos vitales de un paciente desde la página de consultas
    paciente = Paciente.query.get_or_404(paciente_id)
    form = SignosVitalesForm()
    
    if form.validate_on_submit():
        # Verificar si hay una consulta activa para este paciente
        consulta = Consulta.query.filter_by(paciente_id=paciente_id).order_by(Consulta.fecha_consulta.desc()).first()
        
        if not consulta:
            flash('No hay una consulta activa para este paciente', 'warning')
            return redirect(url_for('main.consultas', paciente_id=paciente_id))
        
        # Verificar si ya existen signos vitales para esta consulta
        if consulta.signos_vitales:
            # Actualizar los signos vitales existentes
            consulta.signos_vitales.presion_arterial = form.presion_arterial.data
            consulta.signos_vitales.frecuencia_cardiaca = form.frecuencia_cardiaca.data
            consulta.signos_vitales.frecuencia_respiratoria = form.frecuencia_respiratoria.data
            consulta.signos_vitales.temperatura = form.temperatura.data
            consulta.signos_vitales.saturacion = form.saturacion.data
            consulta.signos_vitales.glucosa = form.glucosa.data
        else:
            # Crear nuevos signos vitales
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
        flash('Signos vitales actualizados correctamente', 'success')
        return redirect(url_for('main.consultas', paciente_id=paciente_id))
    
    return redirect(url_for('main.consultas', paciente_id=paciente_id))

@bp.route('/consulta/nueva/<int:paciente_id>')
@login_required
def nueva_consulta(paciente_id):
    # Crear una nueva consulta para un paciente existente
    paciente = Paciente.query.get_or_404(paciente_id)
    
    # Verificar si hay una clínica disponible
    clinica_disponible = Clinica.query.filter_by(disponible=True).first()
    
    if not clinica_disponible:
        flash('No hay clínicas disponibles en este momento', 'warning')
        return redirect(url_for('main.consultas'))
    
    # Crear la consulta
    consulta = Consulta(
        paciente_id=paciente.id,
        tipo_consulta='Consulta médica',
        clinica_id=clinica_disponible.id,
        medico_id=current_user.id
    )
    
    db.session.add(consulta)
    db.session.commit()
    
    flash(f'Consulta iniciada para {paciente.nombre_completo}', 'success')
    return redirect(url_for('main.consulta', consulta_id=consulta.id))