"""
Generador de PDFs para reportes
Usa ReportLab para crear PDFs profesionales
"""

from datetime import datetime
from io import BytesIO
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.pdfgen import canvas

from .utils import (
    get_progress_data, get_exercise_data, get_type_data,
    get_muscle_data, get_consistency_data, get_performance_data
)


def generate_pdf_progress(user, period='month', exercise_type=None):
    """
    Genera PDF del informe de Progreso Personal
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []

    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=12,
        alignment=1
    )

    # Encabezado
    elements.append(Paragraph("📈 Mi Progreso Personal", title_style))
    elements.append(Paragraph(f"Usuario: {user.get_full_name() or user.username}", styles['Normal']))
    elements.append(Paragraph(f"Período: {period.upper()} | Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 0.2*inch))

    # Obtener datos
    data = get_progress_data(user, period, exercise_type)

    # Tabla de estadísticas
    stats_table_data = [
        ['Sesiones', 'Volumen Total', 'Calorías', 'Duración Promedio'],
        [
            str(data['sessions_count']),
            f"{int(data['total_volume'])} kg",
            f"{data['total_calories']} kcal",
            f"{data['avg_duration']} min"
        ]
    ]

    stats_table = Table(stats_table_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#f3f4f6')),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))

    elements.append(stats_table)
    elements.append(Spacer(1, 0.3*inch))

    # Progreso
    progress_text = f"Progreso vs período anterior: {data['progress']:+.1f}%"
    elements.append(Paragraph(progress_text, styles['Normal']))
    elements.append(Spacer(1, 0.2*inch))

    # Tabla de sesiones
    sessions_table_data = [['Fecha', 'Plan', 'Volumen', 'Duración']]
    for session in data['sessions']:
        volume = data['volumes_by_date'].get(session.date.strftime('%Y-%m-%d'), 0)
        from .utils import calculate_session_duration
        duration = calculate_session_duration(session)

        sessions_table_data.append([
            session.date.strftime('%d/%m/%Y'),
            session.plan.name if session.plan else 'Libre',
            f"{int(volume)} kg",
            f"{duration} min"
        ])

    sessions_table = Table(sessions_table_data, colWidths=[1.3*inch, 1.7*inch, 1.5*inch, 1.5*inch])
    sessions_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6b7280')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')])
    ]))

    elements.append(Paragraph("Historial de Sesiones", styles['Heading2']))
    elements.append(Spacer(1, 0.1*inch))
    elements.append(sessions_table)
    elements.append(Spacer(1, 0.3*inch))

    # Pie de página
    elements.append(Paragraph("GymTracking © 2026 | Reporte de Entrenamiento", styles['Normal']))

    # Construir PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_pdf_exercise(user, exercise_id):
    """
    Genera PDF del informe Por Ejercicio
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=12,
    )

    data = get_exercise_data(user, exercise_id)

    if not data:
        elements.append(Paragraph("Ejercicio no encontrado", styles['Normal']))
        doc.build(elements)
        buffer.seek(0)
        return buffer

    exercise = data['exercise']

    # Encabezado
    elements.append(Paragraph(f"💪 {exercise.name}", title_style))
    elements.append(Paragraph(f"Tipo: {exercise.get_exercise_type_display()}", styles['Normal']))
    elements.append(Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 0.2*inch))

    # Estadísticas
    stats_text = f"""
    <b>Máximo Peso:</b> {data['max_weight']} kg<br/>
    <b>Máximo Reps:</b> {data['max_reps']}<br/>
    <b>Promedio (últimas 3):</b> {data['avg_weight']} kg<br/>
    <b>Tendencia:</b> {data['trend']}<br/>
    <b>Frecuencia:</b> {data['frequency']} veces este mes
    """
    elements.append(Paragraph(stats_text, styles['Normal']))
    elements.append(Spacer(1, 0.2*inch))

    # Tabla de series
    if data['sets_data']:
        sets_table_data = [['Fecha', 'Set', 'Reps', 'Peso']]
        for s in data['sets_data'][:20]:
            sets_table_data.append([
                s['date'].strftime('%d/%m/%Y'),
                str(s['set_number']),
                str(s['reps']) if s['reps'] else '-',
                f"{s['weight']} kg" if s['weight'] else '-'
            ])

        sets_table = Table(sets_table_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1.5*inch])
        sets_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0fdf4')])
        ]))

        elements.append(Paragraph("Últimas Series", styles['Heading2']))
        elements.append(Spacer(1, 0.1*inch))
        elements.append(sets_table)

    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph("GymTracking © 2026", styles['Normal']))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_pdf_type(user, period='month'):
    """
    Genera PDF del informe Por Tipo de Ejercicio
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=12,
        alignment=1
    )

    # Encabezado
    elements.append(Paragraph("⚡ Entrenamientos por Tipo", title_style))
    elements.append(Paragraph(f"Período: {period.upper()} | {datetime.now().strftime('%d/%m/%Y')}", styles['Normal']))
    elements.append(Spacer(1, 0.2*inch))

    data = get_type_data(user, period)

    # Tabla de tipos
    type_table_data = [['Tipo', 'Sesiones', 'Volumen', 'Calorías', '%']]
    for ex_type, type_info in data.items():
        type_table_data.append([
            type_info['type_display'],
            str(type_info['sessions_count']),
            f"{int(type_info['total_volume'])} kg",
            str(type_info['total_calories']),
            f"{type_info['percentage']:.1f}%"
        ])

    type_table = Table(type_table_data, colWidths=[1.3*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1*inch])
    type_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f59e0b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fffbeb')])
    ]))

    elements.append(type_table)
    elements.append(Spacer(1, 0.3*inch))

    # Top ejercicios por tipo
    for ex_type, type_info in data.items():
        if type_info['top_exercises']:
            elements.append(Paragraph(f"Top Ejercicios - {type_info['type_display']}", styles['Heading2']))
            top_table_data = [['Ejercicio', 'Volumen']]
            for ex_name, volume in type_info['top_exercises']:
                top_table_data.append([ex_name, f"{int(volume)} kg"])

            top_table = Table(top_table_data, colWidths=[4*inch, 2*inch])
            top_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5e7eb')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ]))
            elements.append(top_table)
            elements.append(Spacer(1, 0.2*inch))

    elements.append(Paragraph("GymTracking © 2026", styles['Normal']))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_pdf_muscle(user, period='month', muscle_group=None):
    """
    Genera PDF del informe Por Grupo Muscular
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=12,
        alignment=1
    )

    elements.append(Paragraph("🦵 Entrenamientos por Grupo Muscular", title_style))
    elements.append(Paragraph(f"Período: {period.upper()} | {datetime.now().strftime('%d/%m/%Y')}", styles['Normal']))
    elements.append(Spacer(1, 0.2*inch))

    data = get_muscle_data(user, period, muscle_group)

    # Tabla de músculos
    muscle_table_data = [['Grupo Muscular', 'Sesiones', 'Volumen', 'Frecuencia']]
    for muscle_name, muscle_info in data.items():
        muscle_table_data.append([
            muscle_info['name'],
            str(muscle_info['sessions_count']),
            f"{int(muscle_info['total_volume'])} kg",
            f"{muscle_info['frequency']:.1f}x/sem"
        ])

    muscle_table = Table(muscle_table_data, colWidths=[2*inch, 1.2*inch, 1.3*inch, 1.5*inch])
    muscle_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8b5cf6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#faf5ff')])
    ]))

    elements.append(muscle_table)
    elements.append(Spacer(1, 0.3*inch))

    elements.append(Paragraph("GymTracking © 2026", styles['Normal']))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_pdf_consistency(user, weeks=4):
    """
    Genera PDF del informe de Consistencia
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=12,
        alignment=1
    )

    elements.append(Paragraph("📅 Mi Consistencia", title_style))
    elements.append(Paragraph(f"Período: Últimas {weeks} semanas | {datetime.now().strftime('%d/%m/%Y')}", styles['Normal']))
    elements.append(Spacer(1, 0.2*inch))

    data = get_consistency_data(user, weeks)

    # Racha actual
    streak_text = f"<b>🔥 Racha Actual:</b> {data['current_streak']} días<br/><b>Promedio:</b> {data['avg_sessions_per_week']} sesiones/semana<br/><b>Total Sesiones:</b> {data['total_sessions']}"
    elements.append(Paragraph(streak_text, styles['Normal']))
    elements.append(Spacer(1, 0.2*inch))

    # Tabla de semanas
    weeks_table_data = [['Semana', 'Sesiones']]
    for week_key, sessions in sorted(data['weeks_data'].items()):
        weeks_table_data.append([week_key, str(sessions)])

    weeks_table = Table(weeks_table_data, colWidths=[3*inch, 2*inch])
    weeks_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#06b6d4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ecfdf5')])
    ]))

    elements.append(Paragraph("Sesiones por Semana", styles['Heading2']))
    elements.append(Spacer(1, 0.1*inch))
    elements.append(weeks_table)
    elements.append(Spacer(1, 0.3*inch))

    elements.append(Paragraph("GymTracking © 2026", styles['Normal']))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_pdf_performance(user, period='month'):
    """
    Genera PDF del informe de Rendimiento
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=12,
        alignment=1
    )

    elements.append(Paragraph("🔥 Mi Rendimiento", title_style))
    elements.append(Paragraph(f"Período: {period.upper()} | {datetime.now().strftime('%d/%m/%Y')}", styles['Normal']))
    elements.append(Spacer(1, 0.2*inch))

    data = get_performance_data(user, period)

    # Score principal
    score_text = f"<b>Score de Rendimiento:</b> {int(data['overall_score'])}/100"
    elements.append(Paragraph(score_text, styles['Heading2']))
    elements.append(Spacer(1, 0.2*inch))

    # Desglose de scores
    scores_text = f"""
    <b>Consistencia:</b> {int(data['consistency_score'])}/100<br/>
    <b>Volumen:</b> {int(data['volume_score'])}/100<br/>
    <b>Calorías:</b> {int(data['calories_score'])}/100<br/>
    <b>Progreso:</b> {int(data['progress_score'])}/100
    """
    elements.append(Paragraph(scores_text, styles['Normal']))
    elements.append(Spacer(1, 0.2*inch))

    # Números clave
    stats_text = f"""
    <b>Sesiones:</b> {data['sessions_count']}<br/>
    <b>Volumen Total:</b> {int(data['total_volume'])} kg<br/>
    <b>Calorías:</b> {data['total_calories']} kcal<br/>
    <b>Duración Promedio:</b> {data['avg_duration']} min<br/>
    <b>Progreso vs período anterior:</b> {data['progress']:+.1f}%
    """
    elements.append(Paragraph(stats_text, styles['Normal']))
    elements.append(Spacer(1, 0.2*inch))

    # Top ejercicios
    if data['top_exercises']:
        top_table_data = [['Ejercicio', 'Volumen']]
        for ex_name, volume in data['top_exercises']:
            top_table_data.append([ex_name, f"{int(volume)} kg"])

        top_table = Table(top_table_data, colWidths=[4*inch, 2*inch])
        top_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc2626')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))

        elements.append(Paragraph("Top 3 Ejercicios", styles['Heading2']))
        elements.append(Spacer(1, 0.1*inch))
        elements.append(top_table)

    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph("GymTracking © 2026", styles['Normal']))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def export_report_to_pdf(user, report_type, **kwargs):
    """
    Función wrapper que retorna el buffer PDF según el tipo de reporte
    """
    generators = {
        'progress': lambda: generate_pdf_progress(user, kwargs.get('period', 'month'), kwargs.get('exercise_type')),
        'exercise': lambda: generate_pdf_exercise(user, kwargs.get('exercise_id')),
        'type': lambda: generate_pdf_type(user, kwargs.get('period', 'month')),
        'muscle': lambda: generate_pdf_muscle(user, kwargs.get('period', 'month'), kwargs.get('muscle_group')),
        'consistency': lambda: generate_pdf_consistency(user, kwargs.get('weeks', 4)),
        'performance': lambda: generate_pdf_performance(user, kwargs.get('period', 'month')),
    }

    generator_func = generators.get(report_type)
    if generator_func:
        return generator_func()

    return None
