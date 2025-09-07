from flask import render_template, redirect, url_for, flash, request, jsonify, make_response, send_file, current_app
from flask_login import login_required, current_user
from app import db
from app.main import bp
from app.models import Clinica, Paciente, Consulta, SignosVitales, Usuario, HistorialRoles, HistorialAsignacionClinica # Asegúrate de importar HistorialAsignacionClinica si usas current_user.id
from app.main.forms import DiagnosticoForm, RecetaForm, ConsultaForm, MotivoConsultaForm, BusquedaPacienteForm
from app.pacientes.forms import BusquedaPacienteForm, SignosVitalesForm
from datetime import datetime, timedelta
from sqlalchemy import or_, func, extract, text
from sqlalchemy.orm import joinedload
from functools import wraps
from flask import abort
import io
import json
import os
from collections import defaultdict, Counter
from sqlalchemy import asc, desc
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Tratar medico_supervisor como equivalente a admin para permisos
            effective_role = current_user.rol
            if effective_role == 'medico_supervisor' and 'admin' in roles:
                return f(*args, **kwargs)
            if not effective_role in roles:
                flash('No tienes permiso para acceder a esta página.', 'error')
                return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ===== Helpers de control de acceso por clínica =====
def require_clinic_selected_redirect():
    """Si el usuario es médico y no tiene clínica seleccionada, redirige a selección de clínicas."""
    if current_user.rol == 'medico' and not current_user.clinica_actual_id:
        flash('Seleccione una clínica para continuar.', 'warning')
        return redirect(url_for('main.clinicas'))
    return None


def ensure_consulta_access(consulta):
    """Impide que un médico acceda a consultas fuera de su clínica."""
    if current_user.rol == 'medico':
        # Si el médico es el propietario de la consulta, permitir siempre
        if consulta.medico_id == current_user.id:
            return
        # Si no es propietario, exigir clínica seleccionada y coincidencia
        if not current_user.clinica_actual_id:
            abort(403)
        if consulta.clinica_id and consulta.clinica_id != current_user.clinica_actual_id:
            abort(403)


def filtered_consultas_query():
    """Consulta de `Consulta` filtrada por clínica del médico si aplica."""
    q = Consulta.query
    if current_user.rol == 'medico' and current_user.clinica_actual_id:
        q = q.filter(Consulta.clinica_id == current_user.clinica_actual_id)
    return q


def filtered_pacientes_query():
    """Pacientes visibles. Médico solo ve los con consultas en su clínica actual."""
    if current_user.rol == 'medico' and current_user.clinica_actual_id:
        return Paciente.query.join(Consulta, Consulta.paciente_id == Paciente.id) \
            .filter(Consulta.clinica_id == current_user.clinica_actual_id).distinct()
    return Paciente.query

@bp.route('/')
@bp.route('/index')
@login_required
def index():
    # Bloqueo global para cuentas pendientes
    if current_user.rol in ['pendiente', None]:
        flash('Tu cuenta aún no ha sido aprobada por un administrador.', 'warning')
        return redirect(url_for('auth.espera_aprobacion'))

    if current_user.rol in ['medico', 'medico_supervisor']:
        if current_user.rol == 'medico' and not current_user.clinica_actual_id:
            return redirect(url_for('main.clinicas'))
        return redirect(url_for('main.consultas'))
    return redirect(url_for('main.recepcion'))

@bp.route('/recepcion', methods=['GET', 'POST'])
@login_required
@role_required('medico', 'admin', 'medico_supervisor')
def recepcion():
    # Vista para el módulo de recepción
    redirect_resp = require_clinic_selected_redirect()
    if redirect_resp:
        return redirect_resp
    pacientes = filtered_pacientes_query().all()
    # Obtener clínicas visibles (médico solo ve su clínica)
    if current_user.rol == 'medico' and current_user.clinica_actual_id:
        clinicas = Clinica.query.filter(Clinica.id == current_user.clinica_actual_id).all()
    else:
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
                    clinica_id=clinica_disponible.id,
                    estado='en_progreso'
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

@bp.route('/api/search_patients', methods=['GET'])
@login_required
def search_patients():
    query = request.args.get('query', '').strip()
    if query:
        base_q = filtered_pacientes_query()
        patients = base_q.filter(
            or_(
                Paciente.nombre_completo.ilike(f"%{query}%"),
                Paciente.dni.ilike(f"%{query}%")
            )
        ).all()
        resultados = []
        for paciente in patients:
            consultas = filtered_consultas_query().filter_by(paciente_id=paciente.id).order_by(Consulta.fecha_consulta.desc()).all()
            historial_consultas = []
            for consulta in consultas:
                consulta_data = {
                    'id': consulta.id,
                    'fecha': consulta.fecha_consulta.strftime('%d/%m/%Y %H:%M') if consulta.fecha_consulta else '',
                    'tipo_consulta': consulta.tipo_consulta or 'General',
                    'medico': consulta.medico.nombre_completo if consulta.medico else 'No especificado',
                    'motivo_consulta': consulta.motivo_consulta or '',
                    'historia_enfermedad': consulta.historia_enfermedad or '',
                    'revision_sistemas': consulta.revision_sistemas or '',
                    'antecedentes': consulta.antecedentes or '',
                    'diagnostico': consulta.diagnostico or '',
                    'tratamiento': consulta.tratamiento or '',
                    'signos_vitales': consulta.signos_vitales.to_dict() if consulta.signos_vitales else None,
                    'presion_arterial': consulta.presion_arterial or '',
                    'frecuencia_respiratoria': consulta.frecuencia_respiratoria or '',
                    'temperatura': consulta.temperatura or '',
                    'peso': consulta.peso or '',
                    'talla': consulta.talla or '',
                    'frecuencia_cardiaca': consulta.frecuencia_cardiaca or '',
                    'saturacion_oxigeno': consulta.saturacion_oxigeno or '',
                    'imc': consulta.imc or '',
                    'gestas': consulta.gestas or '',
                    'partos': consulta.partos or '',
                    'abortos': consulta.abortos or '',
                    'hijos_vivos': consulta.hijos_vivos or '',
                    'hijos_muertos': consulta.hijos_muertos or '',
                    'fecha_ultima_regla': consulta.fecha_ultima_regla.strftime('%d/%m/%Y') if consulta.fecha_ultima_regla else ''
                }
                historial_consultas.append(consulta_data)
            resultados.append({
                'id': paciente.id,
                'nombre_completo': paciente.nombre_completo,
                'dni': paciente.dni,
                'edad': paciente.edad,
                'genero': paciente.sexo,
                'historial_consultas': historial_consultas
            })
        return jsonify(resultados)
    return jsonify([])

@bp.route('/api/get_patient_info/<int:patient_id>', methods=['GET'])
@login_required
def get_patient_info(patient_id):
    patient = filtered_pacientes_query().filter(Paciente.id == patient_id).first()
    if patient:
        # Get the latest vital signs for the patient
        latest_consulta = filtered_consultas_query().filter_by(paciente_id=patient.id).order_by(Consulta.fecha_consulta.desc()).first()
        
        signos_vitales_data = None
        if latest_consulta and latest_consulta.signos_vitales:
            # Assuming signos_vitales is a relationship that returns a single object or a list
            # If it's a list, take the first one or the most recent if there's a date field
            sv = latest_consulta.signos_vitales
            signos_vitales_data = {
                'presion_arterial': sv.presion_arterial,
                'saturacion': sv.saturacion,
                'temperatura': sv.temperatura,
                'frecuencia_respiratoria': sv.frecuencia_respiratoria,
                'frecuencia_cardiaca': sv.frecuencia_cardiaca,
                'glucosa': sv.glucosa
            }

        return jsonify({
            'id': patient.id,
            'nombre_completo': patient.nombre_completo,
            'edad': patient.edad,
            'genero': patient.sexo, # Assuming 'sexo' maps to 'genero'
            'dni': patient.dni,
            'fecha_nacimiento': patient.fecha_nacimiento.strftime('%Y-%m-%d') if patient.fecha_nacimiento else 'N/A',
            'telefono': patient.telefono,
            'direccion': patient.direccion,
            'signos_vitales': signos_vitales_data
        })
    return jsonify({}), 404

@bp.route('/get_vitals/<int:patient_id>', methods=['GET'])
@login_required
def get_vitals(patient_id):
    # Priorizar la consulta más reciente que tenga signos vitales registrados
    consulta = filtered_consultas_query().filter_by(paciente_id=patient_id)\
        .options(joinedload(Consulta.signos_vitales))\
        .order_by(Consulta.fecha_consulta.desc())\
        .first()

    if consulta and consulta.signos_vitales:
        # Asumiendo que hay una relación uno a uno o que quieres los primeros signos vitales
        vitals = consulta.signos_vitales[0] if isinstance(consulta.signos_vitales, list) else consulta.signos_vitales
        return jsonify(vitals.to_dict())
    
    return jsonify({})

@bp.route('/registrar_consulta', methods=['POST'])
@login_required
@role_required('medico', 'admin')
def registrar_consulta():
    if request.method == 'POST':
        paciente_id = request.form.get('paciente_id')
        tipo_consulta = request.form.get('tipo_consulta')
        # clinica_id ahora es opcional. Si no se envía, y el usuario es médico, usar su clínica actual
        clinica_id = request.form.get('clinica_id') or (
            str(current_user.clinica_actual_id) if getattr(current_user, 'clinica_actual_id', None) and current_user.rol == 'medico' else None
        )
        
        # Verificar datos mínimos requeridos
        if not all([paciente_id, tipo_consulta]):
            flash('Faltan datos requeridos para registrar la consulta', 'error')
            return redirect(url_for('main.recepcion'))
        
        clinica = None
        if clinica_id:
            clinica = Clinica.query.get(clinica_id)
            if not clinica:
                flash('La clínica seleccionada no existe', 'error')
                return redirect(url_for('main.recepcion'))
            # Médico solo puede registrar en su clínica actual
            if current_user.rol == 'medico':
                redirect_resp = require_clinic_selected_redirect()
                if redirect_resp:
                    return redirect_resp
                if int(clinica_id) != int(current_user.clinica_actual_id):
                    flash('Solo puede registrar consultas en su clínica actual.', 'error')
                    return redirect(url_for('main.recepcion'))
        
        try:
            # Crear la consulta
            # Evitar crear duplicado si existe en progreso
            consulta_existente = Consulta.query.filter_by(paciente_id=paciente_id, estado='en_progreso') \
                .order_by(Consulta.fecha_consulta.desc()).first()
            if consulta_existente:
                consulta = consulta_existente
            else:
                consulta = Consulta(
                paciente_id=paciente_id,
                tipo_consulta=tipo_consulta,
                clinica_id=clinica.id if clinica else None,
                medico_id=current_user.id,
                fecha_consulta=datetime.now(),
                estado='en_progreso'
                )
                db.session.add(consulta)
            
            # Registrar signos vitales si se proporcionaron
            presion_arterial = request.form.get('presion_arterial')
            frecuencia_cardiaca = request.form.get('frec_cardiaca')
            frecuencia_respiratoria = request.form.get('frec_respiratoria')
            temperatura = request.form.get('temperatura')
            saturacion = request.form.get('saturacion')
            glucosa = request.form.get('glucosa')
            
            if any([presion_arterial, frecuencia_cardiaca, temperatura, frecuencia_respiratoria, saturacion, glucosa]):
                signos_vitales = SignosVitales(
                    presion_arterial=presion_arterial,
                    frecuencia_cardiaca=frecuencia_cardiaca,
                    frecuencia_respiratoria=frecuencia_respiratoria,
                    temperatura=temperatura,
                    saturacion=saturacion,
                    glucosa=glucosa,
                    consulta=consulta
                )
                db.session.add(signos_vitales)
            
            db.session.commit()
            if clinica:
                flash(f'Consulta registrada correctamente en {clinica.nombre}', 'success')
            else:
                flash('Consulta registrada correctamente', 'success')
            
            # Redirigir a la vista de consultas
            return redirect(url_for('main.consultas'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al registrar la consulta: ' + str(e), 'error')
            
        return redirect(url_for('main.recepcion'))
    
    return redirect(url_for('main.recepcion'))

@bp.route('/registrar_paciente', methods=['POST'])
@login_required
@role_required('medico', 'admin')
def registrar_paciente():
    if request.method == 'POST':
        try:
            # Datos del paciente
            nombre_completo = request.form.get('nombre_completo')
            edad = request.form.get('edad')
            sexo = request.form.get('sexo')
            direccion = request.form.get('direccion')
            telefono = request.form.get('telefono')
            dni = request.form.get('dni')
            clinica_id = current_user.clinica_actual_id if current_user.rol == 'medico' else request.form.get('clinica_id')
            tipo_consulta = request.form.get('tipo_consulta')
            
            # Verificar datos requeridos
            if not all([nombre_completo, edad, sexo, tipo_consulta]):
                flash('Faltan datos requeridos del paciente', 'error')
                return redirect(url_for('main.recepcion'))
            
            # Validar DPI duplicado si se envió
            if dni:
                existente = Paciente.query.filter(Paciente.dni == dni).first()
                if existente:
                    flash('El DPI ya está registrado para otro paciente.', 'error')
                    return redirect(url_for('main.recepcion'))

            # Crear paciente
            paciente = Paciente(
                nombre_completo=nombre_completo,
                edad=edad,
                sexo=sexo,
                direccion=direccion,
                telefono=telefono,
                dni=dni,
                fecha_registro=datetime.utcnow()
            )
            db.session.add(paciente)
            db.session.flush()  # Para obtener el ID del paciente
            
            # Crear SIEMPRE una consulta en progreso para el nuevo paciente,
            # evitando duplicar si ya existe una en progreso (por submit doble)
            clinica_asignada_id = None
            if clinica_id:
                clinica = Clinica.query.get(clinica_id)
                if not clinica:
                    flash('La clínica seleccionada no existe', 'error')
                    return redirect(url_for('main.recepcion'))
                # Si es médico, validar su clínica
                if current_user.rol == 'medico':
                    redirect_resp = require_clinic_selected_redirect()
                    if redirect_resp:
                        return redirect_resp
                    if int(clinica_id) != int(current_user.clinica_actual_id):
                        flash('Solo puede registrar en su clínica actual.', 'error')
                        return redirect(url_for('main.recepcion'))
                clinica_asignada_id = clinica.id
            else:
                # Si no se envió clínica, usar la clínica actual del médico si existe
                if current_user.rol == 'medico' and current_user.clinica_actual_id:
                    clinica_asignada_id = current_user.clinica_actual_id

            # Verificar si ya existe una consulta en progreso reciente
            consulta_existente = Consulta.query.filter_by(paciente_id=paciente.id, estado='en_progreso') \
                .order_by(Consulta.fecha_consulta.desc()).first()
            if consulta_existente:
                consulta = consulta_existente
            else:
                consulta = Consulta(
                paciente_id=paciente.id,
                tipo_consulta=tipo_consulta,
                clinica_id=clinica_asignada_id,
                medico_id=current_user.id,
                fecha_consulta=datetime.now(),
                estado='en_progreso'
                )
                db.session.add(consulta)

            # Registrar signos vitales si se proporcionaron
            presion_arterial = request.form.get('presion_arterial')
            frecuencia_cardiaca = request.form.get('frec_cardiaca')
            frecuencia_respiratoria = request.form.get('frec_respiratoria')
            temperatura = request.form.get('temperatura')
            saturacion = request.form.get('saturacion')
            glucosa = request.form.get('glucosa')
            
            if any([presion_arterial, frecuencia_cardiaca, temperatura, frecuencia_respiratoria, saturacion, glucosa]):
                signos_vitales = SignosVitales(
                    presion_arterial=presion_arterial,
                    frecuencia_cardiaca=frecuencia_cardiaca,
                    frecuencia_respiratoria=frecuencia_respiratoria,
                    temperatura=temperatura,
                    saturacion=saturacion,
                    glucosa=glucosa,
                    consulta=consulta
                )
                db.session.add(signos_vitales)
            
            db.session.commit()
            flash(f'Paciente {nombre_completo} registrado correctamente', 'success')
            
            # Redirigir a Consultas para continuar la atención
            return redirect(url_for('main.consultas'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar el paciente: {str(e)}', 'error')
            return redirect(url_for('main.recepcion'))
    
    return redirect(url_for('main.recepcion'))

@bp.route('/clinicas')
@login_required
def clinicas():
    if current_user.rol in ['pendiente', None]:
        flash('Tu cuenta aún no ha sido aprobada por un administrador.', 'warning')
        return redirect(url_for('auth.espera_aprobacion'))
    # Si es médico y tiene clínica asignada, solo mostrar su clínica
    if current_user.rol == 'medico' and current_user.clinica_actual_id:
        clinicas = Clinica.query.filter(Clinica.id == current_user.clinica_actual_id).all()
    else:
        clinicas = Clinica.query.all()
    # Obtener el paciente en espera si existe
    paciente_en_espera = None
    paciente_id = request.args.get('paciente_id')
    if paciente_id:
        paciente_en_espera = Paciente.query.get(paciente_id)
    
    return render_template('main/clinicas.html', 
                         title='Estado de Clínicas', 
                         clinicas=clinicas,
                         paciente_en_espera=paciente_en_espera)

@bp.route('/actualizar_estado_clinica/<int:clinica_id>', methods=['GET', 'POST'])
@login_required
def actualizar_estado_clinica(clinica_id):
    if current_user.rol not in ['medico', 'medico_supervisor', 'admin']:
        flash('No tienes permiso para realizar esta acción', 'error')
        return redirect(url_for('main.clinicas'))
    
    # Obtener la clínica seleccionada
    clinica = Clinica.query.get_or_404(clinica_id)

    # Médico básico solo puede cambiar estado de su clínica
    if current_user.rol == 'medico':
        if not current_user.clinica_actual_id or int(current_user.clinica_actual_id) != int(clinica_id):
            flash('Solo puede cambiar el estado de su clínica asignada.', 'error')
            return redirect(url_for('main.clinicas'))
    
    # Verificar si es una redirección desde una consulta
    redirect_to = request.args.get('redirect_to')
    consulta_id = request.args.get('consulta_id')
    paciente_id = request.args.get('paciente_id')
    
    if redirect_to and consulta_id:
        # Estamos en el flujo de consulta médica
        consulta = Consulta.query.get_or_404(consulta_id)
        
        # Actualizar la clínica de la consulta y marcarla como ocupada
        consulta.clinica_id = clinica_id
        clinica.disponible = False
        
        # Asignar el médico actual a la consulta y actualizar su clínica actual
        consulta.medico_id = current_user.id
        # No cambiar la asignación fija del médico aquí
        
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
        
        # Si estamos marcando una clínica como ocupada
        if not nuevo_estado:
            # Solo marcar esta clínica como no disponible
            clinica.disponible = False
            
            # Si hay un paciente en espera, crear una nueva consulta
            paciente_en_espera = request.form.get('paciente_id')
            if paciente_en_espera:
                paciente = Paciente.query.get(paciente_en_espera)
                if paciente:
                    # Crear nueva consulta
                    consulta = Consulta(
                        paciente_id=paciente.id,
                        clinica_id=clinica_id,
                        medico_id=current_user.id,
                        tipo_consulta='Consulta médica',
                        fecha_consulta=datetime.now(),
                        estado='en_progreso'
                    )
                    db.session.add(consulta)
                    
                    # Verificar si hay signos vitales previos
                    ultima_consulta = Consulta.query.filter_by(paciente_id=paciente.id).order_by(Consulta.fecha_consulta.desc()).first()
                    if ultima_consulta and ultima_consulta.signos_vitales:
                        # Copiar los últimos signos vitales
                        sv_previos = ultima_consulta.signos_vitales
                        signos_vitales = SignosVitales(
                            presion_arterial=sv_previos.presion_arterial,
                            frecuencia_cardiaca=sv_previos.frecuencia_cardiaca,
                            frecuencia_respiratoria=sv_previos.frecuencia_respiratoria,
                            temperatura=sv_previos.temperatura,
                            saturacion=sv_previos.saturacion,
                            glucosa=sv_previos.glucosa,
                            consulta=consulta
                        )
                        db.session.add(signos_vitales)
                    
                    flash(f'Se ha asignado al paciente {paciente.nombre_completo} a la {clinica.nombre}', 'success')
        else:
            # Marcar únicamente esta clínica como disponible
            clinica.disponible = True
        
        # Guardar cambios
        db.session.commit()
        
        flash(f'Estado de la clínica actualizado correctamente', 'success')
        return redirect(url_for('main.clinicas'))

@bp.route('/buscar_paciente_ajax', methods=['POST'])
@login_required
def buscar_paciente_ajax():
    data = request.get_json()
    termino = data.get('termino_busqueda')
    
    if not termino:
        return jsonify({'encontrado': False, 'mensaje': 'Término de búsqueda vacío'}), 400

    # Limitar visibilidad según clínica si aplica
    base_q = filtered_pacientes_query()
    paciente = base_q.filter(
        (Paciente.nombre_completo.ilike(f'%{termino}%')) |
        (Paciente.id == termino if termino.isdigit() else False)
    ).first()

    if paciente:
        # Buscar la última consulta y sus signos vitales
        consulta = filtered_consultas_query().filter_by(paciente_id=paciente.id).order_by(Consulta.fecha_consulta.desc()).first()
        signos_vitales_data = None
        if consulta and consulta.signos_vitales:
            sv = consulta.signos_vitales
            signos_vitales_data = {
                'presion_arterial': sv.presion_arterial,
                'saturacion': sv.saturacion,
                'temperatura': sv.temperatura,
                'frecuencia_respiratoria': sv.frecuencia_respiratoria,
                'frecuencia_cardiaca': sv.frecuencia_cardiaca,
                'glucosa': sv.glucosa
            }
            
        paciente_data = {
            'id': paciente.id,
            'nombre_completo': paciente.nombre_completo,
            'edad': paciente.edad,
            'genero': paciente.sexo # Usamos 'genero' como clave pero obtenemos el valor de 'sexo'
        }
        return jsonify({'encontrado': True, 'paciente': paciente_data, 'signos_vitales': signos_vitales_data})
    else:
        return jsonify({'encontrado': False, 'mensaje': 'Paciente no encontrado'})


@bp.route('/dashboard')
@login_required
def dashboard():
    # Bloqueo para cuentas pendientes
    if current_user.rol in ['pendiente', None]:
        flash('Tu cuenta aún no ha sido aprobada por un administrador.', 'warning')
        return redirect(url_for('auth.espera_aprobacion'))
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
@role_required('medico', 'admin')
def consultas():
    if current_user.rol in ['pendiente', None]:
        flash('Tu cuenta aún no ha sido aprobada por un administrador.', 'warning')
        return redirect(url_for('auth.espera_aprobacion'))
    # Vista para el módulo de consultas médicas
    paciente_seleccionado = None
    consulta_actual = None
    # Clínicas visibles: médico solo ve su clínica
    if current_user.rol == 'medico' and current_user.clinica_actual_id:
        clinicas = Clinica.query.filter(Clinica.id == current_user.clinica_actual_id).all()
    else:
        clinicas = Clinica.query.all()
    search_form = BusquedaPacienteForm()
    
    if request.method == 'POST':
        if 'paciente_id' in request.form:
            paciente_id = request.form['paciente_id']
            paciente_seleccionado = Paciente.query.get_or_404(paciente_id)
            
            # Verificar si ya existe una consulta activa para este paciente
            consulta_actual = Consulta.query.filter_by(
                paciente_id=paciente_id,
                fecha_consulta=datetime.now().date()
            ).first()
            
            if not consulta_actual:
                consulta_actual = Consulta(
                    paciente_id=paciente_id,
                    medico_id=current_user.id,
                    fecha_consulta=datetime.now()
                )
                # Buscar una clínica disponible
                clinica_disponible = Clinica.query.filter_by(disponible=True).first()
                if clinica_disponible:
                    consulta_actual.clinica_id = clinica_disponible.id
                    clinica_disponible.disponible = False
                
                db.session.add(consulta_actual)
                db.session.commit()

        # Guardar datos del motivo de consulta
        if 'guardar_motivo_consulta' in request.form:
            consulta_id = request.form.get('consulta_id')
            consulta = Consulta.query.get_or_404(consulta_id)
            
            # Guardar motivo de consulta
            consulta.motivo_consulta = request.form.get('motivo_consulta')
            consulta.historia_enfermedad = request.form.get('historia_enfermedad')
            consulta.revision_sistemas = request.form.get('revision_sistemas')
            
            # Guardar antecedentes gineco-obstetricos
            consulta.gestas = request.form.get('gestas')
            consulta.partos = request.form.get('partos')
            consulta.abortos = request.form.get('abortos')
            consulta.hijos_vivos = request.form.get('hijos_vivos')
            consulta.hijos_muertos = request.form.get('hijos_muertos')
            
            # Convertir fecha_ultima_regla a objeto Date si existe
            fecha_ultima_regla = request.form.get('fecha_ultima_regla')
            if fecha_ultima_regla:
                try:
                    consulta.fecha_ultima_regla = datetime.strptime(fecha_ultima_regla, '%Y-%m-%d').date()
                except ValueError:
                    flash('Formato de fecha inválido para última regla', 'error')
            
            consulta.antecedentes = request.form.get('antecedentes')
            
            # Guardar examen físico
            consulta.presion_arterial = request.form.get('presion_arterial')
            consulta.frecuencia_respiratoria = request.form.get('frecuencia_respiratoria')
            consulta.temperatura = request.form.get('temperatura')
            consulta.peso = request.form.get('peso')
            consulta.talla = request.form.get('talla')
            consulta.frecuencia_cardiaca = request.form.get('frecuencia_cardiaca')
            consulta.saturacion_oxigeno = request.form.get('saturacion_oxigeno')
            consulta.imc = request.form.get('imc')
            
            db.session.commit()
            flash('Datos de la consulta guardados exitosamente', 'success')
            return redirect(url_for('main.consultas'))
    
    return render_template('main/consultas.html',
                         title='Consultas Médicas',
                         paciente_seleccionado=paciente_seleccionado,
                         consulta=consulta_actual,
                         clinicas=clinicas,
                         search_form=search_form,
                         datetime=datetime)



@bp.route('/consulta/<int:consulta_id>')
@login_required
def consulta(consulta_id):
    # Vista para una consulta específica
    consulta = Consulta.query.get_or_404(consulta_id)
    ensure_consulta_access(consulta)
    return render_template('main/consulta.html', title='Consulta Médica', consulta=consulta, paciente=consulta.paciente)

@bp.route('/consulta/<int:consulta_id>/receta-completa', methods=['GET'])
@login_required
def consulta_receta_completa(consulta_id):
    consulta = Consulta.query.get_or_404(consulta_id)
    ensure_consulta_access(consulta)
    form = RecetaForm(obj=consulta)

    return render_template('main/consulta_receta.html',
                         title='Receta Médica',
                         consulta=consulta,
                         paciente=consulta.paciente,
                         form=form)

@bp.route('/consulta/<int:consulta_id>/receta-guardar', methods=['POST'])
@login_required
@role_required('medico', 'admin')
def receta_guardar(consulta_id):
    """Guarda la receta desde JSON o form-data y devuelve JSON"""
    consulta = Consulta.query.get_or_404(consulta_id)
    # Si el usuario es médico y es el propietario de la consulta, permitir guardar
    if not (current_user.rol == 'medico' and consulta.medico_id == current_user.id):
        ensure_consulta_access(consulta)

    # Intentar obtener JSON; si no, usar form
    data = request.get_json(silent=True) or {}
    if not data:
        # fallback a form
        medicamentos_textarea = request.form.get('medicamentos', '')
        medicamento = request.form.get('medicamento', '')
        dosificacion = request.form.get('dosificacion', '')
        indicaciones = request.form.get('indicaciones', '')
        diagnostico = request.form.get('diagnostico', '') or request.form.get('diagnostico_receta', '')
    else:
        medicamentos_textarea = data.get('medicamentos', '')
        medicamento = data.get('medicamento', '')
        dosificacion = data.get('dosificacion', '')
        indicaciones = data.get('indicaciones', '')
        diagnostico = data.get('diagnostico', '') or data.get('diagnostico_receta', '')

    # Componer tratamiento: soportar textarea completo o campos separados
    if medicamentos_textarea.strip():
        tratamiento = medicamentos_textarea.strip()
    else:
        lines = []
        if medicamento.strip():
            lines.append(f"Medicamento: {medicamento.strip()}")
        if dosificacion.strip():
            lines.append(f"Dosificación: {dosificacion.strip()}")
        tratamiento = "\n".join(lines)

    # Guardar campos en la consulta
    if tratamiento:
        consulta.tratamiento = tratamiento
    consulta.indicaciones = indicaciones
    if diagnostico:
        consulta.diagnostico = diagnostico
    
    # Marcar la consulta como completada si tiene diagnóstico y tratamiento
    if consulta.diagnostico and consulta.tratamiento:
        consulta.estado = 'completada'

    db.session.commit()

    return jsonify({'success': True, 'consulta_id': consulta.id})

@bp.route('/consulta/<int:consulta_id>/diagnostico', methods=['GET', 'POST'])
@login_required
def consulta_diagnostico(consulta_id):
    consulta = Consulta.query.get_or_404(consulta_id)
    ensure_consulta_access(consulta)
    form = DiagnosticoForm()
    search_form = BusquedaPacienteForm()
    pacientes_encontrados = None

    # Cargar historial de consultas filtrado por clínica si aplica
    historial_consultas = filtered_consultas_query() \
        .filter_by(paciente_id=consulta.paciente_id) \
        .order_by(Consulta.fecha_consulta.desc()) \
        .all()

    if search_form.validate_on_submit():
        query = search_form.query.data
        if query:
            # Busca el paciente por nombre o ID
            paciente_encontrado = filtered_pacientes_query().filter(
                or_(
                    Paciente.nombre_completo.ilike(f'%{query}%'),
                    Paciente.id.like(f'%{query}%')
                )
            ).first()
            
            if paciente_encontrado:
                # Busca si hay una consulta en progreso del paciente encontrado
                consulta_en_progreso = filtered_consultas_query().filter_by(
                    paciente_id=paciente_encontrado.id, 
                    estado='en_progreso'
                ).order_by(Consulta.fecha_consulta.desc()).first()
                
                if consulta_en_progreso:
                    # Si hay una consulta en progreso, redirigir a ella
                    return redirect(url_for('main.consulta_diagnostico', consulta_id=consulta_en_progreso.id))
                else:
                    # Si no hay consulta en progreso, crear una nueva consulta
                    nueva_consulta = Consulta(
                        paciente_id=paciente_encontrado.id,
                        tipo_consulta='Seguimiento',
                        medico_id=current_user.id,
                        estado='en_progreso',
                        fecha_consulta=datetime.now()
                    )
                    db.session.add(nueva_consulta)
                    db.session.commit()
                    flash(f'Nueva consulta iniciada para {paciente_encontrado.nombre_completo}', 'success')
                    return redirect(url_for('main.consulta_diagnostico', consulta_id=nueva_consulta.id))
            else:
                flash('No se encontraron pacientes.', 'warning')
        else:
            flash('Por favor, ingrese un término de búsqueda.', 'info')
        
    if form.validate_on_submit():
        consulta.diagnostico = form.descripcion.data
        consulta.laboratorio = form.laboratorio.data
        # No marcar como completada aquí, se hará en la ruta de receta
        db.session.commit()
        flash('Diagnóstico guardado correctamente')
        return redirect(url_for('main.consulta_receta', consulta_id=consulta_id))
        
    return render_template('main/consulta_diagnostico.html', 
                          title='Diagnóstico', 
                          consulta=consulta, 
                          paciente=consulta.paciente,
                          form=form,
                          search_form=search_form,
                          pacientes_encontrados=None,
                          historial_consultas=historial_consultas)



@bp.route('/reportes_medicos')
@login_required
@role_required('medico', 'admin')
def reportes_medicos():
    """Vista principal de reportes médicos estadísticos"""
    if current_user.rol in ['pendiente', None]:
        flash('Tu cuenta aún no ha sido aprobada por un administrador.', 'warning')
        return redirect(url_for('auth.espera_aprobacion'))
    clinic_name = None
    if current_user.rol == 'medico' and current_user.clinica_actual_id:
        clinica = Clinica.query.get(current_user.clinica_actual_id)
        clinic_name = clinica.nombre if clinica else None
    return render_template('main/reportes.html', clinic_name=clinic_name)

@bp.route('/informe_medico/<int:consulta_id>')
@login_required
def informe_medico(consulta_id):
    # Vista para generar un informe médico
    consulta = Consulta.query.get_or_404(consulta_id)
    ensure_consulta_access(consulta)
    return render_template('main/informe_medico.html', title='Informe Médico', consulta=consulta, paciente=consulta.paciente)

@bp.route('/api/pacientes/buscar')
@login_required
def buscar_pacientes2():
    query = request.args.get('q', '')
    if not query or len(query) < 2:
        return jsonify([])
    
    pacientes = filtered_pacientes_query().filter(
        or_(
            Paciente.nombre_completo.ilike(f'%{query}%'),
            Paciente.id == query if query.isdigit() else False
        )
    ).limit(10).all()
    
    resultados = []
    for paciente in pacientes:
        resultados.append({
            'id': paciente.id,
            'nombre_completo': paciente.nombre_completo,
            'edad': paciente.edad,
            'sexo': paciente.sexo,
            'direccion': paciente.direccion or 'No registrada',
            'telefono': paciente.telefono or 'No registrado'
        })
    
    return jsonify(resultados)

@bp.route('/buscar_paciente_api', methods=['GET'])
@login_required
def buscar_paciente_api():
    # Endpoint para buscar un paciente por término (nombre o ID) y devolver sus datos con signos vitales
    from flask import jsonify
    termino = request.args.get('term', '')
    
    if not termino:
        return jsonify({'error': 'Término de búsqueda vacío'}), 400
    
    # Buscar por ID si es un número, o por nombre
    base_q = filtered_pacientes_query()
    if termino.isdigit():
        paciente = base_q.filter(Paciente.id == int(termino)).first()
    else:
        paciente = base_q.filter(Paciente.nombre_completo.ilike(f'%{termino}%')).first()
    
    if not paciente:
        return jsonify({'error': 'Paciente no encontrado'}), 404
    
    # Obtener la última consulta del paciente
    consulta = filtered_consultas_query().filter_by(paciente_id=paciente.id).order_by(Consulta.fecha_consulta.desc()).first()
    
    # Preparar la respuesta
    respuesta = {
        'paciente': {
            'id': paciente.id,
            'nombre_completo': paciente.nombre_completo,
            'edad': paciente.edad,
            'genero': paciente.sexo  # Usamos 'genero' como clave pero obtenemos el valor de 'sexo'
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

@bp.route('/obtener_signos_vitales/<int:paciente_id>', methods=['GET'])
@login_required
def obtener_signos_vitales(paciente_id):
    # Endpoint para obtener los signos vitales de un paciente mediante AJAX
    from flask import jsonify
    paciente = filtered_pacientes_query().filter(Paciente.id == paciente_id).first()
    if not paciente:
        return jsonify({}), 404
    
    # Obtener la última consulta del paciente
    consulta = filtered_consultas_query().filter_by(paciente_id=paciente_id).order_by(Consulta.fecha_consulta.desc()).first()
    
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
    
    # Verificar si hay una clínica disponible (médico: su clínica actual)
    if current_user.rol == 'medico' and current_user.clinica_actual_id:
        clinica_disponible = Clinica.query.get(current_user.clinica_actual_id)
    else:
        clinica_disponible = Clinica.query.filter_by(disponible=True).first()
    
    if not clinica_disponible:
        flash('No hay clínicas disponibles en este momento', 'warning')
        return redirect(url_for('main.consultas'))
    
    # Crear la consulta
    consulta = Consulta(
        paciente_id=paciente.id,
        tipo_consulta='Consulta médica',
        clinica_id=clinica_disponible.id,
        medico_id=current_user.id,
        estado='en_progreso'
    )
    
    db.session.add(consulta)
    db.session.commit()
    
    # Si es una petición AJAX, devolver JSON; de lo contrario, redirigir
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.accept_mimetypes.best == 'application/json':
        return jsonify({
            'id': consulta.id,
            'paciente_id': paciente.id,
            'fecha': consulta.fecha_consulta.strftime('%d/%m/%Y %H:%M') if consulta.fecha_consulta else '',
            'tipo_consulta': consulta.tipo_consulta,
            'estado': consulta.estado
        })
    flash(f'Consulta iniciada para {paciente.nombre_completo}', 'success')
    return redirect(url_for('main.consulta', consulta_id=consulta.id))

@bp.route('/consulta/nueva_ajax/<int:paciente_id>', methods=['POST'])
@login_required
def nueva_consulta_ajax(paciente_id):
    """Crea una consulta en progreso y devuelve JSON (flujo AJAX desde consultas.js)."""
    paciente = Paciente.query.get_or_404(paciente_id)
    if current_user.rol == 'medico' and current_user.clinica_actual_id:
        clinica_disponible = Clinica.query.get(current_user.clinica_actual_id)
    else:
        # Preferir una disponible; si no hay, tomar cualquier clínica
        clinica_disponible = Clinica.query.filter_by(disponible=True).first() or Clinica.query.first()
    
    # Reutilizar consulta EN PROGRESO si existe para evitar duplicados
    existente = Consulta.query \
        .filter_by(paciente_id=paciente.id, estado='en_progreso') \
        .order_by(Consulta.fecha_consulta.desc()) \
        .first()
    if existente:
        return jsonify({
            'success': True,
            'consulta': {
                'id': existente.id,
                'paciente_id': paciente.id,
                'fecha': existente.fecha_consulta.strftime('%d/%m/%Y %H:%M') if existente.fecha_consulta else '',
                'tipo_consulta': existente.tipo_consulta or 'Consulta médica',
                'estado': existente.estado
            }
        })
    consulta = Consulta(
        paciente_id=paciente.id,
        tipo_consulta='Consulta médica',
        clinica_id=(clinica_disponible.id if clinica_disponible else None),
        medico_id=current_user.id,
        estado='en_progreso',
        fecha_consulta=datetime.now()
    )
    db.session.add(consulta)
    db.session.commit()
    return jsonify({
        'success': True,
        'consulta': {
            'id': consulta.id,
            'paciente_id': paciente.id,
            'fecha': consulta.fecha_consulta.strftime('%d/%m/%Y %H:%M') if consulta.fecha_consulta else '',
            'tipo_consulta': consulta.tipo_consulta,
            'estado': consulta.estado
        }
    })

@bp.route('/consulta/<int:consulta_id>/motivo', methods=['POST'])
@login_required
@role_required('medico', 'admin')
def guardar_motivo_consulta(consulta_id):
    consulta = Consulta.query.get_or_404(consulta_id)
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No se recibieron datos'}), 400
            
        # Actualizar los campos de la consulta
        consulta.motivo_consulta = data.get('motivo_consulta', '')
        consulta.historia_enfermedad = data.get('historia_enfermedad', '')
        consulta.revision_sistemas = data.get('revision_sistemas', '')
        
        # Guardar antecedentes gineco-obstetricos
        consulta.gestas = data.get('gestas', '')
        consulta.partos = data.get('partos', '')
        consulta.abortos = data.get('abortos', '')
        consulta.hijos_vivos = data.get('hijos_vivos', '')
        consulta.hijos_muertos = data.get('hijos_muertos', '')
        consulta.antecedentes = data.get('antecedentes', '')
        
        # Convertir fecha_ultima_regla si existe
        fecha_ultima_regla = data.get('fecha_ultima_regla')
        if fecha_ultima_regla:
            try:
                consulta.fecha_ultima_regla = datetime.strptime(fecha_ultima_regla, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        # Guardar datos de examen físico
        consulta.presion_arterial = data.get('presion_arterial_examen', '')
        consulta.frecuencia_respiratoria = data.get('frecuencia_respiratoria_examen', '')
        consulta.temperatura = data.get('temperatura_examen', '')
        consulta.peso = data.get('peso', '')
        consulta.talla = data.get('talla', '')
        consulta.frecuencia_cardiaca = data.get('frecuencia_cardiaca_examen', '')
        consulta.saturacion_oxigeno = data.get('saturacion_oxigeno', '')
        consulta.imc = data.get('imc', '')
        
        # Actualizar timestamp de la consulta cuando se guarda sección
        # Guardar hora actual directamente (sistema ya está en Guatemala)
        consulta.fecha_consulta = datetime.now()
        db.session.commit()
        
        return jsonify({
            'message': 'Motivo de consulta guardado correctamente',
            'consulta_id': consulta.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/consulta/<int:consulta_id>/datos-generales', methods=['POST'])
@login_required
@role_required('medico', 'admin')
def guardar_datos_generales(consulta_id):
    """Guarda los datos generales del paciente asociado a la consulta"""
    consulta = Consulta.query.get_or_404(consulta_id)
    paciente = consulta.paciente
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No se recibieron datos'}), 400
        
        # Actualizar los campos del paciente
        paciente.estado_civil = data.get('estado_civil', '')
        paciente.religion = data.get('religion', '')
        paciente.escolaridad = data.get('escolaridad', '')
        paciente.ocupacion = data.get('ocupacion', '')
        paciente.procedencia = data.get('procedencia', '')
        paciente.numero_expediente = data.get('numero_expediente', '')
        # DPI (dni) con validación de unicidad si cambia
        nuevo_dni = (data.get('dni') or '').strip()
        if nuevo_dni and nuevo_dni != (paciente.dni or ''):
            existente = Paciente.query.filter(Paciente.dni == nuevo_dni, Paciente.id != paciente.id).first()
            if existente:
                return jsonify({'error': 'El DPI ya está registrado para otro paciente.'}), 400
            paciente.dni = nuevo_dni
        
        # Actualizar dirección y teléfono si se proporcionan
        if data.get('direccion'):
            paciente.direccion = data.get('direccion')
        if data.get('telefono'):
            paciente.telefono = data.get('telefono')
        
        db.session.commit()
        
        return jsonify({
            'message': 'Datos generales guardados correctamente',
            'paciente_id': paciente.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/consulta/<int:consulta_id>/diagnostico-completo', methods=['POST'])
@login_required
@role_required('medico', 'admin')
def guardar_diagnostico_completo(consulta_id):
    """Guarda el diagnóstico completo de la consulta"""
    consulta = Consulta.query.get_or_404(consulta_id)
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No se recibieron datos'}), 400
        
        # Actualizar los campos de diagnóstico
        consulta.diagnostico = data.get('diagnostico', '')
        # Crear un campo de laboratorio en el modelo si no existe (se añadirá más adelante)
        if hasattr(consulta, 'laboratorio'):
            consulta.laboratorio = data.get('laboratorio', '')
        
        # Actualizar timestamp de la consulta cuando se guarda sección
        # Guardar hora actual directamente (sistema ya está en Guatemala)
        consulta.fecha_consulta = datetime.now()
        db.session.commit()
        
        return jsonify({
            'message': 'Diagnóstico guardado correctamente',
            'consulta_id': consulta.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/consulta/<int:consulta_id>/receta-completa', methods=['POST'])
@login_required
@role_required('medico', 'admin')
def guardar_receta_completa(consulta_id):
    """Guarda la receta médica completa"""
    consulta = Consulta.query.get_or_404(consulta_id)
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No se recibieron datos'}), 400
        
        # Formatear el tratamiento con medicamentos e indicaciones
        medicamento = data.get('medicamento', '')
        dosificacion = data.get('dosificacion', '')
        indicaciones = data.get('indicaciones', '')
        
        # Crear el formato de la receta
        receta_completa = ""
        if medicamento:
            receta_completa += f"Medicamento: {medicamento}\n"
        if dosificacion:
            receta_completa += f"Dosificación: {dosificacion}\n"
        if indicaciones:
            receta_completa += f"Indicaciones: {indicaciones}\n"
        
        consulta.tratamiento = receta_completa
        
        # Actualizar timestamp de la consulta cuando se guarda sección
        # Guardar hora actual directamente (sistema ya está en Guatemala)
        consulta.fecha_consulta = datetime.now()
        db.session.commit()
        
        return jsonify({
            'message': 'Receta guardada correctamente',
            'consulta_id': consulta.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/consulta/<int:consulta_id>/guardar_todo', methods=['POST'])
@login_required
@role_required('medico', 'admin')
def guardar_consulta_completa(consulta_id):
    """Guarda en una sola llamada: motivo_consulta, diagnóstico y receta. Devuelve historial actualizado."""
    consulta = Consulta.query.get_or_404(consulta_id)
    ensure_consulta_access(consulta)

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No se recibieron datos'}), 400

        # 1) Motivo de consulta y relacionados
        consulta.motivo_consulta = data.get('motivo_consulta', consulta.motivo_consulta)
        consulta.historia_enfermedad = data.get('historia_enfermedad', consulta.historia_enfermedad)
        consulta.revision_sistemas = data.get('revision_sistemas', consulta.revision_sistemas)
        consulta.antecedentes = data.get('antecedentes', consulta.antecedentes)

        consulta.gestas = data.get('gestas', consulta.gestas)
        consulta.partos = data.get('partos', consulta.partos)
        consulta.abortos = data.get('abortos', consulta.abortos)
        consulta.hijos_vivos = data.get('hijos_vivos', consulta.hijos_vivos)
        consulta.hijos_muertos = data.get('hijos_muertos', consulta.hijos_muertos)

        fecha_ultima_regla = data.get('fecha_ultima_regla')
        if fecha_ultima_regla:
            try:
                consulta.fecha_ultima_regla = datetime.strptime(fecha_ultima_regla, '%Y-%m-%d').date()
            except Exception:
                pass

        # Examen físico opcional
        consulta.presion_arterial = data.get('presion_arterial_examen', consulta.presion_arterial)
        consulta.frecuencia_respiratoria = data.get('frecuencia_respiratoria_examen', consulta.frecuencia_respiratoria)
        consulta.temperatura = data.get('temperatura_examen', consulta.temperatura)
        consulta.peso = data.get('peso', consulta.peso)
        consulta.talla = data.get('talla', consulta.talla)
        consulta.frecuencia_cardiaca = data.get('frecuencia_cardiaca_examen', consulta.frecuencia_cardiaca)
        consulta.saturacion_oxigeno = data.get('saturacion_oxigeno', consulta.saturacion_oxigeno)
        consulta.imc = data.get('imc', consulta.imc)

        # 2) Diagnóstico
        if 'diagnostico' in data:
            consulta.diagnostico = data.get('diagnostico')
        if 'laboratorio' in data and hasattr(consulta, 'laboratorio'):
            consulta.laboratorio = data.get('laboratorio')

        # 3) Receta (tratamiento + indicaciones)
        medicamentos_text = data.get('medicamentos', '').strip()
        medicamento = data.get('medicamento', '').strip()
        dosificacion = data.get('dosificacion', '').strip()
        indicaciones = data.get('indicaciones', '').strip()

        if medicamentos_text:
            consulta.tratamiento = medicamentos_text
        else:
            receta_lines = []
            if medicamento:
                receta_lines.append(f"Medicamento: {medicamento}")
            if dosificacion:
                receta_lines.append(f"Dosificación: {dosificacion}")
            if receta_lines:
                consulta.tratamiento = "\n".join(receta_lines)

        if 'indicaciones' in data:
            consulta.indicaciones = indicaciones

        finalizar = bool(data.get('finalizar'))

        if finalizar:
            # Crear una nueva consulta como snapshot (historial)
            snapshot_clinica_id = consulta.clinica_id or (current_user.clinica_actual_id if getattr(current_user, 'clinica_actual_id', None) else None)
            nueva = Consulta(
                paciente_id=consulta.paciente_id,
                tipo_consulta=consulta.tipo_consulta or 'Consulta médica',
                clinica_id=snapshot_clinica_id,
                medico_id=current_user.id,
                fecha_consulta=datetime.now(),
                motivo_consulta=consulta.motivo_consulta,
                historia_enfermedad=consulta.historia_enfermedad,
                revision_sistemas=consulta.revision_sistemas,
                gestas=consulta.gestas,
                partos=consulta.partos,
                abortos=consulta.abortos,
                hijos_vivos=consulta.hijos_vivos,
                hijos_muertos=consulta.hijos_muertos,
                fecha_ultima_regla=consulta.fecha_ultima_regla,
                antecedentes=consulta.antecedentes,
                presion_arterial=consulta.presion_arterial,
                frecuencia_respiratoria=consulta.frecuencia_respiratoria,
                temperatura=consulta.temperatura,
                peso=consulta.peso,
                talla=consulta.talla,
                frecuencia_cardiaca=consulta.frecuencia_cardiaca,
                saturacion_oxigeno=consulta.saturacion_oxigeno,
                imc=consulta.imc,
                diagnostico=consulta.diagnostico,
                laboratorio=getattr(consulta, 'laboratorio', None),
                tratamiento=consulta.tratamiento,
                indicaciones=consulta.indicaciones,
            )
            db.session.add(nueva)
            db.session.commit()
        else:
            # Solo actualizar la consulta actual y timestamp
            consulta.fecha_consulta = datetime.now()
            db.session.commit()

        # Preparar historial (todas las consultas)
        consultas = Consulta.query \
            .filter_by(paciente_id=consulta.paciente_id) \
            .order_by(Consulta.fecha_consulta.desc()) \
            .all()

        historial = []
        for c in consultas:
            historial.append({
                'id': c.id,
                'fecha': c.fecha_consulta.strftime('%d/%m/%Y %H:%M') if c.fecha_consulta else '',
                'motivo_consulta': c.motivo_consulta or '',
                'diagnostico': c.diagnostico or '',
                'tratamiento': c.tratamiento or '',
                'indicaciones': c.indicaciones or '',
                'estado': getattr(c, 'estado', '') or '',
                'medico': c.medico.nombre_completo if c.medico else ''
            })

        return jsonify({'success': True, 'consulta_id': consulta.id, 'historial': historial})

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/consulta/<int:consulta_id>/historial', methods=['GET'])
@login_required
def obtener_historial_consulta(consulta_id):
    """Devuelve el historial (últimas 10 consultas) del paciente asociado a la consulta"""
    consulta = Consulta.query.get_or_404(consulta_id)
    ensure_consulta_access(consulta)

    # Historial del paciente filtrado por clínica para médicos
    consultas = filtered_consultas_query() \
        .filter_by(paciente_id=consulta.paciente_id) \
        .order_by(Consulta.fecha_consulta.desc()) \
        .all()

    historial = []
    for c in consultas:
        historial.append({
            'id': c.id,
            'fecha': c.fecha_consulta.strftime('%d/%m/%Y %H:%M') if c.fecha_consulta else '',
            'motivo_consulta': c.motivo_consulta or '',
            'diagnostico': c.diagnostico or '',
            'tratamiento': c.tratamiento or '',
            'indicaciones': c.indicaciones or '',
            'estado': getattr(c, 'estado', '') or '',
            'medico': c.medico.nombre_completo if c.medico else ''
        })

    return jsonify({'historial': historial})

@bp.route('/api/buscar_pacientes')
@login_required
@role_required('medico', 'admin')
def buscar_pacientes():
    """API endpoint para buscar pacientes por nombre o DNI"""
    query = request.args.get('q', '')
    if not query or len(query) < 2:
        return jsonify([])
    
    # Base query: si es médico, limitar a pacientes con consultas en su clínica
    base_q = filtered_pacientes_query()

    # Buscar pacientes que coincidan con el query en nombre completo o DNI
    pacientes = base_q.filter(
        or_(
            Paciente.nombre_completo.ilike(f'%{query}%'),
            Paciente.dni.ilike(f'%{query}%')
        )
    ).limit(10).all()
    
    # Formatear los resultados para el frontend
    resultados = []
    for paciente in pacientes:
        # Obtener consultas del paciente (filtradas por clínica si aplica)
        consultas = filtered_consultas_query().filter_by(paciente_id=paciente.id).order_by(Consulta.fecha_consulta.desc()).all()
        
        # Formatear historial de consultas
        historial_consultas = []
        signos_vitales = None
        
        for consulta in consultas:
            # Obtener signos vitales de la consulta más reciente para el panel lateral
            if not signos_vitales and consulta.signos_vitales:
                signos_vitales = consulta.signos_vitales.to_dict()
            
            # Agregar consulta al historial
            consulta_data = {
                'id': consulta.id,
                'fecha': consulta.fecha_consulta.strftime('%d/%m/%Y %H:%M') if consulta.fecha_consulta else '',
                'tipo_consulta': consulta.tipo_consulta or 'General',
                'medico': consulta.medico.nombre_completo if consulta.medico else 'No especificado',
                'motivo_consulta': consulta.motivo_consulta or '',
                'historia_enfermedad': consulta.historia_enfermedad or '',
                'revision_sistemas': consulta.revision_sistemas or '',
                'antecedentes': consulta.antecedentes or '',
                'diagnostico': consulta.diagnostico or '',
                'tratamiento': consulta.tratamiento or '',
                'estado': getattr(consulta, 'estado', '') or '',
                'signos_vitales': consulta.signos_vitales.to_dict() if consulta.signos_vitales else None,
                # Examen físico
                'presion_arterial': consulta.presion_arterial or '',
                'frecuencia_respiratoria': consulta.frecuencia_respiratoria or '',
                'temperatura': consulta.temperatura or '',
                'peso': consulta.peso or '',
                'talla': consulta.talla or '',
                'frecuencia_cardiaca': consulta.frecuencia_cardiaca or '',
                'saturacion_oxigeno': consulta.saturacion_oxigeno or '',
                'imc': consulta.imc or '',
                # Antecedentes gineco-obstétricos
                'gestas': consulta.gestas or '',
                'partos': consulta.partos or '',
                'abortos': consulta.abortos or '',
                'hijos_vivos': consulta.hijos_vivos or '',
                'hijos_muertos': consulta.hijos_muertos or '',
                'fecha_ultima_regla': consulta.fecha_ultima_regla.strftime('%d/%m/%Y') if consulta.fecha_ultima_regla else ''
            }
            historial_consultas.append(consulta_data)
        
        resultado = {
            'id': paciente.id,
            'nombre_completo': paciente.nombre_completo,
            'edad': paciente.edad,
            'genero': paciente.sexo,
            'dni': paciente.dni or 'No registrado',
            'telefono': paciente.telefono or 'No registrado',
            'direccion': paciente.direccion or 'No registrada',
            'estado_civil': paciente.estado_civil or '',
            'religion': paciente.religion or '',
            'escolaridad': paciente.escolaridad or '',
            'ocupacion': paciente.ocupacion or '',
            'procedencia': paciente.procedencia or '',
            'numero_expediente': paciente.numero_expediente or '',
            'signos_vitales': signos_vitales,
            'historial_consultas': historial_consultas,
            'total_consultas': len(historial_consultas),
            'tiene_consulta_activa': len(historial_consultas) > 0
        }
        resultados.append(resultado)
    
    return jsonify(resultados)

@bp.route('/descargar_historial_pdf/<int:paciente_id>')
@login_required
@role_required('medico', 'admin')
def descargar_historial_pdf(paciente_id):
    """Generar y descargar PDF con el historial médico completo del paciente"""
    
    if not REPORTLAB_AVAILABLE:
        flash('Error: La funcionalidad de PDF no está disponible. Instale reportlab.', 'error')
        return redirect(url_for('main.consultas'))
    
    # Obtener paciente
    paciente = Paciente.query.get_or_404(paciente_id)
    
    # Obtener consultas del paciente (filtrar por clínica si es médico)
    consultas_q = Consulta.query.filter_by(paciente_id=paciente.id)
    if current_user.rol == 'medico' and current_user.clinica_actual_id:
        consultas_q = consultas_q.filter(Consulta.clinica_id == current_user.clinica_actual_id)
    consultas = consultas_q.order_by(Consulta.fecha_consulta.desc()).all()
    
    # Crear buffer para el PDF
    buffer = io.BytesIO()
    
    # Crear documento PDF
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=inch,
        leftMargin=inch,
        topMargin=inch,
        bottomMargin=inch
    )
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.darkblue
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.darkgreen
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=12,
        spaceAfter=8,
        textColor=colors.darkred
    )
    
    # Construir contenido del PDF
    story = []
    
    # Título principal
    story.append(Paragraph("HISTORIAL MÉDICO COMPLETO", title_style))
    story.append(Spacer(1, 20))
    
    # Información del paciente
    story.append(Paragraph("INFORMACIÓN DEL PACIENTE", heading_style))
    
    paciente_info = [
        ['Nombre Completo:', paciente.nombre_completo or 'No registrado'],
        ['DPI:', paciente.dni or 'No registrado'],
        ['Edad:', f"{paciente.edad} años" if paciente.edad else 'No registrada'],
        ['Sexo:', paciente.sexo or 'No registrado'],
        ['Estado Civil:', paciente.estado_civil or 'No registrado'],
        ['Ocupación:', paciente.ocupacion or 'No registrada'],
        ['Dirección:', paciente.direccion or 'No registrada'],
        ['Teléfono:', paciente.telefono or 'No registrado'],
        ['Expediente:', paciente.numero_expediente or 'No asignado'],
        ['Fecha de Registro:', paciente.fecha_registro.strftime('%d/%m/%Y') if paciente.fecha_registro else 'No registrada']
    ]
    
    paciente_table = Table(paciente_info, colWidths=[2*inch, 4*inch])
    paciente_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(paciente_table)
    story.append(Spacer(1, 30))
    
    # Resumen de consultas
    story.append(Paragraph(f"HISTORIAL DE CONSULTAS ({len(consultas)} consulta{'s' if len(consultas) != 1 else ''})", heading_style))
    story.append(Spacer(1, 15))
    
    if not consultas:
        story.append(Paragraph("No hay consultas registradas para este paciente.", styles['Normal']))
    else:
        # Iterar por cada consulta
        for i, consulta in enumerate(consultas, 1):
            # Encabezado de consulta
            consulta_title = f"CONSULTA #{i} - {consulta.fecha_consulta.strftime('%d/%m/%Y %H:%M') if consulta.fecha_consulta else 'Fecha no registrada'}"
            story.append(Paragraph(consulta_title, subheading_style))
            
            # Información básica de la consulta
            consulta_info = [
                ['Tipo de Consulta:', consulta.tipo_consulta or 'No especificado'],
                ['Médico:', consulta.medico.nombre_completo if consulta.medico else 'No especificado'],
                ['Clínica:', consulta.clinica.nombre if consulta.clinica else 'No especificada']
            ]
            
            consulta_table = Table(consulta_info, colWidths=[2*inch, 4*inch])
            consulta_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(consulta_table)
            story.append(Spacer(1, 10))
            
            # Signos vitales si existen
            if consulta.signos_vitales:
                story.append(Paragraph("Signos Vitales:", ParagraphStyle('SignosTitle', parent=styles['Normal'], fontSize=10, textColor=colors.darkblue, fontName='Helvetica-Bold')))
                
                signos_info = [
                    ['Presión Arterial:', consulta.signos_vitales.presion_arterial or '--'],
                    ['Frecuencia Cardíaca:', f"{consulta.signos_vitales.frecuencia_cardiaca} lpm" if consulta.signos_vitales.frecuencia_cardiaca else '--'],
                    ['Temperatura:', f"{consulta.signos_vitales.temperatura}°C" if consulta.signos_vitales.temperatura else '--'],
                    ['Saturación O2:', f"{consulta.signos_vitales.saturacion}%" if consulta.signos_vitales.saturacion else '--'],
                    ['Frecuencia Respiratoria:', f"{consulta.signos_vitales.frecuencia_respiratoria} rpm" if consulta.signos_vitales.frecuencia_respiratoria else '--'],
                    ['Glucosa:', f"{consulta.signos_vitales.glucosa} mg/dl" if consulta.signos_vitales.glucosa else '--']
                ]
                
                signos_table = Table(signos_info, colWidths=[1.5*inch, 1.5*inch])
                signos_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightyellow),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ]))
                story.append(signos_table)
                story.append(Spacer(1, 10))
            
            # Motivo de consulta
            if consulta.motivo_consulta:
                story.append(Paragraph("Motivo de Consulta:", ParagraphStyle('MotivoTitle', parent=styles['Normal'], fontSize=10, textColor=colors.darkgreen, fontName='Helvetica-Bold')))
                story.append(Paragraph(consulta.motivo_consulta, styles['Normal']))
                story.append(Spacer(1, 8))
            
            # Historia de la enfermedad
            if consulta.historia_enfermedad:
                story.append(Paragraph("Historia de la Enfermedad:", ParagraphStyle('HistoriaTitle', parent=styles['Normal'], fontSize=10, textColor=colors.darkorange, fontName='Helvetica-Bold')))
                story.append(Paragraph(consulta.historia_enfermedad, styles['Normal']))
                story.append(Spacer(1, 8))
            
            # Diagnóstico
            if consulta.diagnostico:
                story.append(Paragraph("Diagnóstico:", ParagraphStyle('DiagnosticoTitle', parent=styles['Normal'], fontSize=10, textColor=colors.darkred, fontName='Helvetica-Bold')))
                story.append(Paragraph(consulta.diagnostico, styles['Normal']))
                story.append(Spacer(1, 8))
            
            # Tratamiento
            if consulta.tratamiento:
                story.append(Paragraph("Tratamiento:", ParagraphStyle('TratamientoTitle', parent=styles['Normal'], fontSize=10, textColor=colors.darkblue, fontName='Helvetica-Bold')))
                story.append(Paragraph(consulta.tratamiento, styles['Normal']))
                story.append(Spacer(1, 8))
            
            # Antecedentes si existen
            if consulta.antecedentes:
                story.append(Paragraph("Antecedentes:", ParagraphStyle('AntecedentesTitle', parent=styles['Normal'], fontSize=10, textColor=colors.purple, fontName='Helvetica-Bold')))
                story.append(Paragraph(consulta.antecedentes, styles['Normal']))
                story.append(Spacer(1, 8))
            
            # Separador entre consultas
            if i < len(consultas):
                story.append(Spacer(1, 20))
                story.append(Paragraph("─" * 80, styles['Normal']))
                story.append(Spacer(1, 20))
    
    # Removido pie de página con fecha/autor
    # Nota: La firma se dibuja solo en la última página mediante canvasmaker abajo
    
    # Construir PDF con encabezado y marca de agua
    def _watermark(canv, doc):
        import os
        candidates = ['logo_clinicas.jpg', 'logo_clinicas.JPG', 'logo_clinicas_familiares_cunori.jpg', 'logotipo-cunori-transparente.png', 'logo.png', 'logo.JPG']
        logo_path = None
        for name in candidates:
            p = os.path.join(current_app.root_path, 'static', 'img', name)
            if os.path.exists(p):
                logo_path = p
                break
        if not logo_path:
            return
        try:
            canv.saveState()
            if hasattr(canv, 'setFillAlpha'):
                canv.setFillAlpha(0.08)
            try:
                page_w, page_h = doc.pagesize
            except Exception:
                page_w, page_h = getattr(canv, '_pagesize', (letter[0], letter[1]))
            w = page_w * 0.6
            h = page_h * 0.6
            x = (page_w - w) / 2
            y = (page_h - h) / 2
            canv.drawImage(logo_path, x, y, width=w, height=h, preserveAspectRatio=True, mask='auto')
        finally:
            if hasattr(canv, 'setFillAlpha'):
                canv.setFillAlpha(1)
            canv.restoreState()
    def _header(canv, doc):
        margin = inch
        img_h = 28
        img_w = 28
        try:
            page_w, page_h = doc.pagesize
        except Exception:
            page_w, page_h = getattr(canv, '_pagesize', (letter[0], letter[1]))
        y = page_h - img_h - 10
        # logos
        left_candidates = ['logo_clinicas.jpg', 'logo_clinicas.JPG', 'logo_clinicas_familiares_cunori.jpg', 'logotipo-cunori-transparente.png', 'logo.png', 'logo.JPG']
        right_candidates = ['escudo_guatemala.png', 'logotipo-cunori-transparente.png', 'logo.JPG']
        def pick(cands):
            for nm in cands:
                p = os.path.join(current_app.root_path, 'static', 'img', nm)
                if os.path.exists(p):
                    return p
            return None
        left_path = pick(left_candidates)
        right_path = pick(right_candidates)
        try:
            canv.saveState()
            if left_path:
                canv.drawImage(left_path, margin, y, width=img_w, height=img_h, preserveAspectRatio=True, mask='auto')
            if right_path:
                canv.drawImage(right_path, page_w - margin - img_w, y, width=img_w, height=img_h, preserveAspectRatio=True, mask='auto')
            canv.setFont('Helvetica-Bold', 12)
            canv.setFillColorRGB(0.1, 0.16, 0.23)
            canv.drawCentredString(page_w/2, y + 8, 'Clínicas Familiares CUNORI-Shororagua')
            canv.setLineWidth(0.5)
            canv.setStrokeColorRGB(0.6, 0.6, 0.6)
            canv.line(margin, y - 4, page_w - margin, y - 4)
        finally:
            canv.restoreState()

    def _draw(canv, doc):
        _header(canv, doc)
        _watermark(canv, doc)

    # Dibujar bloque de firma únicamente en la última página
    from reportlab.pdfgen import canvas as rl_canvas
    class LastPageSignatureCanvas(rl_canvas.Canvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._saved_page_states = []
        def showPage(self):
            self._saved_page_states.append(dict(self.__dict__))
            self._startPage()
        def save(self):
            total = len(self._saved_page_states)
            for idx, state in enumerate(self._saved_page_states, start=1):
                self.__dict__.update(state)
                _draw(self, self)
                if idx == total:
                    self.saveState()
                    page_w, page_h = self._pagesize
                    margin = 72
                    line_w = 200
                    x1 = (page_w - line_w) / 2
                    y = margin + 40
                    self.setLineWidth(1)
                    self.line(x1, y, x1 + line_w, y)
                    self.setFont('Helvetica', 10)
                    self.drawCentredString(page_w/2, y - 14, 'Firma y sello')
                    self.setFont('Helvetica-Oblique', 10)
                    self.drawCentredString(page_w/2, y - 28, 'Médico')
                    self.restoreState()
                super().showPage()
            super().save()

    doc.build(story, canvasmaker=LastPageSignatureCanvas)
    
    # Preparar respuesta
    buffer.seek(0)
    
    # Crear nombre del archivo
    nombre_archivo = f"historial_medico_{paciente.nombre_completo.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    # Crear respuesta con el PDF
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
    
    buffer.close()
    
    return response

# ==================== RUTAS DE REPORTES MÉDICOS ESTADÍSTICOS ====================

@bp.route('/api/reportes/estadisticas_generales')
@login_required
@role_required('medico', 'admin')
def estadisticas_generales():
    """API para obtener estadísticas generales de pacientes"""
    try:
        # Alcance: si es médico, filtrar por su clínica; admin/supervisor => global
        is_medico_scoped = (current_user.rol == 'medico' and current_user.clinica_actual_id)

        # Obtener subconjunto de pacientes según alcance (IDs por consultas en la clínica)
        if is_medico_scoped:
            pacientes_ids_rows = db.session.query(Consulta.paciente_id) \
                .filter(Consulta.clinica_id == current_user.clinica_actual_id) \
                .distinct().all()
            pacientes_ids = [row[0] for row in pacientes_ids_rows if row[0] is not None]
            pacientes_base_q = Paciente.query.filter(Paciente.id.in_(pacientes_ids))
            consultas_base_q = Consulta.query.filter(Consulta.clinica_id == current_user.clinica_actual_id)
        else:
            pacientes_base_q = Paciente.query
            consultas_base_q = Consulta.query

        # Total de pacientes (según alcance)
        total_pacientes = pacientes_base_q.count()
        
        # Distribución por género (según alcance)
        pacientes_por_genero = db.session.query(
            Paciente.sexo, func.count(Paciente.id)
        )
        if is_medico_scoped:
            pacientes_por_genero = pacientes_por_genero.filter(Paciente.id.in_(pacientes_ids))
        pacientes_por_genero = pacientes_por_genero.group_by(Paciente.sexo).all()
        
        genero_data = {}
        for genero, count in pacientes_por_genero:
            genero_data[genero or 'No especificado'] = count
            
        # Distribución por edad (rangos) sobre el subconjunto de pacientes
        rangos_edad = {
            '0-5': 0, '6-10': 0, '11-15': 0, '16-20': 0, '21-25': 0,
            '26-30': 0, '31-35': 0, '36-40': 0, '41-45': 0, '46-50': 0,
            '51-55': 0, '56-60': 0, '61-65': 0, '66-70': 0, '71-75': 0,
            '76-80': 0, '81-85': 0, '86-90': 0, '90+': 0
        }
        
        pacientes = pacientes_base_q.all()
        for paciente in pacientes:
            if paciente.edad is not None:
                edad = paciente.edad
                if edad <= 5:
                    rangos_edad['0-5'] += 1
                elif edad <= 10:
                    rangos_edad['6-10'] += 1
                elif edad <= 15:
                    rangos_edad['11-15'] += 1
                elif edad <= 20:
                    rangos_edad['16-20'] += 1
                elif edad <= 25:
                    rangos_edad['21-25'] += 1
                elif edad <= 30:
                    rangos_edad['26-30'] += 1
                elif edad <= 35:
                    rangos_edad['31-35'] += 1
                elif edad <= 40:
                    rangos_edad['36-40'] += 1
                elif edad <= 45:
                    rangos_edad['41-45'] += 1
                elif edad <= 50:
                    rangos_edad['46-50'] += 1
                elif edad <= 55:
                    rangos_edad['51-55'] += 1
                elif edad <= 60:
                    rangos_edad['56-60'] += 1
                elif edad <= 65:
                    rangos_edad['61-65'] += 1
                elif edad <= 70:
                    rangos_edad['66-70'] += 1
                elif edad <= 75:
                    rangos_edad['71-75'] += 1
                elif edad <= 80:
                    rangos_edad['76-80'] += 1
                elif edad <= 85:
                    rangos_edad['81-85'] += 1
                elif edad <= 90:
                    rangos_edad['86-90'] += 1
                else:
                    rangos_edad['90+'] += 1
        
        # Total de consultas (según alcance)
        total_consultas = consultas_base_q.count()

        # Consultas por mes (últimos 6 meses) - sistema ya está en Guatemala
        now = datetime.now()
        first_of_this_month = datetime(now.year, now.month, 1)

        def add_months(dt, months):
            year = dt.year + (dt.month - 1 + months) // 12
            month = (dt.month - 1 + months) % 12 + 1
            return datetime(year, month, 1)

        month_starts = [add_months(first_of_this_month, offset) for offset in range(-5, 1)]
        meses_data = {}
        for start in month_starts:
            end = add_months(start, 1)
            q = consultas_base_q
            total = q.filter(Consulta.fecha_consulta >= start, Consulta.fecha_consulta < end).count()
            mes_nombre = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                          'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'][start.month]
            clave = f"{mes_nombre} {start.year}"
            meses_data[clave] = total
            print(f"DEBUG: Mes {clave}, consultas: {total}")
        consultas_mes_actual = list(meses_data.values())[-1] if meses_data else 0
        
        return jsonify({
            'success': True,
            'data': {
                'total_pacientes': total_pacientes,
                'total_consultas': total_consultas,
                'genero_distribucion': genero_data,
                'edad_distribucion': rangos_edad,
                'consultas_por_mes': meses_data,
                'consultas_mes_actual': consultas_mes_actual
            }
        })
        
    except Exception as e:
        print(f"Error en estadísticas generales: {e}")
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/api/reportes/enfermedades_comunes')
@login_required
@role_required('medico', 'admin')
def enfermedades_comunes():
    """API para obtener las enfermedades más comunes"""
    try:
        # Obtener diagnósticos (filtrar por clínica si es médico)
        if current_user.rol == 'medico' and current_user.clinica_actual_id:
            consultas = Consulta.query.filter(
                Consulta.diagnostico.isnot(None),
                Consulta.clinica_id == current_user.clinica_actual_id
            ).all()
        else:
            consultas = Consulta.query.filter(Consulta.diagnostico.isnot(None)).all()
        
        # Contar diagnósticos
        diagnosticos = []
        for consulta in consultas:
            if consulta.diagnostico and consulta.diagnostico.strip():
                diagnosticos.append(consulta.diagnostico.strip().lower())
        
        # Contar frecuencias
        contador_diagnosticos = Counter(diagnosticos)
        
        # Obtener los 15 más comunes
        top_diagnosticos = contador_diagnosticos.most_common(15)
        
        enfermedades_data = {}
        for diagnostico, count in top_diagnosticos:
            # Capitalizar primera letra de cada palabra
            diagnostico_formateado = ' '.join(word.capitalize() for word in diagnostico.split())
            enfermedades_data[diagnostico_formateado] = count
        
        return jsonify({
            'success': True,
            'data': enfermedades_data
        })
        
    except Exception as e:
        print(f"Error en enfermedades comunes: {e}")
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/api/reportes/problemas_por_sistemas')
@login_required
@role_required('medico', 'admin')
def problemas_por_sistemas():
    """API para obtener problemas clasificados por sistemas médicos"""
    try:
        # Definir palabras clave para cada sistema
        sistemas_keywords = {
            'Respiratorio': ['tos', 'gripe', 'resfriado', 'bronquitis', 'asma', 'neumonía', 'congestion', 'respiratorio'],
            'Cardiovascular': ['corazón', 'hipertensión', 'presión', 'cardiaco', 'cardiovascular', 'arritmia'],
            'Neurológico': ['dolor de cabeza', 'cefalea', 'migraña', 'neurológico', 'mareo', 'vértigo'],
            'Musculo Esquelético': ['dolor', 'espalda', 'articulaciones', 'músculo', 'hueso', 'artritis', 'lumbar'],
            'Gastrointestinal': ['estómago', 'digestivo', 'diarrea', 'estreñimiento', 'gastritis', 'intestinal'],
            'Genitourinario': ['urinario', 'riñón', 'vejiga', 'genital', 'infección urinaria'],
            'Endocrino': ['diabetes', 'tiroides', 'hormonal', 'endocrino', 'glucosa'],
            'Dermatológico': ['piel', 'dermatitis', 'rash', 'alergia', 'eccema'],
            'Oftalmológico': ['ojo', 'visión', 'oftalmológico', 'conjuntivitis'],
            'Otorrinolaringológico': ['oído', 'garganta', 'nariz', 'otitis', 'sinusitis'],
            'Ginecológico': ['ginecológico', 'menstrual', 'embarazo', 'pélvico'],
            'Pediátrico': ['niño', 'infantil', 'pediátrico', 'desarrollo']
        }
        
        # Obtener diagnósticos y motivos (filtrar por clínica si es médico)
        if current_user.rol == 'medico' and current_user.clinica_actual_id:
            consultas = Consulta.query.filter(
                or_(Consulta.diagnostico.isnot(None), Consulta.motivo_consulta.isnot(None)),
                Consulta.clinica_id == current_user.clinica_actual_id
            ).all()
        else:
            consultas = Consulta.query.filter(
                or_(Consulta.diagnostico.isnot(None), Consulta.motivo_consulta.isnot(None))
            ).all()
        
        # Contar por sistemas
        sistemas_count = defaultdict(int)
        
        for consulta in consultas:
            texto_consulta = ""
            if consulta.diagnostico:
                texto_consulta += consulta.diagnostico.lower() + " "
            if consulta.motivo_consulta:
                texto_consulta += consulta.motivo_consulta.lower() + " "
            
            if texto_consulta.strip():
                # Clasificar por sistema
                for sistema, keywords in sistemas_keywords.items():
                    for keyword in keywords:
                        if keyword in texto_consulta:
                            sistemas_count[sistema] += 1
                            break  # Solo contar una vez por consulta por sistema
        
        # Convertir a diccionario regular y ordenar
        sistemas_data = dict(sistemas_count)
        
        return jsonify({
            'success': True,
            'data': sistemas_data
        })
        
    except Exception as e:
        print(f"Error en problemas por sistemas: {e}")
        return jsonify({'success': False, 'error': str(e)})

@bp.route('/api/reportes/sistema_detalle/<sistema>')
@login_required
@role_required('medico', 'admin')
def sistema_detalle(sistema):
    """API para obtener detalles de un sistema específico"""
    try:
        # Definir sub-categorías por sistema
        subcategorias = {
            'Respiratorio': {
                'resfriado común': ['resfriado', 'tos', 'gripe'],
                'bronquitis': ['bronquitis'],
                'asma': ['asma'],
                'neumonía': ['neumonía'],
                'sinusitis': ['sinusitis']
            },
            'Neurológico': {
                'cefalea': ['dolor de cabeza', 'cefalea'],
                'migraña': ['migraña'],
                'mareos': ['mareo', 'vértigo']
            },
            'Musculo Esquelético': {
                'dolor lumbar': ['lumbar', 'espalda baja'],
                'artritis': ['artritis'],
                'dolor articular': ['articulaciones'],
                'dolor muscular': ['músculo', 'muscular']
            },
            'Cardiovascular': {
                'hipertensión': ['hipertensión', 'presión alta'],
                'arritmia': ['arritmia', 'palpitaciones']
            },
            'Gastrointestinal': {
                'gastritis': ['gastritis'],
                'diarrea': ['diarrea'],
                'estreñimiento': ['estreñimiento']
            }
        }
        
        if sistema not in subcategorias:
            return jsonify({'success': False, 'error': 'Sistema no encontrado'})
        
        # Obtener consultas relacionadas (filtrar por clínica si es médico)
        if current_user.rol == 'medico' and current_user.clinica_actual_id:
            consultas = Consulta.query.filter(
                or_(Consulta.diagnostico.isnot(None), Consulta.motivo_consulta.isnot(None)),
                Consulta.clinica_id == current_user.clinica_actual_id
            ).all()
        else:
            consultas = Consulta.query.filter(
                or_(Consulta.diagnostico.isnot(None), Consulta.motivo_consulta.isnot(None))
            ).all()
        
        # Contar subcategorías
        subcat_count = defaultdict(int)
        
        for consulta in consultas:
            texto_consulta = ""
            if consulta.diagnostico:
                texto_consulta += consulta.diagnostico.lower() + " "
            if consulta.motivo_consulta:
                texto_consulta += consulta.motivo_consulta.lower() + " "
            
            if texto_consulta.strip():
                for subcategoria, keywords in subcategorias[sistema].items():
                    for keyword in keywords:
                        if keyword in texto_consulta:
                            subcat_count[subcategoria] += 1
                            break
        
        return jsonify({
            'success': True,
            'data': dict(subcat_count),
            'sistema': sistema
        })
        
    except Exception as e:
        print(f"Error en detalle de sistema: {e}")
        return jsonify({'success': False, 'error': str(e)})


# ===== Vista para asignar médicos a clínicas (Supervisor/Admin) =====
@bp.route('/asignar_clinicas', methods=['GET'])
@login_required
@role_required('medico_supervisor', 'admin')
def asignar_clinicas():
    # Mostrar SOLO usuarios con rol 'medico'
    medicos = Usuario.query.filter(Usuario.rol == 'medico').order_by(asc(Usuario.nombre_completo)).all()
    clinicas = Clinica.query.order_by(asc(Clinica.nombre)).all()
    return render_template('main/asignar_clinicas.html',
                          title='Asignar Clínicas a Médicos',
                          medicos=medicos,
                          clinicas=clinicas)


@bp.route('/asignar_medico_clinica', methods=['POST'])
@login_required
@role_required('medico_supervisor', 'admin')
def asignar_medico_clinica():
    """Asigna (o desasigna) una clínica a un médico."""
    medico_id = request.form.get('medico_id', type=int)
    clinica_id_raw = request.form.get('clinica_id', default='')

    if not medico_id:
        return jsonify({'success': False, 'error': 'medico_id requerido'}), 400

    medico = Usuario.query.get(medico_id)
    if not medico:
        return jsonify({'success': False, 'error': 'Médico no encontrado'}), 404
    if medico.rol != 'medico':
        return jsonify({'success': False, 'error': 'Solo se pueden asignar clínicas a usuarios con rol médico'}), 400

    clinica_anterior_id = medico.clinica_actual_id
    clinica_nueva_id = None

    # Si clinica_id viene vacío, desasignar
    if not clinica_id_raw:
        if medico.clinica_actual_id is None:
             return jsonify({'success': True, 'message': 'El médico ya está desasignado.'})
        clinica_nueva_id = None
    else:
        try:
            clinica_nueva_id = int(clinica_id_raw)
        except ValueError:
            return jsonify({'success': False, 'error': 'clinica_id inválido'}), 400

    if clinica_anterior_id == clinica_nueva_id:
        return jsonify({'success': True, 'message': 'La clínica seleccionada es la misma que la actual.'})
    
    try:
        historial = HistorialAsignacionClinica(
            admin_id=current_user.id,
            medico_id=medico_id,
            clinica_anterior_id=clinica_anterior_id,
            clinica_nueva_id=clinica_nueva_id
        )
        db.session.add(historial)
        
        medico.clinica_actual_id = clinica_nueva_id
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error al asignar clínica: {e}")
        return jsonify({'success': False, 'error': 'Ocurrió un error al asignar la clínica.'}), 500

@bp.route('/eliminar_medico', methods=['POST'])
@login_required
@role_required('medico_supervisor', 'admin')
def eliminar_medico():
    """Elimina lógicamente un médico. NO borra pacientes ni consultas. Mantiene historial intacto."""
    medico_id = request.form.get('medico_id', type=int)
    if not medico_id:
        return jsonify({'success': False, 'error': 'medico_id requerido'}), 400
    medico = Usuario.query.get(medico_id)
    if not medico:
        return jsonify({'success': False, 'error': 'Médico no encontrado'}), 404
    if medico.rol != 'medico':
        return jsonify({'success': False, 'error': 'Solo se pueden eliminar usuarios con rol médico'}), 400
    
    clinica_anterior_id = medico.clinica_actual_id

    try:
        # Solo registrar si el médico estaba asignado a una clínica
        if clinica_anterior_id is not None:
            historial = HistorialAsignacionClinica(
                admin_id=current_user.id,
                medico_id=medico_id,
                clinica_anterior_id=clinica_anterior_id,
                clinica_nueva_id=None
            )
            db.session.add(historial)

        # Desasignar de clínica y desactivar usuario; historial/consultas permanecen
        medico.clinica_actual_id = None
        medico.activo = False
        # Opcional: cambiar rol a 'pendiente' para ocultarlo de listados operativos
        medico.rol = 'pendiente'
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ===== Cambio de rol inline (Admin/Supervisor) =====
@bp.route('/usuarios/cambiar_rol', methods=['POST'])
@login_required
@role_required('medico_supervisor', 'admin')
def cambiar_rol_usuario():
    user_id = request.form.get('user_id', type=int)
    nuevo_rol = request.form.get('rol', type=str)
    if not user_id or not nuevo_rol:
        return jsonify({'success': False, 'error': 'Parámetros incompletos'}), 400
    if nuevo_rol not in ['admin', 'medico', 'medico_supervisor', 'pendiente']:
        return jsonify({'success': False, 'error': 'Rol inválido'}), 400
    usuario = Usuario.query.get(user_id)
    if not usuario:
        return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404
    
    rol_anterior = usuario.rol
    if rol_anterior == nuevo_rol:
        return jsonify({'success': True, 'message': 'El rol seleccionado es el mismo que el actual.'})

    try:
        historial = HistorialRoles(
            admin_id=current_user.id,
            usuario_id=user_id,
            rol_anterior=rol_anterior,
            rol_nuevo=nuevo_rol
        )
        db.session.add(historial)
        usuario.rol = nuevo_rol
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error al cambiar rol: {e}")
        return jsonify({'success': False, 'error': 'Ocurrió un error al cambiar el rol.'}), 500

# ===== Historial de Cambios =====
@bp.route('/historial_cambios')
@login_required
@role_required('medico_supervisor', 'admin')
def historial_cambios():
    historial_roles = db.session.query(HistorialRoles).order_by(HistorialRoles.fecha_cambio.desc()).all()
    
    historial_clinicas = db.session.query(HistorialAsignacionClinica).options(
        db.joinedload(HistorialAsignacionClinica.clinica_anterior),
        db.joinedload(HistorialAsignacionClinica.clinica_nueva)
    ).order_by(HistorialAsignacionClinica.fecha_cambio.desc()).all()

    return render_template('main/historial_cambios.html',
                           title='Historial de Cambios',
                           historial_roles=historial_roles,
                           historial_clinicas=historial_clinicas)