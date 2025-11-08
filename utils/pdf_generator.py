from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
import os

def generate_pdf_report(report_data):
    """
    Generate a PDF report from skin analysis data
    """
    report_id = report_data['id']
    pdf_filename = f"static/reports/report_{report_id}.pdf"
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(pdf_filename), exist_ok=True)
    
    # Create PDF document
    doc = SimpleDocTemplate(pdf_filename, pagesize=letter)
    story = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#34495E'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    normal_style = styles['Normal']
    
    # Title
    story.append(Paragraph("GlowMate Analysis Report", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Report date
    try:
        if isinstance(report_data['created_at'], str):
            report_date = datetime.strptime(report_data['created_at'], '%Y-%m-%d %H:%M:%S').strftime('%B %d, %Y')
        else:
            report_date = report_data['created_at'].strftime('%B %d, %Y')
    except:
        report_date = datetime.now().strftime('%B %d, %Y')
    
    story.append(Paragraph(f"<b>Report Date:</b> {report_date}", normal_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Skin Type
    story.append(Paragraph(f"<b>Skin Type:</b> {report_data['skin_type']}", heading_style))
    story.append(Spacer(1, 0.1*inch))
    
    # Health Score
    health_score = report_data['health_score']
    if health_score >= 70:
        score_color = colors.green
        color_hex = '#2ECC71'  # Green
    elif health_score >= 50:
        score_color = colors.orange
        color_hex = '#F39C12'  # Orange
    else:
        score_color = colors.red
        color_hex = '#E74C3C'  # Red
    
    story.append(Paragraph(f"<b>Skin Health Score:</b> <font color='{color_hex}'>{health_score:.1f}/100</font>", heading_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Analysis Results
    story.append(Paragraph("Analysis Results", heading_style))
    analysis = report_data['analysis_data']
    
    analysis_data = [
        ['Condition', 'Severity', 'Level'],
        ['Acne Spots', f"{analysis.get('acne_spots', {}).get('severity', 0):.2f}", analysis.get('acne_spots', {}).get('level', 'N/A')],
        ['Dark Circles', f"{analysis.get('dark_circles', {}).get('severity', 0):.2f}", analysis.get('dark_circles', {}).get('level', 'N/A')],
        ['Redness', f"{analysis.get('redness', {}).get('severity', 0):.2f}", analysis.get('redness', {}).get('level', 'N/A')],
        ['Oiliness', f"{analysis.get('oiliness', {}).get('score', 0):.2f}", analysis.get('oiliness', {}).get('level', 'N/A')],
        ['Dryness', f"{analysis.get('dryness', {}).get('score', 0):.2f}", analysis.get('dryness', {}).get('level', 'N/A')],
        ['Uneven Tone', f"{analysis.get('uneven_tone', {}).get('score', 0):.2f}", analysis.get('uneven_tone', {}).get('level', 'N/A')],
    ]
    
    analysis_table = Table(analysis_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
    analysis_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(analysis_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Recommendations
    story.append(Paragraph("Recommended Products", heading_style))
    recommendations = report_data['recommendations']
    for product in recommendations.get('products', []):
        story.append(Paragraph(f"• {product}", normal_style))
    
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Morning Routine", heading_style))
    for step in recommendations.get('morning_routine', []):
        story.append(Paragraph(f"• {step}", normal_style))
    
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Night Routine", heading_style))
    for step in recommendations.get('night_routine', []):
        story.append(Paragraph(f"• {step}", normal_style))
    
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Diet Tips", heading_style))
    for tip in recommendations.get('diet_tips', []):
        story.append(Paragraph(f"• {tip}", normal_style))
    
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("General Tips", heading_style))
    for tip in recommendations.get('general_tips', []):
        story.append(Paragraph(f"• {tip}", normal_style))
    
    # Build PDF
    doc.build(story)
    
    return pdf_filename

