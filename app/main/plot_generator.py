import matplotlib
matplotlib.use('Agg')  # Configurar el backend ANTES de importar pyplot
import matplotlib.pyplot as plt
import io
from app import db
from app.models import Paciente, Consulta
from sqlalchemy import func, or_
from collections import Counter
import datetime
from typing import Optional

def _pacientes_ids_por_clinica(clinica_id: Optional[int]) -> list[int]:
    if not clinica_id:
        return []
    rows = db.session.query(Consulta.paciente_id).filter(Consulta.clinica_id == clinica_id).distinct().all()
    return [r[0] for r in rows if r[0] is not None]


def plot_genero(clinica_id: Optional[int] = None):
    """Genera un gráfico de pastel de la distribución de pacientes por género.
    Si se pasa clinica_id, limita a pacientes con consultas en esa clínica.
    """
    base_q = db.session.query(Paciente.sexo, func.count(Paciente.id))
    if clinica_id:
        ids = _pacientes_ids_por_clinica(clinica_id)
        if not ids:
            return None
        base_q = base_q.filter(Paciente.id.in_(ids))
    genero_dist = dict(base_q.group_by(Paciente.sexo).all())
    
    # Asegurarse de que haya datos
    if not genero_dist:
        return None

    labels = [k for k in genero_dist.keys() if k is not None]
    sizes = [v for k, v in genero_dist.items() if k is not None]
    
    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    plt.title('Distribución de Pacientes por Género')
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)
    return buf

def plot_edades_rangos(clinica_id: Optional[int] = None):
    """Genera un gráfico de barras de la distribución de pacientes por rango de edad
    usando los mismos rangos que la UI. Respeta clinica_id si se proporciona.
    """
    if clinica_id:
        ids = _pacientes_ids_por_clinica(clinica_id)
        pacientes = Paciente.query.filter(Paciente.id.in_(ids)).all() if ids else []
    else:
        pacientes = Paciente.query.all()
    edades = [p.edad for p in pacientes if p.edad is not None]
    
    if not edades:
        return None

    # Definir los mismos rangos que en la API/UI
    rangos = [
        (0, 5), (6, 10), (11, 15), (16, 20), (21, 25), (26, 30),
        (31, 35), (36, 40), (41, 45), (46, 50), (51, 55), (56, 60),
        (61, 65), (66, 70), (71, 75), (76, 80), (81, 85), (86, 90)
    ]
    labels = [f'{a}-{b}' for a, b in rangos] + ['90+']

    dist_edades = Counter({label: 0 for label in labels})
    for edad in edades:
        placed = False
        for a, b in rangos:
            if a <= edad <= b:
                dist_edades[f'{a}-{b}'] += 1
                placed = True
                break
        if not placed and edad > 90:
            dist_edades['90+'] += 1

    sorted_labels = labels
    sorted_values = [dist_edades[lbl] for lbl in sorted_labels]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(sorted_labels, sorted_values)
    plt.xticks(rotation=45, ha="right")
    plt.title('Rango de Edades de Pacientes')
    plt.xlabel('Rango de Edad')
    plt.ylabel('Número de Pacientes')
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)
    return buf

def plot_consultas_mes(clinica_id: Optional[int] = None):
    """Genera un gráfico de línea de las consultas en los últimos 6 meses."""
    now = datetime.datetime.now()
    first_of_this_month = datetime.datetime(now.year, now.month, 1)

    def add_months(dt: datetime.datetime, months: int) -> datetime.datetime:
        year = dt.year + (dt.month - 1 + months) // 12
        month = (dt.month - 1 + months) % 12 + 1
        return datetime.datetime(year, month, 1)

    # Construir los inicios de los últimos 6 meses (incluyendo el mes actual)
    month_starts = [add_months(first_of_this_month, offset) for offset in range(-5, 1)]

    labels = []
    values = []
    for start in month_starts:
        end = add_months(start, 1)
        # Contar consultas cuyo timestamp cae en [start, end)
        q = db.session.query(func.count(Consulta.id)) \
            .filter(Consulta.fecha_consulta >= start) \
            .filter(Consulta.fecha_consulta < end)
        if clinica_id:
            q = q.filter(Consulta.clinica_id == clinica_id)
        count = q.scalar() or 0
        labels.append(start.strftime('%Y-%m'))
        values.append(count)

    # Si todos son cero, no graficar
    if not any(values):
        return None

    fig, ax = plt.subplots()
    ax.plot(labels, values, marker='o')
    plt.title('Consultas en los Últimos 6 Meses')
    plt.xlabel('Mes')
    plt.ylabel('Número de Consultas')
    plt.grid(True)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)
    return buf


def plot_enfermedades_comunes(clinica_id: Optional[int] = None, top_n: int = 10):
    """Genera un gráfico de barras con las enfermedades más comunes.
    Respeta el alcance por clínica si se proporciona clinica_id.
    """
    q = Consulta.query.filter(Consulta.diagnostico.isnot(None))
    if clinica_id:
        q = q.filter(Consulta.clinica_id == clinica_id)
    diagnos = [ (c.diagnostico or '').strip().lower() for c in q.all() if (c.diagnostico or '').strip() ]
    if not diagnos:
        return None

    conteo = Counter(diagnos).most_common(top_n)
    labels = [' '.join(w.capitalize() for w in k.split()) for k, _ in conteo]
    values = [v for _, v in conteo]

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.barh(labels, values, color='#17a2b8')
    ax.invert_yaxis()
    plt.title('Enfermedades Más Comunes')
    plt.xlabel('Casos')
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)
    return buf


def plot_problemas_por_sistemas(clinica_id: Optional[int] = None):
    """Genera un gráfico de barras para problemas por sistemas médicos.
    Usa diagnóstico, motivo y revisión por sistemas para clasificar.
    """
    sistemas_keywords = {
        'Respiratorio': ['tos', 'gripe', 'resfriado', 'bronquitis', 'asma', 'neumonía', 'congestion', 'respiratorio'],
        'Cardiovascular': ['corazón', 'hipertensión', 'presión', 'cardiaco', 'cardiovascular', 'arritmia', 'palpitaciones'],
        'Neurológico': ['dolor de cabeza', 'cefalea', 'migraña', 'neurológico', 'mareo', 'vértigo'],
        'Musculo Esquelético': ['dolor', 'espalda', 'articulaciones', 'músculo', 'hueso', 'artritis', 'lumbar'],
        'Gastrointestinal': ['estómago', 'digestivo', 'diarrea', 'estreñimiento', 'gastritis', 'intestinal', 'dolor abdominal'],
        'Genitourinario': ['urinario', 'riñón', 'vejiga', 'genital', 'infección urinaria', 'disuria', 'polaquiuria'],
        'Endocrino': ['diabetes', 'tiroides', 'hormonal', 'endocrino', 'glucosa'],
        'Dermatológico': ['piel', 'dermatitis', 'rash', 'alergia', 'eccema', 'erupción', 'acné'],
        'Oftalmológico': ['ojo', 'visión', 'oftalmológico', 'conjuntivitis'],
        'Otorrinolaringológico': ['oído', 'garganta', 'nariz', 'otitis', 'sinusitis'],
        'Ginecológico': ['ginecológico', 'menstrual', 'embarazo', 'pélvico'],
        'Pediátrico': ['niño', 'infantil', 'pediátrico', 'desarrollo']
    }

    q = Consulta.query.filter(
        or_(
            Consulta.diagnostico.isnot(None),
            Consulta.motivo_consulta.isnot(None),
            Consulta.revision_sistemas.isnot(None)
        )
    )
    if clinica_id:
        q = q.filter(Consulta.clinica_id == clinica_id)

    sistemas_count = Counter()
    for c in q.all():
        texto = ' '.join([
            (c.diagnostico or '').lower(),
            (c.motivo_consulta or '').lower(),
            (c.revision_sistemas or '').lower()
        ])
        if not texto.strip():
            continue
        for sistema, keywords in sistemas_keywords.items():
            for kw in keywords:
                if kw in texto:
                    sistemas_count[sistema] += 1
                    break

    if not sistemas_count:
        return None

    labels = list(sistemas_count.keys())
    values = [sistemas_count[l] for l in labels]

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.barh(labels, values, color='#FF9F40')
    ax.invert_yaxis()
    plt.title('Problemas por Sistemas Médicos')
    plt.xlabel('Casos')
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)
    return buf
