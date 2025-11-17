import requests
import os
from dotenv import load_dotenv  # <-- Memuat library untuk membaca file .env

# Memuat variabel dari file .env (seperti SPOONACULAR_API_KEY)
load_dotenv()

# 1. Ambil API Key dari environment yang sudah dimuat oleh load_dotenv()
API_KEY = os.environ.get("SPOONACULAR_API_KEY")

# 2. Tentukan URL utama API Spoonacular
BASE_URL = "https://api.spoonacular.com/recipes/complexSearch"

def cari_resep_spoonacular(bahan_bahan_list):
    """
    Mencari resep di Spoonacular berdasarkan bahan,
    dengan filter masakan Indonesia dan data nutrisi.
    """
    
    # Cek apakah API Key berhasil dimuat dari file .env
    if not API_KEY:
        print("="*50)
        print("ERROR: SPOONACULAR_API_KEY tidak ditemukan.")
        print("Pastikan Anda sudah membuat file .env di folder utama")
        print("dan mengisinya dengan: SPOONACULAR_API_KEY='key_anda'")
        print("="*50)
        return None

    # 3. Ubah list bahan menjadi satu string yang dipisah koma
    #    Contoh: ["ayam", "kecap"] -> "ayam,kecap"
    bahan_string = ",".join(bahan_bahan_list)

    # 4. Siapkan parameter untuk dikirim ke API
    params = {
        "apiKey": API_KEY,
        "includeIngredients": bahan_string,  # <-- Sesuai input pengguna
        "cuisine": "Indonesian",             # <-- Filter masakan Indonesia
        "addRecipeNutrition": True,          # <-- Minta data nutrisi (penting!)
        "number": 5                          # <-- Minta 5 resep (hemat kuota gratis)
    }

    # 5. Lakukan panggilan API menggunakan library requests
    try:
        response = requests.get(BASE_URL, params=params)
        
        # Jika request gagal (misal: API key salah, kuota habis)
        response.raise_for_status() 
        
        data = response.json()
        
        # API mengembalikan hasil dalam key 'results'
        return data.get('results', []) # Gunakan .get() agar lebih aman

    except requests.exceptions.RequestException as e:
        print(f"Error saat memanggil API: {e}")
        return None

# ----- (Blok ini untuk mengetes file ini secara langsung) -----
# Anda bisa menjalankan 'python src/api_client.py' di terminal
if __name__ == "__main__":
    # Ganti ini dengan bahan yang ingin Anda tes
    bahan_tes = ["chicken", "soy sauce", "rice"] # (ayam, kecap, nasi)
    
    print(f"Mencari resep dengan bahan: {', '.join(bahan_tes)}")
    hasil = cari_resep_spoonacular(bahan_tes)
    
    if hasil:
        print(f"--- Menemukan {len(hasil)} resep ---")
        for resep in hasil:
            # Ambil data kalori dari bagian nutrisi
            if 'nutrition' in resep and 'nutrients' in resep['nutrition'] and len(resep['nutrition']['nutrients']) > 0:
                kalori = resep['nutrition']['nutrients'][0]['amount']
                print(f"- {resep['title']} (Kalori: {kalori} kcal)")
            else:
                print(f"- {resep['title']} (Data nutrisi tidak tersedia)")
    elif hasil == []:
        print("Tidak ada resep yang ditemukan dengan bahan tersebut.")
    else:
        print("Gagal mengambil data dari API (Cek API Key di file .env).")