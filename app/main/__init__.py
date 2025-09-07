from flask import Blueprint

bp = Blueprint('main', __name__)

# Importar los módulos después de que el blueprint (bp) ha sido creado
# para evitar importaciones circulares.
from . import routes
from . import pdf_reports
from . import plot_generator
