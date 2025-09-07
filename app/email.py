from flask import render_template, current_app
from flask_mail import Message
from app import mail
import random


def generate_verification_code():
    """Generates a random 4-digit verification code."""
    return random.randint(1000, 9999)


def send_verification_code_email(user, code):
    """Sends an email with a verification code for password reset."""
    # Bypass real sending in development/testing
    if current_app.config.get('MAIL_USERNAME') == '' or current_app.config.get('TESTING', False):
        current_app.logger.info(f'Código de verificación para {user.email}: {code}')
        return True
    subject = '[Clínica] Código de Verificación para Restablecer Contraseña'
    text_body = f'''Estimado/a {user.nombre_completo},

Ha solicitado restablecer su contraseña en el Sistema de Clínica.

Su código de verificación es: {code}

Si no solicitó este cambio, por favor ignore este correo.

Atentamente,
Equipo del Sistema de Clínica
'''
    html_body = f'''
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #2c3e50;">Código de Verificación</h2>
        <p>Estimado/a <strong>{user.nombre_completo}</strong>,</p>
        <p>Ha solicitado restablecer su contraseña en el Sistema de Clínica.</p>
        <p>Su código de verificación es: <strong>{code}</strong></p>
        <p>Si no solicitó este cambio, por favor ignore este correo.</p>
        <p>Atentamente,<br>Equipo del Sistema de Clínica</p>
    </div>
    '''
    return send_email(
        subject,
        current_app.config['MAIL_DEFAULT_SENDER'],
        [user.email],
        text_body,
        html_body
    )


def send_email(subject, sender, recipients, text_body, html_body):
    """Función auxiliar para enviar emails"""
    try:
        msg = Message(subject, sender=sender, recipients=recipients)
        msg.body = text_body
        msg.html = html_body
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f'Error enviando email: {str(e)}')
        return False


def send_password_reset_email(user):
    """Envía email de recuperación de contraseña con token seguro"""
    token = user.get_reset_password_token()
    
    # Para desarrollo local, mostrar el token en lugar de enviar email
    if current_app.config.get('MAIL_USERNAME') == '' or current_app.config.get('TESTING', False):
        current_app.logger.info(f'Token de recuperación para {user.email}: {token}')
        # Simular envío exitoso en desarrollo
        return True
    
    subject = '[Clínica] Recuperar Contraseña'
    
    # Crear URL completa para reset
    from flask import url_for
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    
    # Cuerpo del email en texto plano
    text_body = f'''Estimado/a {user.nombre_completo},

Ha solicitado restablecer su contraseña en el Sistema de Clínica.

Para restablecer su contraseña, haga clic en el siguiente enlace:
{reset_url}

Si no solicitó este cambio, por favor ignore este correo.

IMPORTANTE: Este enlace expirará en 30 minutos por seguridad.

Atentamente,
Equipo del Sistema de Clínica
'''

    # Cuerpo del email en HTML
    html_body = f'''
    <html>
        <body>
            <h2>Recuperación de Contraseña</h2>
            <p>Estimado/a <strong>{user.nombre_completo}</strong>,</p>
            
            <p>Ha solicitado restablecer su contraseña en el Sistema de Clínica.</p>
            
            <p>Para restablecer su contraseña, haga clic en el siguiente enlace:</p>
            <p><a href="{reset_url}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Restablecer Contraseña</a></p>
            
            <p><strong>IMPORTANTE:</strong> Este enlace expirará en 30 minutos por seguridad.</p>
            
            <p>Si no solicitó este cambio, por favor ignore este correo.</p>
            
            <p>Atentamente,<br>
            Equipo del Sistema de Clínica</p>
        </body>
    </html>
    ''' f'''
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #2c3e50;">Recuperación de Contraseña</h2>
        
        <p>Estimado/a <strong>{user.nombre_completo}</strong>,</p>
        
        <p>Ha solicitado restablecer su contraseña en el Sistema de Clínica.</p>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_url}" 
               style="background-color: #3498db; color: white; padding: 12px 30px; 
                      text-decoration: none; border-radius: 5px; display: inline-block;">
                Restablecer Contraseña
            </a>
        </div>
        
        <p style="color: #e74c3c; font-weight: bold;">
            ⏰ IMPORTANTE: Este enlace expirará en 30 minutos por seguridad.
        </p>
        
        <p>Si no solicitó este cambio, por favor ignore este correo.</p>
        
        <hr style="margin: 30px 0; border: none; border-top: 1px solid #ecf0f1;">
        
        <p style="color: #7f8c8d; font-size: 12px;">
            Atentamente,<br>
            Equipo del Sistema de Clínica
        </p>
    </div>
    '''
    
    return send_email(
        subject,
        current_app.config['MAIL_DEFAULT_SENDER'],
        [user.email],
        text_body,
        html_body
    )







