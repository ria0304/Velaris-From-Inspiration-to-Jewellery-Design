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


_PREVIEW_CACHE: dict[str, list] = {}
_PREVIEW_CACHE_MAX = 32


def _preview_key(design_data: dict) -> str:
    import hashlib
    import json as _json
    spec = design_data.get("spec", {})
    return hashlib.sha256(_json.dumps(
        [design_data.get("id"), spec, design_data.get("motif")],
        sort_keys=True, default=str).encode()).hexdigest()


def _realistic_previews(design_data: dict) -> list[tuple[str, object, str]]:
    """Studio-lit previews for front/artistic/profile/back. Beauty diffusion
    when available (cached), procedural PIL fallback. Returns (title, buf, source).
    Results are memoized per design so repeat exports don't re-render 8 images."""
    key = _preview_key(design_data)
    if key in _PREVIEW_CACHE:
        out = []
        for title, raw, source in _PREVIEW_CACHE[key]:
            out.append((title, io.BytesIO(raw), source))
        return out
    spec = design_data.get('spec', {})
    try:
        from .beauty import beauty_png
        from .cad import parse_carat
        carat = parse_carat(spec.get('stoneSize', '1.0 carat'))
        out = []
        for title, view in (("Front", "front"), ("Artistic", "perspective"),
                            ("Profile", "side"), ("Back", "back")):
            raw, source = beauty_png(
                spec.get('type', 'Ring'), spec.get('metal', '18K Yellow Gold'),
                spec.get('stone', 'Diamond'), spec.get('shape', 'Round'),
                carat, spec.get('setting', 'Prong'), view, design_data.get('motif'))
            buf = io.BytesIO(raw)
            out.append((title, buf, source))
        # memoize raw bytes (not the consumed buffers) for repeat exports
        if len(_PREVIEW_CACHE) >= _PREVIEW_CACHE_MAX:
            _PREVIEW_CACHE.pop(next(iter(_PREVIEW_CACHE)))
        _PREVIEW_CACHE[key] = [(t, b.getvalue(), s) for t, b, s in out]
        return out
    except Exception:
        return []


def _cad_svg_for_view(design_data: dict, view: str) -> tuple[str | None, dict]:
    """Render deterministic parametric CAD SVG for a view. Returns (svg, params)."""
    spec = design_data.get('spec', {})
    try:
        from .cad import render_cad_svg
        svg, p = render_cad_svg(
            spec.get('type', 'Ring'), spec.get('metal', '18K Yellow Gold'),
            spec.get('stone', 'Diamond'), spec.get('shape', 'Round'),
            spec.get('stoneSize', '1.0 carat'), spec.get('setting', 'Prong'),
            spec.get('bandWidth'), view,
            re.sub(r'[^a-zA-Z0-9]', '', design_data.get('id', design_data.get('name', 'cad')))[:12] or 'cad',
            design_data.get('motif'),
        )
        return svg, {"carat": p.carat, "stone_r_mm": round(p.stone_r, 3),
                     "band_w_mm": p.band_w, "band_r_mm": p.band_r, **p.dims()}
    except Exception:
        return None, {}


def _svg_to_drawing(svg: str, width: float = 220, height: float = 220):
    """Convert SVG string to a ReportLab Drawing (true vector, not placeholder)."""
    from svglib.svglib import svg2rlg
    drawing = svg2rlg(io.BytesIO(svg.encode('utf-8')))
    if drawing is None:
        raise ValueError("svg2rlg returned None")
    sx = width / drawing.width if drawing.width else 1
    sy = height / drawing.height if drawing.height else 1
    drawing.scale(sx, sy)
    drawing.width, drawing.height = width, height
    return drawing


def _attach_dxf(pdf_bytes: bytes, dxf_text: str, filename: str) -> bytes:
    """Embed the DXF as a PDF file attachment (jeweller handoff)."""
    from pypdf import PdfReader, PdfWriter
    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.add_attachment(filename, dxf_text.encode('utf-8'))
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


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
        ('Front View', 'front', multi_view.get('front', 'Front view description not available')),
        ('Artistic View', 'perspective', multi_view.get('perspective', 'Artistic view description not available')),
        ('Profile View', 'side', multi_view.get('side', 'Profile view description not available')),
        ('Back View', 'back', multi_view.get('back', 'Back view: mirrored silhouette with pin stem, hinge and safety catch.')),
    ]

    cad_params: dict = {}
    for view_title, view_key, view_description in views_config:
        # View title
        story.append(Paragraph(view_title, subsection_style))

        # True parametric CAD vector — replaces the old styled placeholder box
        svg, params = _cad_svg_for_view(design_data, view_key)
        if params:
            cad_params = params
        try:
            if svg is None:
                raise ValueError("CAD render failed")
            story.append(_svg_to_drawing(svg))
        except Exception:
            view_box = create_view_placeholder(view_title, view_description)
            story.append(view_box)

        # View description
        story.append(Paragraph(view_description, body_style))
        story.append(Spacer(1, 0.15*inch))

    story.append(PageBreak())

    # === REALISTIC PREVIEWS (studio-lit raster, all 4 views) ===
    story.append(Paragraph("REALISTIC PREVIEWS", section_style))
    story.append(Paragraph(
        "Photorealistic-style studio renders — metal shading, faceted gemstones, "
        "soft shadows. For presentation; see CAD DATA for manufacturing geometry.",
        body_style))
    story.append(Spacer(1, 0.1*inch))
    for title, buf, source in _realistic_previews(design_data):
        label = "AI diffusion render — illustrative" if source.startswith("diffusion") else "Procedural preview"
        story.append(Paragraph(f"{title} View — Realistic <font size=8 color=#888888>({label})</font>", subsection_style))
        try:
            story.append(Image(buf, width=3.2*inch, height=3.2*inch))
        except Exception:
            story.append(Paragraph("Preview unavailable.", body_style))
        story.append(Spacer(1, 0.12*inch))

    story.append(PageBreak())
    
    # === TECHNICAL SPECIFICATIONS ===
    story.append(Paragraph("TECHNICAL SPECIFICATIONS", section_style))
    story.append(Spacer(1, 0.1*inch))
    
    spec = design_data.get('spec', {})

    # Full product dimensions from the same parametric model as the views
    dims: dict = {}
    try:
        from .cad import CadParams, parse_carat, parse_mm
        _g = CadParams(spec.get('type', 'Ring'), spec.get('metal', '18K Yellow Gold'),
                       spec.get('stone', 'Diamond'), spec.get('shape', 'Round'),
                       spec.get('stoneSize', '1.0 carat'), spec.get('bandWidth'),
                       spec.get('setting', 'Prong'))
        dims = _g.dims()
    except Exception:
        dims = {}

    def _d(k: str, suffix: str = "") -> str:
        v = dims.get(k)
        return f"{v}{suffix}" if v is not None else "N/A"

    spec_data = [
        ['Property', 'Specification'],
        ['Design Type', spec.get('type', 'N/A')],
        ['Metal', spec.get('metal', 'N/A')],
        ['Gemstone', spec.get('stone', 'N/A')],
        ['Gemstone Cut', spec.get('shape', 'N/A')],
        ['Gemstone Weight', f"{dims.get('carat', spec.get('stoneSize', 'N/A'))} ct"],
        ['Stone Dimensions', f"{_d('stone_w_mm', ' mm')} × {_d('stone_h_mm', ' mm')} (W × H)"],
        ['Overall Width', _d('width_mm', ' mm')],
        ['Overall Height', _d('height_mm', ' mm')],
        ['Depth / Thickness', _d('depth_mm', ' mm')],
        ['Band / Frame Width', _d('band_w_mm', ' mm')],
        ['Est. Metal Weight', _d('est_metal_wt_g', ' g')],
        ['Est. Total Weight', _d('est_total_wt_g', ' g')],
        ['Setting', spec.get('setting', 'N/A')],
        ['Occasion', spec.get('occasion', 'N/A')],
        ['Stone Size (spec)', spec.get('stoneSize', 'N/A')],
        ['Band Width (spec)', spec.get('bandWidth', 'N/A')],
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
    
    # === CAD DATA (true mm dimensions, shared across all 3 views) ===
    story.append(Paragraph("CAD DATA — MANUFACTURING HANDOFF", section_style))
    story.append(Spacer(1, 0.1*inch))
    if cad_params:
        story.append(Paragraph(
            f"<b>Overall:</b> {cad_params.get('width_mm')} mm (W) × "
            f"{cad_params.get('height_mm')} mm (H) × {cad_params.get('depth_mm')} mm (D)"
            f" &nbsp;·&nbsp; <b>Stone:</b> {cad_params.get('stone_w_mm')} × "
            f"{cad_params.get('stone_h_mm')} mm, {cad_params.get('carat')} ct"
            f" &nbsp;·&nbsp; <b>Weight:</b> ~{cad_params.get('est_total_wt_g')} g total "
            f"({cad_params.get('est_metal_wt_g')} g metal)", body_style))
        story.append(Paragraph(
            "A DXF file with these true-scale entities (BAND circle, STONE circle, label) "
            "is attached to this PDF — open the attachments panel in your PDF reader "
            "to send it to Rhino/Matrix/CNC.", body_style))
    else:
        story.append(Paragraph("Parametric CAD data unavailable for this design.", body_style))
    story.append(Spacer(1, 0.15*inch))

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

    # Attach DXF handoff file (non-fatal if it fails)
    try:
        from .cad import render_cad_svg, to_dxf_entities
        spec = design_data.get('spec', {})
        _, p = render_cad_svg(
            spec.get('type', 'Ring'), spec.get('metal', '18K Yellow Gold'),
            spec.get('stone', 'Diamond'), spec.get('shape', 'Round'),
            spec.get('stoneSize', '1.0 carat'), spec.get('setting', 'Prong'),
            spec.get('bandWidth'), 'front', 'cad')
        dxf_name = sanitize_filename(design_data.get('name', 'Velaris_Design')).replace('.pdf', '.dxf')
        pdf_data = _attach_dxf(pdf_data, to_dxf_entities(p), dxf_name)
    except Exception:
        pass

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
