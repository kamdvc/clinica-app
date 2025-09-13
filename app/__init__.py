from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from config import Config
from datetime import timedelta

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor inicie sesión para acceder a esta página.'
csrf = CSRFProtect()
mail = Mail()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Configuración del tiempo de vida de la sesión
    app.permanent_session_lifetime = timedelta(seconds=app.config['PERMANENT_SESSION_LIFETIME'])

    @app.before_request
    def make_session_permanent():
        session.permanent = True

    # Asegurar existencia de directorio de backups
    from pathlib import Path
    backup_dir = app.config.get('BACKUP_DIR')
    if backup_dir:
        Path(backup_dir).mkdir(parents=True, exist_ok=True)
    
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from app.pacientes import bp as pacientes_bp
    app.register_blueprint(pacientes_bp, url_prefix='/pacientes')
    
    from app.reportes import bp as reportes_bp
    app.register_blueprint(reportes_bp, url_prefix='/reportes')
    
    return app

from app import models