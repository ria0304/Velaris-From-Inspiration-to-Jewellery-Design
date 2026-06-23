# backend/pdf_generator.py

import io
import base64
import re
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.colors import HexColor, white, black, grey
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics import renderPDF
from reportlab.pdfgen import canvas
import os

# Custom colors
VELARIS_GOLD = HexColor('#C9A96E')
VELARIS_DARK = HexColor('#1A1A1A')
VELARIS_LIGHT = HexColor('#F5F0EB')
VELARIS_TEXT = HexColor('#2C2C2C')
VELARIS_GREY = HexColor('#888888')


def generate_design_pdf(design_data: dict) -> tuple[str, str]:
    """
    Generate a comprehensive PDF with all design views and specifications.
    Returns: (base64_encoded_pdf, filename)
    """
    buffer = io.BytesIO()
    
    # Create PDF with custom page size
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=0.75*inch,
        rightMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    # === Custom Styles ===
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=VELARIS_DARK,
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=VELARIS_GREY,
        spaceAfter=12,
        alignment=TA_CENTER
    )
    
    section_style = ParagraphStyle(
        'SectionStyle',
        parent=styles['Heading2'],
        fontSize=18,
        textColor=VELARIS_DARK,
        spaceBefore=16,
        spaceAfter=8,
        fontName='Helvetica-Bold'
    )
    
    subsection_style = ParagraphStyle(
        'SubsectionStyle',
        parent=styles['Heading3'],
        fontSize=14,
        textColor=VELARIS_DARK,
        spaceBefore=10,
        spaceAfter=4,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=VELARIS_TEXT,
        spaceAfter=6,
        leading=14
    )
    
    label_style = ParagraphStyle(
        'LabelStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=VELARIS_GREY,
        spaceAfter=2
    )
    
    value_style = ParagraphStyle(
        'ValueStyle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=VELARIS_DARK,
        spaceAfter=6,
        fontName='Helvetica-Bold'
    )
    
    # === Get design name for filename ===
    design_name = design_data.get('name', 'Untitled-Design')
    filename = sanitize_filename(design_name)
    
    # === HEADER ===
    story.append(Paragraph("VELARIS", title_style))
    story.append(Paragraph("From Inspiration to Jewellery Design", subtitle_style))
    story.append(Spacer(1, 0.1*inch))
    
    # Divider
    story.append(Paragraph("—" * 40, styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # === DESIGN NAME & DATE ===
    story.append(Paragraph(design_name, 
                          ParagraphStyle('DesignName', parent=section_style, fontSize=22)))
    
    timestamp = design_data.get('timestamp', datetime.now().strftime("%B %d, %Y"))
    story.append(Paragraph(f"Generated: {timestamp}", subtitle_style))
    story.append(Spacer(1, 0.2*inch))
    
    # === THREE VIEWS SECTION ===
    story.append(Paragraph("DESIGN VIEWS", section_style))
    story.append(Spacer(1, 0.1*inch))
    
    # Get views from multiView
    multi_view = design_data.get('multiView', {})
    
    views_config = [
        ('Front View', multi_view.get('front', 'Front view description not available')),
        ('Artistic View', multi_view.get('perspective', 'Artistic view description not available')),
        ('Profile View', multi_view.get('side', 'Profile view description not available'))
    ]
    
    for view_title, view_description in views_config:
        # View title
        story.append(Paragraph(view_title, subsection_style))
        
        # Create a visual placeholder - in production, you'd render actual images
        # For now, we create a styled box with the view name
        view_box = create_view_placeholder(view_title, view_description)
        story.append(view_box)
        
        # View description
        story.append(Paragraph(view_description, body_style))
        story.append(Spacer(1, 0.15*inch))
    
    story.append(PageBreak())
    
    # === TECHNICAL SPECIFICATIONS ===
    story.append(Paragraph("TECHNICAL SPECIFICATIONS", section_style))
    story.append(Spacer(1, 0.1*inch))
    
    spec = design_data.get('spec', {})
    
    spec_data = [
        ['Property', 'Specification'],
        ['Design Type', spec.get('type', 'N/A')],
        ['Metal', spec.get('metal', 'N/A')],
        ['Gemstone', spec.get('stone', 'N/A')],
        ['Gemstone Cut', spec.get('shape', 'N/A')],
        ['Setting', spec.get('setting', 'N/A')],
        ['Occasion', spec.get('occasion', 'N/A')],
        ['Stone Size', spec.get('stoneSize', 'N/A')],
        ['Band Width', spec.get('bandWidth', 'N/A')],
        ['Details', spec.get('details', 'N/A')]
    ]
    
    spec_table = Table(spec_data, colWidths=[2.2*inch, 3.3*inch])
    spec_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), VELARIS_DARK),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), VELARIS_LIGHT),
        ('GRID', (0, 0), (-1, -1), 0.5, VELARIS_GREY),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(spec_table)
    story.append(Spacer(1, 0.2*inch))
    
    story.append(PageBreak())
    
    # === COST BREAKDOWN ===
    story.append(Paragraph("COST ESTIMATION", section_style))
    story.append(Spacer(1, 0.1*inch))
    
    cost = design_data.get('cost', {})
    metal_cost = cost.get('metalCost', 0)
    stone_cost = cost.get('stoneCost', 0)
    labor_cost = cost.get('laborCost', 0)
    total_cost = cost.get('totalCost', 0)
    markup = cost.get('markupPercent', 25)
    
    cost_data = [
        ['Cost Component', 'Amount (USD)'],
        ['Metal Cost', f"${metal_cost:,}"],
        ['Stone Cost', f"${stone_cost:,}"],
        ['Labor Cost', f"${labor_cost:,}"],
        [f'Markup ({markup}%)', f"${int(total_cost * markup / (100 + markup)):,}"],
        ['TOTAL RETAIL', f"${total_cost:,}"]
    ]
    
    cost_table = Table(cost_data, colWidths=[2.5*inch, 2*inch])
    cost_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), VELARIS_GOLD),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -2), VELARIS_LIGHT),
        ('BACKGROUND', (0, -1), (-1, -1), HexColor('#E8DCD4')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 0.5, VELARIS_GREY),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(cost_table)
    story.append(Spacer(1, 0.2*inch))
    
    story.append(PageBreak())
    
    # === MANUFACTURING DETAILS ===
    story.append(Paragraph("MANUFACTURING DETAILS", section_style))
    story.append(Spacer(1, 0.1*inch))
    
    mfg = design_data.get('manufacturing', {})
    score = mfg.get('score', 0)
    level = mfg.get('level', 'N/A')
    
    story.append(Paragraph(f"<b>Complexity Score:</b> {score}/100", body_style))
    story.append(Paragraph(f"<b>Manufacturing Level:</b> {level}", body_style))
    story.append(Spacer(1, 0.1*inch))
    
    # Complexity bar (visual)
    story.append(create_complexity_bar(score))
    story.append(Spacer(1, 0.15*inch))
    
    # Manufacturing notes
    story.append(Paragraph("<b>Casting Notes:</b>", subsection_style))
    story.append(Paragraph(mfg.get('castingNotes', 'N/A'), body_style))
    story.append(Spacer(1, 0.05*inch))
    
    story.append(Paragraph("<b>Setting Notes:</b>", subsection_style))
    story.append(Paragraph(mfg.get('settingNotes', 'N/A'), body_style))
    story.append(Spacer(1, 0.05*inch))
    
    story.append(Paragraph("<b>Polishing Notes:</b>", subsection_style))
    story.append(Paragraph(mfg.get('polishingNotes', 'N/A'), body_style))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(PageBreak())
    
    # === DESIGN NARRATIVE ===
    story.append(Paragraph("DESIGN NARRATIVE", section_style))
    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph(design_data.get('notes', 'No additional notes provided.'), body_style))
    story.append(Spacer(1, 0.2*inch))
    
    # === MODEL INFO (if available) ===
    if 'modelUsed' in design_data:
        story.append(Paragraph(f"<i>AI Model: {design_data['modelUsed']}</i>", 
                              ParagraphStyle('ModelInfo', parent=styles['Normal'], 
                                            fontSize=8, textColor=VELARIS_GREY)))
    
    # === FOOTER ===
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("—" * 30, styles['Normal']))
    story.append(Paragraph(
        f"Velaris AI · Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
        ParagraphStyle('Footer', parent=styles['Normal'], 
                      fontSize=8, textColor=VELARIS_GREY, alignment=TA_CENTER)
    ))
    
    # Build PDF
    doc.build(story)
    pdf_data = buffer.getvalue()
    buffer.close()
    
    return base64.b64encode(pdf_data).decode('utf-8'), filename


def create_view_placeholder(title: str, description: str) -> Drawing:
    """Create a styled rectangle with view title for visual representation."""
    drawing = Drawing(400, 180)
    
    # Background rectangle
    rect = Rect(0, 0, 400, 180, 
                fillColor=VELARIS_LIGHT, 
                strokeColor=VELARIS_GOLD,
                strokeWidth=1)
    drawing.add(rect)
    
    # View title in center
    title_text = String(200, 90, title, 
                        fontSize=18, 
                        fillColor=VELARIS_DARK,
                        textAnchor='middle')
    drawing.add(title_text)
    
    # Subtitle
    sub_text = String(200, 60, "AI Generated Visualization", 
                      fontSize=10, 
                      fillColor=VELARIS_GREY,
                      textAnchor='middle')
    drawing.add(sub_text)
    
    # Small decorative line
    line = Rect(150, 45, 100, 1, fillColor=VELARIS_GOLD, strokeColor=VELARIS_GOLD)
    drawing.add(line)
    
    return drawing


def create_complexity_bar(score: int) -> Drawing:
    """Create a visual complexity bar."""
    drawing = Drawing(400, 40)
    
    # Background bar
    rect = Rect(0, 10, 400, 20, fillColor=VELARIS_LIGHT, strokeColor=VELARIS_GREY)
    drawing.add(rect)
    
    # Fill bar based on score
    fill_width = (score / 100) * 400
    if score < 40:
        fill_color = HexColor('#4CAF50')  # Green
    elif score < 75:
        fill_color = HexColor('#FFA726')  # Orange
    else:
        fill_color = HexColor('#EF5350')  # Red
    
    fill_rect = Rect(0, 10, fill_width, 20, fillColor=fill_color)
    drawing.add(fill_rect)
    
    # Score label
    label = String(fill_width + 10, 22, f"{score}%", 
                   fontSize=10, fillColor=VELARIS_DARK)
    drawing.add(label)
    
    return drawing


def sanitize_filename(name: str) -> str:
    """
    Sanitize a design name to create a safe filename.
    Example: "Aurum Bloom" -> "Aurum_Bloom.pdf"
    """
    # Remove any characters that aren't alphanumeric, spaces, or hyphens
    clean = re.sub(r'[^a-zA-Z0-9\s\-]', '', name)
    # Replace spaces with underscores
    clean = clean.replace(' ', '_')
    # Remove multiple underscores
    clean = re.sub(r'_+', '_', clean)
    # Trim leading/trailing underscores and whitespace
    clean = clean.strip('_')
    # If empty, use default
    if not clean:
        clean = 'Velaris_Design'
    # Add .pdf extension
    return f"{clean}.pdf"
