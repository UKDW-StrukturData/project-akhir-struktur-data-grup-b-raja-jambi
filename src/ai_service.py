import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

def tanya_chef_ai(pertanyaan, username="Pengguna"):
    """
    Mengirim pertanyaan ke Google Gemini dengan persona Chef.
    """
    if not API_KEY:
        return "Maaf, API Key Chef AI belum dipasang."

    try:
        # Konfigurasi
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # --- PROMPT ENGINEERING ---
        # Kita bungkus pertanyaan user dengan instruksi agar AI bertingkah seperti Chef
        prompt_khusus = f"""
        Kamu adalah Chef AI, asisten masak profesional yang ramah dan ahli gizi.
        Nama pengguna saat ini adalah: {username}.
        
        Tugasmu:
        1. Jawab pertanyaan seputar resep, bahan makanan, teknik memasak, dan gizi.
        2. Gunakan bahasa Indonesia yang santai tapi sopan.
        3. Jika ditanya di luar topik masak (misal politik/coding), tolak dengan halus dan ajak kembali bahas makanan.
        4. Berikan tips tambahan jika relevan (misal cara memotong atau pengganti bahan).

        Pertanyaan User: {pertanyaan}
        """

        response = model.generate_content(prompt_khusus)
        return response.text
        
    except Exception as e:
        return f"Waduh, Chef AI sedang sibuk (Error: {e})"