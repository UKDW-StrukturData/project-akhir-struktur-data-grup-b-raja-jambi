from fpdf import FPDF
from bs4 import BeautifulSoup
import requests
from io import BytesIO

class ResepPDF(FPDF):
    def header(self):
        # KOSONGIN AJA BIAR GAK ADA WATERMARK / TULISAN DI ATAS
        pass

    def footer(self):
        # Footer tetap ada nomor halaman di bawah (kecil)
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Halaman {self.page_no()}', align='C')

def clean_html(raw_html):
    """Membersihkan tag HTML"""
    if not raw_html:
        return ""
    try:
        soup = BeautifulSoup(str(raw_html), "html.parser")
        return soup.get_text()
    except Exception:
        return str(raw_html)

def generate_pdf_bytes(resep_data):
    # 1. Setup Halaman A4
    pdf = ResepPDF(orientation='P', unit='mm', format='A4')
    pdf.set_margins(15, 15, 15) # Kiri, Atas, Kanan
    pdf.add_page()

    # 2. JUDUL RESEP
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(0, 0, 0)
    pdf.set_x(15)
    judul = clean_html(resep_data.get('title', 'Tanpa Judul'))
    pdf.multi_cell(0, 10, judul, align='C')
    pdf.ln(5)

    # 3. GAMBAR (Dibuat lebih rapi & presisi)
    image_url = resep_data.get('image')
    if image_url:
        try:
            response = requests.get(image_url, timeout=5)
            if response.status_code == 200:
                img_data = BytesIO(response.content)
                
                # Tentukan Lebar Gambar (Misal 90mm biar gak kegedean)
                img_w = 90
                # Hitung posisi X biar bener-bener di tengah halaman A4 (210mm)
                # Rumus: (Lebar Kertas - Lebar Gambar) / 2
                x_center = (210 - img_w) / 2
                
                pdf.image(img_data, x=x_center, w=img_w)
                pdf.ln(10)
        except Exception:
            pass

    # RESET KURSOR (Wajib!)
    pdf.set_x(15)

    # 4. STATISTIK
    waktu = resep_data.get('readyInMinutes', '-')
    porsi = resep_data.get('servings', '-')
    
    pdf.set_font("Helvetica", "I", 12)
    pdf.cell(0, 10, f"Waktu Masak: {waktu} Menit  |  Porsi: {porsi} Orang", align='C')
    pdf.ln(15)

    # 5. BAHAN-BAHAN
    pdf.set_x(15)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Bahan-Bahan:")
    pdf.ln(8)
    
    pdf.set_font("Helvetica", "", 12)
    ingredients = resep_data.get('extendedIngredients', [])
    if ingredients:
        for ing in ingredients:
            pdf.set_x(15)
            original_text = clean_html(ing.get('original', ''))
            pdf.multi_cell(0, 7, f"- {original_text}")
    else:
        pdf.cell(0, 10, "Data bahan tidak tersedia.")
    pdf.ln(10)

    # 6. CARA MEMBUAT
    pdf.set_x(15)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Cara Membuat:")
    pdf.ln(8)

    pdf.set_font("Helvetica", "", 12)
    instructions = resep_data.get('instructions')
    
    if instructions:
        pdf.set_x(15)
        clean_instructions = clean_html(instructions)
        pdf.multi_cell(0, 7, clean_instructions)
    else:
        pdf.multi_cell(0, 7, "Instruksi tidak tersedia untuk resep ini.")

    return bytes(pdf.output(dest='S'))