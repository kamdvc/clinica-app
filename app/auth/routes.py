from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app import db
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm
from app.models import Usuario

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.recepcion'))
    form = LoginForm()
    if form.validate_on_submit():
        user = Usuario.query.filter_by(usuario=form.usuario.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Usuario o contraseña inválidos')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.recepcion')
        return redirect(next_page)
    return render_template('auth/login.html', title='Acceder', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.recepcion'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = Usuario(nombre_completo=form.nombre_completo.data, 
                      usuario=form.usuario.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('¡Felicidades, ahora eres un usuario registrado!')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title='Registro', form=form)

@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.recepcion'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = Usuario.query.filter_by(usuario=form.usuario.data).first()
        if user:
            # Aquí normalmente enviaríamos un email, pero para simplificar
            # solo redirigimos a la página de reseteo
            flash('Se ha enviado un correo con instrucciones para restablecer su contraseña')
            return redirect(url_for('auth.reset_password', token='dummy-token'))
        else:
            flash('Usuario no encontrado')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password_request.html',
                           title='Restablecer Contraseña', form=form)

@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.recepcion'))
    # Aquí normalmente verificaríamos el token
    # pero para simplificar, permitimos cualquier token
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = Usuario.query.filter_by(usuario=form.usuario.data).first()
        if user:
            user.set_password(form.password.data)
            db.session.commit()
            flash('Su contraseña ha sido actualizada.')
            return redirect(url_for('auth.login'))
        else:
            flash('Usuario no encontrado')
            return redirect(url_for('auth.reset_password_request'))
    return render_template('auth/reset_password.html', form=form)