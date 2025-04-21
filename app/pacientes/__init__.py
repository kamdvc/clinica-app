from flask import Blueprint

bp = Blueprint('pacientes', __name__)

from app.pacientes import routes