from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from bs4 import BeautifulSoup
import requests
from io import BytesIO
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# Coba register font untuk mendukung Unicode
try:
    # Windows font path
    font_path = "C:\\Windows\\Fonts\\arial.ttf"
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('Arial', font_path))
        HAS_UNICODE_FONT = True
    else:
        HAS_UNICODE_FONT = False
except Exception:
    HAS_UNICODE_FONT = False

def clean_html(raw_html):
    """Membersihkan tag HTML dan encode dengan benar"""
    if not raw_html:
        return ""
    try:
        # Convert ke string jika belum
        raw_html = str(raw_html)
        soup = BeautifulSoup(raw_html, "html.parser")
        text = soup.get_text()
        # Pastikan return string yang valid
        return text.strip() if text else ""
    except Exception as e:
        print(f"Error cleaning HTML: {e}")
        return str(raw_html).strip() if raw_html else ""

def generate_pdf_bytes(resep_data):
    """Generate PDF dari data resep menggunakan ReportLab"""
    try:
        # Buat BytesIO untuk menyimpan PDF
        pdf_buffer = BytesIO()
        
        # Buat PDF document
        doc = SimpleDocTemplate(pdf_buffer, pagesize=A4,
                               rightMargin=20, leftMargin=20,
                               topMargin=20, bottomMargin=20)
        
        # Story untuk menampung semua elemen
        story = []
        
        # Style
        styles = getSampleStyleSheet()
        
        # Title style
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#000000'),
            spaceAfter=12,
            alignment=1  # Center
        )
        
        # Heading style
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#333333'),
            spaceAfter=8,
            spaceBefore=8
        )
        
        # Body style
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=11,
            leading=14,
            spaceAfter=6
        )
        
        # 1. TITLE
        judul = clean_html(resep_data.get('title', 'Tanpa Judul'))
        if judul:
            story.append(Paragraph(str(judul), title_style))
        
        story.append(Spacer(1, 0.3*inch))
        
        # 2. GAMBAR
        image_url = resep_data.get('image')
        if image_url:
            try:
                response = requests.get(image_url, timeout=5)
                if response.status_code == 200:
                    img_data = BytesIO(response.content)
                    # Tentukan ukuran gambar
                    img = Image(img_data, width=4.5*inch, height=3*inch)
                    story.append(img)
                    story.append(Spacer(1, 0.2*inch))
            except Exception as e:
                print(f"Error loading image: {e}")
        
        # 3. STATISTIK
        waktu = resep_data.get('readyInMinutes', '-')
        porsi = resep_data.get('servings', '-')
        stats_text = f"<b>Waktu Masak:</b> {waktu} Menit  |  <b>Porsi:</b> {porsi} Orang"
        story.append(Paragraph(stats_text, body_style))
        story.append(Spacer(1, 0.2*inch))
        
        # 4. BAHAN-BAHAN
        story.append(Paragraph("Bahan-Bahan:", heading_style))
        ingredients = resep_data.get('extendedIngredients', [])
        if ingredients:
            for ing in ingredients:
                original_text = clean_html(ing.get('original', ''))
                if original_text:
                    story.append(Paragraph(f"• {str(original_text)}", body_style))
        else:
            story.append(Paragraph("Data bahan tidak tersedia.", body_style))
        
        story.append(Spacer(1, 0.2*inch))
        
        # 5. CARA MEMBUAT
        story.append(Paragraph("Cara Membuat:", heading_style))
        instructions = resep_data.get('instructions')
        if instructions:
            clean_instructions = clean_html(instructions)
            if clean_instructions:
                # Split instructions by line/paragraph untuk format lebih baik
                instruction_text = str(clean_instructions)
                # Limit length untuk menghindari overflow
                if len(instruction_text) > 5000:
                    instruction_text = instruction_text[:5000] + "..."
                story.append(Paragraph(instruction_text, body_style))
            else:
                story.append(Paragraph("Instruksi tidak tersedia untuk resep ini.", body_style))
        else:
            story.append(Paragraph("Instruksi tidak tersedia untuk resep ini.", body_style))
        
        # Build PDF
        doc.build(story)
        
        # Get bytes dan return
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()
        
    except Exception as e:
        print(f"Error generating PDF: {e}")
        raise