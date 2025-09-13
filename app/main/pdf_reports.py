from flask import flash, redirect, url_for, send_file, abort, current_app
from flask_login import login_required, current_user
from app.main import bp
from app.models import Paciente, Consulta
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfgen import canvas as rl_canvas
import io
from datetime import datetime
import os
from zoneinfo import ZoneInfo

# Importar generadores de gráficos
from app.main.plot_generator import plot_genero, plot_edades_rangos, plot_consultas_mes, plot_enfermedades_comunes, plot_problemas_por_sistemas

# Importar decorador de roles y variable de disponibilidad de ReportLab
from .routes import role_required, REPORTLAB_AVAILABLE

# Helper seguro para obtener fecha en Guatemala (con fallback si no existe tzdata)
def _fecha_guatemala_str(formato='%d/%m/%Y'):
    try:
        return datetime.now(ZoneInfo('America/Guatemala')).strftime(formato)
    except Exception:
        # Fallback: hora local del sistema
        return datetime.now().strftime(formato)

@bp.route('/exportar_reportes_pdf')
@login_required
@role_required('medico', 'admin')
def exportar_reportes_pdf():
    """Genera un PDF con un resumen de los reportes estadísticos."""
    if not REPORTLAB_AVAILABLE:
        flash('La librería ReportLab es necesaria para generar PDFs.', 'error')
        return redirect(url_for('main.reportes_medicos'))

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()

    # Título
    story.append(Paragraph("Reportes Médicos Estadísticos", styles['h1']))
    story.append(Spacer(1, 0.2 * inch))

    # Alcance igual al de la UI
    is_medico_scoped = getattr(current_user, 'rol', None) == 'medico' and getattr(current_user, 'clinica_actual_id', None)
    if is_medico_scoped:
        clinica_scope_id = int(current_user.clinica_actual_id)
        # Subconjunto de pacientes por consultas en la clínica
        pacientes_ids = [row[0] for row in 
                         Consulta.query.with_entities(Consulta.paciente_id)
                         .filter(Consulta.clinica_id == clinica_scope_id)
                         .distinct()
                         .all()
                         if row[0] is not None]
        pacientes_base_q = Paciente.query.filter(Paciente.id.in_(pacientes_ids))
        consultas_base_q = Consulta.query.filter(Consulta.clinica_id == clinica_scope_id)
    else:
        clinica_scope_id = None
        pacientes_base_q = Paciente.query
        consultas_base_q = Consulta.query

    # Resumen de estadísticas (coherente con la UI y el alcance)
    story.append(Paragraph("Resumen General", styles['h2']))
    total_pacientes = pacientes_base_q.count()
    total_consultas = consultas_base_q.count()
    story.append(Paragraph(f"<b>Total de Pacientes Registrados:</b> {total_pacientes}", styles['Normal']))
    story.append(Paragraph(f"<b>Total de Consultas Realizadas:</b> {total_consultas}", styles['Normal']))
    story.append(Spacer(1, 0.3 * inch))

    # Gráfico de Distribución por Género
    story.append(Paragraph("Distribución de Pacientes por Género", styles['h2']))
    gender_plot_buf = plot_genero(clinica_scope_id)
    if gender_plot_buf:
        story.append(Image(gender_plot_buf, width=4*inch, height=3*inch))
    story.append(Spacer(1, 0.2 * inch))

    # Gráfico de Rango de Edades (mismos rangos que UI)
    story.append(Paragraph("Rango de Edades de Pacientes", styles['h2']))
    edades_plot_buf = plot_edades_rangos(clinica_scope_id)
    if edades_plot_buf:
        story.append(Image(edades_plot_buf, width=6*inch, height=4*inch))
    story.append(Spacer(1, 0.2 * inch))

    # Gráfico de Consultas por Mes
    story.append(Paragraph("Consultas en los Últimos 6 Meses", styles['h2']))
    consultas_plot_buf = plot_consultas_mes(clinica_scope_id)
    if consultas_plot_buf:
        story.append(Image(consultas_plot_buf, width=6*inch, height=4*inch))

    # Enfermedades más comunes (alineado con UI)
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("Enfermedades Más Frecuentes", styles['h2']))
    enf_buf = plot_enfermedades_comunes(clinica_scope_id)
    if enf_buf:
        story.append(Image(enf_buf, width=6*inch, height=4*inch))

    # Problemas por sistemas médicos (alineado con UI)
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("Problemas por Sistemas Médicos", styles['h2']))
    sist_buf = plot_problemas_por_sistemas(clinica_scope_id)
    if sist_buf:
        story.append(Image(sist_buf, width=6*inch, height=4*inch))

    # Construir el PDF
    # Marca de agua (opcional para este PDF de reportes generales)
    def _watermark(canv, doc):
        # Buscar logo de marca de agua con nombres comunes
        candidates = [
            'logo_clinicas.jpg',
            'logo_clinicas.JPG',
            'logo_clinicas_familiares_cunori.jpg',
            'logotipo-cunori-transparente.png',
            'logo.png',
            'logo.JPG'
        ]
        logo_path = None
        for name in candidates:
            path_try = os.path.join(current_app.root_path, 'static', 'img', name)
            if os.path.exists(path_try):
                logo_path = path_try
                break
        if not logo_path:
            return
        try:
            canv.saveState()
            # Intentar transparencia si está disponible
            if hasattr(canv, 'setFillAlpha'):
                canv.setFillAlpha(0.08)
            page_w, page_h = doc.pagesize
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
        left_candidates = [
            'logo_clinicas.jpg',
            'logo_clinicas.JPG',
            'logo_clinicas_familiares_cunori.jpg',
            'logotipo-cunori-transparente.png',
            'logo.png',
            'logo.JPG'
        ]
        right_candidates = [
            'escudo_guatemala.png',
            'logotipo-cunori-transparente.png',
            'logo.JPG'
        ]
        left_path = None
        right_path = None
        for nm in left_candidates:
            p = os.path.join(current_app.root_path, 'static', 'img', nm)
            if os.path.exists(p):
                left_path = p
                break
        for nm in right_candidates:
            p = os.path.join(current_app.root_path, 'static', 'img', nm)
            if os.path.exists(p):
                right_path = p
                break
        page_w, page_h = doc.pagesize
        margin = 36
        img_h = 28
        img_w = 28
        y = page_h - img_h - 10
        try:
            canv.saveState()
            if left_path:
                canv.drawImage(left_path, margin, y, width=img_w, height=img_h, preserveAspectRatio=True, mask='auto')
            if right_path:
                canv.drawImage(right_path, page_w - margin - img_w, y, width=img_w, height=img_h, preserveAspectRatio=True, mask='auto')
            canv.setFont('Helvetica-Bold', 12)
            canv.setFillColorRGB(0.1, 0.16, 0.23)
            canv.drawCentredString(page_w/2, y + 8, 'Clínicas Familiares CUNORI-Shororagua')
            # Línea bajo encabezado
            canv.setLineWidth(0.5)
            canv.setStrokeColorRGB(0.6, 0.6, 0.6)
            canv.line(margin, y - 4, page_w - margin, y - 4)
        finally:
            canv.restoreState()

    def _draw(canv, doc):
        _header(canv, doc)
        _watermark(canv, doc)

    doc.build(story, onFirstPage=_draw, onLaterPages=_draw)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name='reportes_estadisticos.pdf',
        mimetype='application/pdf'
    )

@bp.route('/generar_receta_pdf/<int:consulta_id>')
@login_required
@role_required('medico', 'admin')
def generar_receta_pdf(consulta_id):
    """Genera un PDF para una receta médica específica."""
    if not REPORTLAB_AVAILABLE:
        flash('La librería ReportLab es necesaria para generar PDFs.', 'error')
        return redirect(url_for('main.consultas'))

    consulta = Consulta.query.get_or_404(consulta_id)
    paciente = consulta.paciente
    medico = consulta.medico

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    story = []
    styles = getSampleStyleSheet()
    
    # Estilo para el cuerpo del texto
    body_style = ParagraphStyle(name='Body', parent=styles['Normal'], spaceAfter=10)
    center_body = ParagraphStyle(name='CenterBody', parent=body_style, alignment=TA_CENTER)
    
    # Encabezado
    story.append(Paragraph("RECETA MÉDICA", styles['h1']))
    story.append(Spacer(1, 0.25 * inch))

    # Información del Paciente y Fecha
    paciente_info_style = styles['Normal']
    paciente_info = [
        [Paragraph(f"<b>Paciente:</b> {paciente.nombre_completo}", paciente_info_style), Paragraph(f"<b>Fecha:</b> {_fecha_guatemala_str()}", paciente_info_style)],
        [Paragraph(f"<b>Edad:</b> {paciente.edad} años", paciente_info_style), ""]
    ]
    paciente_table = Table(paciente_info, colWidths=[3.5*inch, 2.5*inch])
    paciente_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(paciente_table)
    story.append(Spacer(1, 0.3 * inch))
    
    # Diagnóstico
    story.append(Paragraph("<u>Diagnóstico:</u>", body_style))
    diagnostico_texto = consulta.diagnostico or "No especificado"
    story.append(Paragraph(diagnostico_texto, body_style))
    story.append(Spacer(1, 0.2 * inch))

    # Parsear tratamiento en medicamento y dosificación
    medicamento_texto = None
    dosificacion_texto = None
    if consulta.tratamiento:
        for raw_line in consulta.tratamiento.splitlines():
            line = raw_line.strip()
            lower = line.lower()
            if lower.startswith('medicamento:'):
                medicamento_texto = line.split(':', 1)[1].strip()
            elif lower.startswith('dosificación:') or lower.startswith('dosificacion:'):
                dosificacion_texto = line.split(':', 1)[1].strip()
            elif not medicamento_texto and line:
                # Soportar casos donde se guardó un solo texto en tratamiento
                medicamento_texto = line
    
    # Medicamentos (solo nombre)
    story.append(Paragraph("<u>Medicamentos:</u>", body_style))
    story.append(Paragraph(medicamento_texto or "No especificado", body_style))
    story.append(Spacer(1, 0.2 * inch))

    # Dosificación en sección separada
    story.append(Paragraph("<u>Dosificación:</u>", body_style))
    story.append(Paragraph(dosificacion_texto or "No especificado", body_style))
    story.append(Spacer(1, 0.2 * inch))

    # Indicaciones
    story.append(Paragraph("<u>Indicaciones:</u>", body_style))
    indicaciones_texto = consulta.indicaciones.replace('\n', '<br/>') if consulta.indicaciones else "No especificado"
    story.append(Paragraph(indicaciones_texto, body_style))
    story.append(Spacer(1, 0.5 * inch))

    # (Se dibuja la firma solo en la última página via canvasmaker)

    # Marca de agua
    def _watermark(canv, doc):
        candidates = [
            'logo_clinicas.jpg',
            'logo_clinicas.JPG',
            'logo_clinicas_familiares_cunori.jpg',
            'logotipo-cunori-transparente.png',
            'logo.png',
            'logo.JPG'
        ]
        logo_path = None
        for name in candidates:
            path_try = os.path.join(current_app.root_path, 'static', 'img', name)
            if os.path.exists(path_try):
                logo_path = path_try
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
            w = page_w * 0.55
            h = page_h * 0.55
            x = (page_w - w) / 2
            y = (page_h - h) / 2
            canv.drawImage(logo_path, x, y, width=w, height=h, preserveAspectRatio=True, mask='auto')
        finally:
            if hasattr(canv, 'setFillAlpha'):
                canv.setFillAlpha(1)
            canv.restoreState()

    def _header(canv, doc):
        left_candidates = [
            'logo_clinicas.jpg',
            'logo_clinicas.JPG',
            'logo_clinicas_familiares_cunori.jpg',
            'logotipo-cunori-transparente.png',
            'logo.png',
            'logo.JPG'
        ]
        right_candidates = [
            'escudo_guatemala.png',
            'logotipo-cunori-transparente.png',
            'logo.JPG'
        ]
        left_path = None
        right_path = None
        for nm in left_candidates:
            p = os.path.join(current_app.root_path, 'static', 'img', nm)
            if os.path.exists(p):
                left_path = p
                break
        for nm in right_candidates:
            p = os.path.join(current_app.root_path, 'static', 'img', nm)
            if os.path.exists(p):
                right_path = p
                break
        try:
            page_w, page_h = doc.pagesize
        except Exception:
            page_w, page_h = getattr(canv, '_pagesize', (letter[0], letter[1]))
        margin = 36
        img_h = 28
        img_w = 28
        y = page_h - img_h - 10
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
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'receta_{paciente.nombre_completo.replace(" ", "_")}.pdf',
        mimetype='application/pdf'
    )

@bp.route('/generar_consulta_pdf/<int:consulta_id>')
@login_required
@role_required('medico', 'admin')
def generar_consulta_pdf(consulta_id):
    if not REPORTLAB_AVAILABLE:
        flash('La librería ReportLab es necesaria para generar PDFs.', 'error')
        return redirect(url_for('main.consultas'))

    consulta = Consulta.query.get_or_404(consulta_id)
    paciente = consulta.paciente
    medico = consulta.medico
    clinica = consulta.clinica

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=36)
    styles = getSampleStyleSheet()

    title = ParagraphStyle('TitleX', parent=styles['Heading1'], spaceAfter=12)
    heading = ParagraphStyle('HeadingX', parent=styles['Heading2'], spaceAfter=6)
    small = ParagraphStyle('Small', parent=styles['Normal'], fontSize=10, spaceAfter=6)
    small_center = ParagraphStyle('SmallCenter', parent=small, alignment=TA_CENTER)

    story = []

    story.append(Paragraph('INFORME DE CONSULTA MÉDICA', title))
    story.append(Spacer(1, 6))

    # Encabezado con datos básicos
    info = [
        [Paragraph(f'<b>Paciente:</b> {paciente.nombre_completo}', small), Paragraph(f'<b>Fecha:</b> {consulta.fecha_consulta.strftime("%d/%m/%Y %H:%M") if consulta.fecha_consulta else "--"}', small)],
        [Paragraph(f'<b>Edad:</b> {paciente.edad or "--"} años', small), Paragraph(f'<b>Clínica:</b> {clinica.nombre if clinica else "--"}', small)],
        [Paragraph(f'<b>Médico:</b> {medico.nombre_completo if medico else "--"}', small), Paragraph(f'<b>Tipo consulta:</b> {consulta.tipo_consulta or "General"}', small)],
    ]
    t = Table(info, colWidths=[3.6*inch, 3.6*inch])
    t.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))

    # Secciones clínicas
    def add_section(titulo, texto):
        story.append(Paragraph(f'<u>{titulo}:</u>', heading))
        story.append(Paragraph(texto if texto else 'No registrado', small))
        story.append(Spacer(1, 6))

    add_section('Motivo de Consulta', consulta.motivo_consulta)
    add_section('Historia de la Enfermedad', consulta.historia_enfermedad)
    add_section('Revisión por Sistemas', consulta.revision_sistemas)

    # Antecedentes GO + generales
    go_lines = []
    def add_line(label, value):
        if value:
            go_lines.append(f'<b>{label}:</b> {value}')
    add_line('Gestas', consulta.gestas)
    add_line('Partos', consulta.partos)
    add_line('Abortos', consulta.abortos)
    add_line('Hijos vivos', consulta.hijos_vivos)
    add_line('Hijos muertos', consulta.hijos_muertos)
    if consulta.fecha_ultima_regla:
        add_line('Fecha última regla', consulta.fecha_ultima_regla.strftime('%d/%m/%Y'))

    story.append(Paragraph('<u>Antecedentes</u>:', heading))
    if go_lines:
        story.append(Paragraph(' | '.join(go_lines), small))
    if consulta.antecedentes:
        story.append(Paragraph(consulta.antecedentes, small))
    if not go_lines and not consulta.antecedentes:
        story.append(Paragraph('No registrados', small))
    story.append(Spacer(1, 6))

    # Examen físico (valores sueltos)
    story.append(Paragraph('<u>Examen Físico</u>:', heading))
    ef = []
    def ef_val(label, value, suffix=''):
        if value:
            ef.append([label, f'{value}{suffix}'])
    ef_val('Presión arterial', consulta.presion_arterial)
    ef_val('Frecuencia respiratoria', consulta.frecuencia_respiratoria, ' rpm')
    ef_val('Temperatura', consulta.temperatura, ' °C')
    ef_val('Peso', consulta.peso, ' kg')
    ef_val('Talla', consulta.talla, ' cm')
    ef_val('Frecuencia cardíaca', consulta.frecuencia_cardiaca, ' lpm')
    ef_val('Saturación O2', consulta.saturacion_oxigeno, ' %')
    ef_val('IMC', consulta.imc)

    if ef:
        ef_table = Table(ef, colWidths=[2.4*inch, 4.8*inch])
        ef_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.25, colors.lightgrey),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BACKGROUND', (0,0), (0,-1), colors.whitesmoke)
        ]))
        story.append(ef_table)
    else:
        story.append(Paragraph('No registrados', small))
    story.append(Spacer(1, 6))

    # Diagnóstico / Tratamiento / Indicaciones
    add_section('Diagnóstico', consulta.diagnostico)

    # Parsear tratamiento en medicamento y dosificación cuando aplique
    medicamento_texto = None
    dosificacion_texto = None
    if consulta.tratamiento:
        for raw_line in consulta.tratamiento.splitlines():
            line = raw_line.strip()
            lower = line.lower()
            if lower.startswith('medicamento:'):
                medicamento_texto = line.split(':', 1)[1].strip()
            elif lower.startswith('dosificación:') or lower.startswith('dosificacion:'):
                dosificacion_texto = line.split(':', 1)[1].strip()
            elif not medicamento_texto and line:
                medicamento_texto = line

    add_section('Medicamentos', medicamento_texto)
    add_section('Dosificación', dosificacion_texto)
    add_section('Indicaciones', consulta.indicaciones)

    # (Se dibuja la firma solo en la última página via canvasmaker)

    # Marca de agua
    def _watermark(canv, doc):
        candidates = [
            'logo_clinicas.jpg',
            'logo_clinicas.JPG',
            'logo_clinicas_familiares_cunori.jpg',
            'logotipo-cunori-transparente.png',
            'logo.png',
            'logo.JPG'
        ]
        logo_path = None
        for name in candidates:
            path_try = os.path.join(current_app.root_path, 'static', 'img', name)
            if os.path.exists(path_try):
                logo_path = path_try
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
        left_candidates = [
            'logo_clinicas.jpg',
            'logo_clinicas.JPG',
            'logo_clinicas_familiares_cunori.jpg',
            'logotipo-cunori-transparente.png',
            'logo.png',
            'logo.JPG'
        ]
        right_candidates = [
            'escudo_guatemala.png',
            'logotipo-cunori-transparente.png',
            'logo.JPG'
        ]
        left_path = None
        right_path = None
        for nm in left_candidates:
            p = os.path.join(current_app.root_path, 'static', 'img', nm)
            if os.path.exists(p):
                left_path = p
                break
        for nm in right_candidates:
            p = os.path.join(current_app.root_path, 'static', 'img', nm)
            if os.path.exists(p):
                right_path = p
                break
        try:
            page_w, page_h = doc.pagesize
        except Exception:
            page_w, page_h = getattr(canv, '_pagesize', (letter[0], letter[1]))
        margin = 36
        img_h = 28
        img_w = 28
        y = page_h - img_h - 10
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
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'consulta_{consulta.id}_{paciente.nombre_completo.replace(" ", "_")}.pdf',
        mimetype='application/pdf'
    )
