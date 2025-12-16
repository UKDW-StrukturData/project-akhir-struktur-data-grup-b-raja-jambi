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
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-GUI backend

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

def extract_nutrition_data(resep_data):
    """Extract nutrisi utama dari data resep"""
    try:
        nutrition_data = resep_data.get('nutrition', {})
        nutrients = nutrition_data.get('nutrients', [])
        
        protein = 0
        fat = 0
        carbs = 0
        calories = 0
        fiber = 0
        
        for nutrient in nutrients:
            name = nutrient.get('name', '').lower()
            value = nutrient.get('amount', 0)
            
            if 'protein' in name:
                protein = round(value, 1)
            elif 'fat' in name and 'saturated' not in name:
                fat = round(value, 1)
            elif 'carbohydrates' in name:
                carbs = round(value, 1)
            elif 'calories' in name or 'energy' in name:
                calories = round(value, 1)
            elif 'fiber' in name:
                fiber = round(value, 1)
        
        return {
            'protein': protein,
            'fat': fat,
            'carbs': carbs,
            'calories': calories,
            'fiber': fiber
        }
    except Exception:
        return {'protein': 0, 'fat': 0, 'carbs': 0, 'calories': 0, 'fiber': 0}

def create_nutrition_chart_image(resep_data):
    """Membuat 2 pie chart nutrisi sebagai gambar untuk PDF"""
    try:
        nutrition = extract_nutrition_data(resep_data)
        
        # Jika tidak ada data nutrisi
        if nutrition['protein'] == 0 and nutrition['fat'] == 0 and nutrition['carbs'] == 0:
            return None, None
        
        # CHART 1: Komposisi Nutrisi (gram)
        fig1, ax1 = plt.subplots(figsize=(5, 4), dpi=100)
        
        labels1 = ['Protein', 'Lemak', 'Karbohidrat']
        sizes1 = [nutrition['protein'], nutrition['fat'], nutrition['carbs']]
        colors_pie = ['#FF6B6B', '#FFA500', '#4ECDC4']
        
        # Filter out zero values
        labels1_filtered = [l for l, s in zip(labels1, sizes1) if s > 0]
        sizes1_filtered = [s for s in sizes1 if s > 0]
        colors1_filtered = [c for l, c in zip(labels1, colors_pie) if l in labels1_filtered]
        
        if sizes1_filtered:
            ax1.pie(sizes1_filtered, labels=labels1_filtered, autopct='%1.1f%%', 
                   colors=colors1_filtered, startangle=90)
            ax1.set_title('Komposisi Nutrisi Utama (g)', fontsize=11, fontweight='bold')
            
            # Save chart 1 to BytesIO
            img_buffer1 = BytesIO()
            plt.savefig(img_buffer1, format='png', bbox_inches='tight', dpi=100)
            img_buffer1.seek(0)
            plt.close(fig1)
        else:
            img_buffer1 = None
            plt.close(fig1)
        
        # CHART 2: Distribusi Kalori
        # Protein: 4 kcal/g, Fat: 9 kcal/g, Carbs: 4 kcal/g
        calories_protein = nutrition['protein'] * 4
        calories_fat = nutrition['fat'] * 9
        calories_carbs = nutrition['carbs'] * 4
        
        fig2, ax2 = plt.subplots(figsize=(5, 4), dpi=100)
        
        labels2 = ['Protein', 'Lemak', 'Karbohidrat']
        sizes2 = [calories_protein, calories_fat, calories_carbs]
        
        # Filter out zero values
        labels2_filtered = [l for l, s in zip(labels2, sizes2) if s > 0]
        sizes2_filtered = [s for s in sizes2 if s > 0]
        colors2_filtered = [c for l, c in zip(labels2, colors_pie) if l in labels2_filtered]
        
        if sizes2_filtered:
            ax2.pie(sizes2_filtered, labels=labels2_filtered, autopct='%1.1f%%', 
                   colors=colors2_filtered, startangle=90)
            ax2.set_title('Distribusi Kalori dari Nutrisi', fontsize=11, fontweight='bold')
            
            # Save chart 2 to BytesIO
            img_buffer2 = BytesIO()
            plt.savefig(img_buffer2, format='png', bbox_inches='tight', dpi=100)
            img_buffer2.seek(0)
            plt.close(fig2)
        else:
            img_buffer2 = None
            plt.close(fig2)
        
        return img_buffer1, img_buffer2
    except Exception as e:
        print(f"Error creating nutrition chart: {e}")
        return None, None
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
        
        # 4. VISUALISASI NUTRISI (PIE CHART)
        chart_img1, chart_img2 = create_nutrition_chart_image(resep_data)
        if chart_img1 and chart_img2:
            story.append(Paragraph("Analisis Nutrisi:", heading_style))
            
            # Tampilkan kedua chart side by side
            img1 = Image(chart_img1, width=2.8*inch, height=2.2*inch)
            img2 = Image(chart_img2, width=2.8*inch, height=2.2*inch)
            
            # Buat table untuk layout side by side
            nutrition_table = Table([[img1, img2]])
            nutrition_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(nutrition_table)
            
            # Tampilkan data nutrisi dalam tabel
            nutrition = extract_nutrition_data(resep_data)
            nutrition_text = (
                f"<b>Nutrisi per Sajian:</b><br/>"
                f"Protein: {nutrition['protein']}g | "
                f"Lemak: {nutrition['fat']}g | "
                f"Karbohidrat: {nutrition['carbs']}g | "
                f"Kalori: {nutrition['calories']} kcal"
            )
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(nutrition_text, body_style))
            story.append(Spacer(1, 0.2*inch))
        elif chart_img1:
            story.append(Paragraph("Komposisi Nutrisi:", heading_style))
            chart_img = Image(chart_img1, width=3.5*inch, height=2.5*inch)
            story.append(chart_img)
            

        # 5. BAHAN-BAHAN
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
        
        # 6. CARA MEMBUAT
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