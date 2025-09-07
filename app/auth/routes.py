from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlparse as url_parse
from app import db, csrf
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm, ChangeRoleForm, VerificationCodeForm
from app.models import Usuario, Consulta, HistorialRoles, VerificationCode, CodigoVerificacion
from flask import current_app
import requests
from app.email import send_password_reset_email, generate_verification_code, send_verification_code_email
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError


@bp.route('/espera_aprobacion')
@login_required
def espera_aprobacion():
    return render_template('auth/espera_aprobacion.html', title='Cuenta en revisión')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = Usuario.query.filter_by(usuario=form.usuario.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Usuario o contraseña inválidos')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)
    return render_template('auth/login.html', title='Acceder', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = Usuario(nombre_completo=form.nombre_completo.data, 
                      usuario=form.usuario.data,
                      email=form.email.data,
                      rol='pendiente',
                      clinica_actual_id=None,
                      activo=False)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Cuenta creada. Un administrador/supervisor debe aprobar tu acceso y asignarte una clínica antes de iniciar sesión.')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title='Registro', form=form)

@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = Usuario.query.filter_by(email=form.email.data).first()
        if user:
            code = generate_verification_code()
            # Upsert: si ya existe para ese email, actualizar; si no, crear
            existing = VerificationCode.query.filter_by(email=user.email).first()
            if existing:
                existing.code = str(code)
                existing.timestamp = datetime.utcnow()
            else:
                verification_code = VerificationCode(email=user.email, code=str(code))
                db.session.add(verification_code)
            db.session.commit()
            if send_verification_code_email(user, code):
                flash('Se ha enviado un correo con el código de verificación. Revise su bandeja de entrada y spam.', 'info')
            else:
                flash('Error al enviar el correo. Intente nuevamente más tarde.', 'error')
            return redirect(url_for('auth.verify_code', email=user.email))
        else:
            flash('Si el correo existe en nuestro sistema, recibirá un código de verificación.', 'info')
            return redirect(url_for('auth.verify_code'))
    return render_template('auth/reset_password_request.html', title='Restablecer Contraseña', form=form)


@bp.route('/verify_code', methods=['GET', 'POST'])
def verify_code():
    form = VerificationCodeForm()
    # Prefill email if passed as query param
    prefill_email = request.args.get('email')
    if request.method == 'GET' and prefill_email and not form.email.data:
        form.email.data = prefill_email
    if form.validate_on_submit():
        verification_code = VerificationCode.query.filter_by(email=form.email.data, code=form.code.data).first()
        if verification_code and not verification_code.is_expired():
            user = Usuario.query.filter_by(email=form.email.data).first()
            if not user:
                flash('Usuario no encontrado para ese correo.', 'error')
                return render_template('auth/verify_code.html', title='Verificar Código', form=form)
            # Generar token seguro y marcar ese registro como expirado (actualizar timestamp)
            token = user.get_reset_password_token()
            verification_code.timestamp = verification_code.timestamp - timedelta(minutes=31)
            db.session.commit()
            return redirect(url_for('auth.reset_password', token=token))
        else:
            flash('Código de verificación inválido o expirado.', 'error')
    return render_template('auth/verify_code.html', title='Verificar Código', form=form)

@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    # Verificar que el token sea válido y no haya expirado
    user = Usuario.verify_reset_password_token(token)
    if not user:
        flash('El enlace de recuperación es inválido o ha expirado. '
              'Solicite un nuevo enlace de recuperación.', 'error')
        return redirect(url_for('auth.reset_password_request'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Su contraseña ha sido actualizada exitosamente. '
              'Ya puede iniciar sesión con su nueva contraseña.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', form=form, token=token)

@bp.route('/change_role', methods=['GET'])
@login_required
def change_role():
    if current_user.rol not in ['admin', 'medico_supervisor']:
        flash('No tienes permiso para realizar esta acción')
        return redirect(url_for('main.index'))

    # Mostrar solo usuarios que requieren asignación: rol pendiente o rol medico/supervisor/admin sin activar
    # Revertido: mostrar todos los usuarios para poder gestionar roles libremente
    usuarios = Usuario.query.order_by(Usuario.nombre_completo.asc()).all()
    return render_template('auth/gestionar_roles.html', title='Gestionar Roles', usuarios=usuarios)


@bp.route('/change_role', methods=['POST'])
@login_required
def change_role_post():
    if current_user.rol not in ['admin', 'medico_supervisor']:
        return jsonify({'success': False, 'error': 'No autorizado'}), 403

    # Aceptar tanto form-url-encoded como JSON
    user_id = request.form.get('user_id', type=int)
    nuevo_rol = request.form.get('rol')
    if user_id is None or not nuevo_rol:
        data = request.get_json(silent=True) or {}
        user_id = data.get('user_id') or data.get('userId') or user_id
        try:
            user_id = int(user_id) if user_id is not None else None
        except (TypeError, ValueError):
            user_id = None
        nuevo_rol = (data.get('rol') or data.get('role') or nuevo_rol)

    if user_id is None or not nuevo_rol:
        return jsonify({'success': False, 'error': 'Parámetros incompletos'}), 400

    nuevo_rol = str(nuevo_rol).strip()
    if nuevo_rol not in ['admin', 'medico', 'medico_supervisor', 'pendiente']:
        return jsonify({'success': False, 'error': 'Rol inválido'}), 400
    
    user = Usuario.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404
    
    rol_anterior = user.rol
    if rol_anterior == nuevo_rol:
        return jsonify({'success': True, 'message': 'El rol seleccionado es el mismo que el actual.'})

    try:
        historial = HistorialRoles(
            admin_id=current_user.id,
            usuario_id=user.id,
            rol_anterior=rol_anterior,
            rol_nuevo=nuevo_rol
        )
        db.session.add(historial)
        
        user.rol = nuevo_rol
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/login-json', methods=['POST'])
@csrf.exempt
def api_login_json():
    data = request.get_json(silent=True) or {}
    username_or_email = (data.get('correo') or data.get('email') or data.get('usuario') or '').strip()
    password = (data.get('contrasena') or data.get('password') or '').strip()
    recaptcha_token = data.get('recaptcha')

    if not username_or_email or not password:
        return jsonify({'message': 'Parámetros incompletos'}), 400

    # Validación opcional de reCAPTCHA si hay SECRET y token presente
    secret = current_app.config.get('RECAPTCHA_SECRET_KEY')
    if secret and recaptcha_token:
        try:
            r = requests.post(
                'https://www.google.com/recaptcha/api/siteverify',
                data={'secret': secret, 'response': recaptcha_token},
                timeout=5
            )
            ok = bool(r.json().get('success'))
            if not ok:
                return jsonify({'message': 'Falló la verificación de reCAPTCHA'}), 403
        except Exception:
            current_app.logger.exception('Error verificando reCAPTCHA')
            return jsonify({'message': 'Error verificando reCAPTCHA'}), 500

    # Permitir login por usuario o email
    user = (Usuario.query.filter_by(usuario=username_or_email).first() or
            Usuario.query.filter_by(email=username_or_email.lower()).first())

    if user is None or not user.check_password(password):
        return jsonify({'message': 'Credenciales inválidas'}), 401

    # En este proyecto usamos sesión server-side, no JWT; devolvemos estado simple
    login_user(user, remember=True)
    return jsonify({'message': 'Inicio de sesión exitoso', 'userId': user.id, 'rol': user.rol}), 200


# ==========================
#  API JSON para frontend
# ==========================

@bp.route('/check-email', methods=['POST'])
@csrf.exempt
def api_check_email():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    if not email:
        return jsonify({'message': 'Email es requerido'}), 400
    exists = Usuario.query.filter_by(email=email).first() is not None
    return jsonify({'exists': exists}), 200


@bp.route('/send-verification-code', methods=['POST'])
@csrf.exempt
def api_send_verification_code():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    if not email:
        return jsonify({'message': 'Email es requerido'}), 400
    user = Usuario.query.filter_by(email=email).first()
    if not user:
        # Responder 200 para evitar enumeración de usuarios
        return jsonify({'message': 'Si el correo existe, se envió un código'}), 200

    try:
        # Genera un código de 6 dígitos y expira en 15 minutos
        codigo_registro = CodigoVerificacion.crear_codigo_verificacion(
            usuario_id=user.id,
            tipo='password_change',
            duracion_minutos=15
        )

        # Enviar el correo
        if send_verification_code_email(user, codigo_registro.codigo):
            return jsonify({'message': 'Código enviado correctamente al correo'}), 200
        else:
            return jsonify({'message': 'No se pudo enviar el correo'}), 500
    except Exception as e:
        current_app.logger.exception('Error enviando código de verificación')
        return jsonify({'message': 'Error interno del servidor'}), 500


@bp.route('/validate-verification-code', methods=['POST'])
@csrf.exempt
def api_validate_verification_code():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    code = (data.get('code') or '').strip()

    if not email or not code:
        return jsonify({'message': 'Parámetros incompletos'}), 400

    user = Usuario.query.filter_by(email=email).first()
    if not user:
        # Evitar enumeración de usuarios
        return jsonify({'message': 'Código inválido o expirado', 'status': 400}), 400

    # Buscar el código activo más reciente para este usuario
    registro = (CodigoVerificacion.query
                .filter_by(usuario_id=user.id, tipo='password_change', usado=False)
                .order_by(CodigoVerificacion.fecha_creacion.desc())
                .first())

    if not registro:
        return jsonify({'message': 'Código inválido o expirado', 'status': 400}), 400

    if registro.codigo != code:
        registro.incrementar_intento()
        return jsonify({'message': 'Código inválido', 'status': 400}), 400

    if not registro.es_valido():
        return jsonify({'message': 'El código ha expirado', 'status': 400}), 400

    registro.marcar_como_usado()
    return jsonify({'message': 'Código válido', 'status': 200}), 200


@bp.route('/change-password', methods=['POST'])
@csrf.exempt
def api_change_password():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    new_password = (data.get('newPassword') or '').strip()

    if not email or not new_password:
        return jsonify({'message': 'Parámetros incompletos'}), 400

    user = Usuario.query.filter_by(email=email).first()
    if not user:
        # Evitar enumeración
        return jsonify({'message': 'Operación realizada'}), 200

    try:
        user.set_password(new_password)
        db.session.commit()
        # Invalidar códigos pendientes de password_change
        CodigoVerificacion.query.filter_by(usuario_id=user.id, tipo='password_change', usado=False).update({'usado': True})
        db.session.commit()
        return jsonify({'message': 'Contraseña actualizada con éxito'}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception('Error cambiando contraseña')
        return jsonify({'message': 'Error interno del servidor'}), 500

@bp.route('/delete_user', methods=['POST'])
@login_required
def delete_user():
    if current_user.rol not in ['admin', 'medico_supervisor']:
        return jsonify({'success': False, 'error': 'No autorizado'}), 403

    data = request.get_json()
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'success': False, 'error': 'ID de usuario no proporcionado'}), 400

    user = Usuario.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404
    
    if user.id == current_user.id:
        return jsonify({'success': False, 'error': 'No puedes eliminar tu propia cuenta'}), 400

    try:
        # Desvincular las consultas del médico antes de eliminarlo
        consultas_asociadas = Consulta.query.filter_by(medico_id=user.id).all()
        for consulta in consultas_asociadas:
            consulta.medico_id = None
        
        db.session.delete(user)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500