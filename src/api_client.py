import requests # Library untuk mengirim permintaan ke internet (API)
import os       # Library untuk mengakses sistem operasi (mengambil API Key)
from dotenv import load_dotenv # Library untuk membaca file .env

# 1. Memuat konfigurasi rahasia
load_dotenv() # Membaca file .env
API_KEY = os.environ.get("SPOONACULAR_API_KEY") # Mengambil kunci rahasia

# URL (Alamat) API Spoonacular
BASE_URL = "https://api.spoonacular.com/recipes/complexSearch" # Untuk cari resep
RANDOM_URL = "https://api.spoonacular.com/recipes/random"      # Untuk resep acak

# --- FUNGSI PENCARIAN UTAMA ---
# Kita tambahkan parameter baru: diet, tipe, dan max_kalori (defaultnya None/Kosong)
def cari_resep_spoonacular(bahan_bahan_list, diet=None, tipe=None, max_kalori=None):
    """
    Mengirim permintaan ke Spoonacular dengan filter yang dipilih pengguna.
    """
    # Cek keamanan: Pastikan API Key ada
    if not API_KEY: 
        print("Error: API Key hilang.")
        return []

    # Mengubah list ["ayam", "nasi"] menjadi string "ayam,nasi"
    bahan_string = ",".join(bahan_bahan_list)

    # Menyiapkan 'Surat' permintaan (Parameters)
    params = {
        "apiKey": API_KEY,              # Kunci akses
        "includeIngredients": bahan_string, # Bahan yang dicari
        "cuisine": "Indonesian",        # Filter masakan Indonesia (bisa dihapus jika mau global)
        "addRecipeNutrition": True,     # Minta data gizi
        "number": 9,                    # Minta 9 hasil
        "fillIngredients": True         # Minta info detail bahan
    }

    # --- LOGIKA FILTER TAMBAHAN ---
    # Jika pengguna memilih Diet (misal: Vegetarian), masukkan ke params
    if diet and diet != "Semua":
        params['diet'] = diet
    
    # Jika pengguna memilih Tipe (misal: Sarapan), masukkan ke params
    if tipe and tipe != "Semua":
        params['type'] = tipe.lower() # API butuh huruf kecil (breakfast)

    # Jika pengguna mengatur Slider Kalori, masukkan ke params
    if max_kalori and max_kalori < 1000: # Jika diset < 1000, baru kita filter
        params['maxCalories'] = max_kalori

    # Mengirim permintaan ke server Spoonacular
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status() # Cek jika ada error (misal koneksi putus)
        data = response.json()      # Ubah hasil jadi format Python (Dictionary)
        return data.get('results', []) # Ambil bagian 'results'
    except Exception as e:
        print(f"Error API Search: {e}")
        return []

# --- FUNGSI RESEP RANDOM ---
def dapatkan_resep_random(jumlah=3):
    """Mengambil resep acak untuk inspirasi dashboard."""
    if not API_KEY: return []
    
    params = {
        "apiKey": API_KEY,
        "number": jumlah,
        "tags": "main course", # Hanya ambil makanan berat
        "includeNutrition": True
    }
    
    try:
        response = requests.get(RANDOM_URL, params=params)
        response.raise_for_status()
        # API Random struktur datanya 'recipes', bukan 'results'
        return response.json().get('recipes', [])
    except Exception as e:
        print(f"Error API Random: {e}")
        return []