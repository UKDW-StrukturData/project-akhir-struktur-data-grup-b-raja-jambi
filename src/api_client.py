import requests # Library untuk mengirim permintaan ke internet (API)
import os       # Library untuk mengakses sistem operasi (mengambil API Key)
from dotenv import load_dotenv # Library untuk membaca file .env

# 1. Memuat konfigurasi rahasia dari .env
load_dotenv() # Membaca file .env
API_KEY = os.environ.get("SPOONACULAR_API_KEY") # Mengambil kunci rahasia

# URL (Alamat) API Spoonacular
BASE_URL = "https://api.spoonacular.com/recipes/complexSearch" # Untuk cari resep
RANDOM_URL = "https://api.spoonacular.com/recipes/random"      # Untuk resep acak
DETAIL_URL = "https://api.spoonacular.com/recipes/{id}/information" # Untuk detail resep

# --- FUNGSI PENCARIAN UTAMA ---
# Kita tambahkan parameter baru: diet, tipe, dan max_kalori (defaultnya None/Kosong)
def cari_resep_spoonacular(bahan_bahan_list, diet=None, tipe=None, max_kalori=None):
    """
    Mengirim permintaan ke Spoonacular dengan filter yang dipilih pengguna.
    """
    # Cek keamanan: Pastikan API Key ada
    if not API_KEY: 
        print("Error: API Key hilang - Pastikan SPOONACULAR_API_KEY ada di file .env")
        return []

    # Mengubah list ["ayam", "nasi"] menjadi string "ayam,nasi"
    bahan_string = ",".join(bahan_bahan_list)

    # Menyiapkan 'Surat' permintaan (Parameters)
    params = {
        "apiKey": API_KEY,              # Kunci akses
        "includeIngredients": bahan_string, # Bahan yang dicari
        "cuisine": "Indonesian",        # Filter masakan Indonesia (bisa dihapus jika mau global)
        "addRecipeNutrition": True,     # Minta data gizi
        "number": 30,                    # Minta 30 hasil
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
        response = requests.get(BASE_URL, params=params, timeout=15)
        response.raise_for_status() # Cek jika ada error (misal koneksi putus)
        data = response.json()      # Ubah hasil jadi format Python (Dictionary)
        results = data.get('results', []) # Ambil bagian 'results'
        
        if not results:
            print(f"Warning: Tidak ada hasil untuk bahan: {bahan_string}")
        
        return results
    except requests.exceptions.Timeout:
        print(f"Error: Request timeout saat mencari resep dengan bahan {bahan_string}")
        return []
    except requests.exceptions.HTTPError as e:
        print(f"Error HTTP {response.status_code} saat pencarian: {e}")
        return []
    except Exception as e:
        print(f"Error API Search: {e}")
        return []

# --- FUNGSI RESEP RANDOM ---
def dapatkan_resep_random(jumlah=3, api_key=None):
    """Mengambil resep acak untuk inspirasi dashboard.

    Parameters
    - jumlah: jumlah resep yang diminta
    - api_key: tidak digunakan lagi (untuk backward compatibility saja)
    """
    # Gunakan API_KEY dari .env
    if not API_KEY:
        print("Error: SPOONACULAR_API_KEY tidak ditemukan di file .env")
        return []

    params = {
        "apiKey": API_KEY,
        "number": jumlah,
        "tags": "main course", # Hanya ambil makanan berat
        "includeNutrition": True
    }

    try:
        response = requests.get(RANDOM_URL, params=params, timeout=15)
        response.raise_for_status()
        # API Random struktur datanya 'recipes', bukan 'results'
        recipes = response.json().get('recipes', [])
        
        if not recipes:
            print(f"Warning: Tidak ada resep random yang ditemukan")
        
        return recipes
    except requests.exceptions.Timeout:
        print(f"Error: Request timeout saat mengambil resep random")
        return []
    except requests.exceptions.HTTPError as e:
        print(f"Error HTTP {response.status_code} saat random: {e}")
        return []
    except Exception as e:
        print(f"Error API Random: {e}")
        return []

# --- FUNGSI DETAIL RESEP ---
def dapatkan_detail_resep(id_resep):
    """Mengambil detail lengkap satu resep berdasarkan ID-nya."""
    if not API_KEY:
        print("Error: API Key hilang - Pastikan SPOONACULAR_API_KEY ada di file .env")
        return None

    url = DETAIL_URL.format(id=id_resep)
    params = {
        "apiKey": API_KEY,
        "includeNutrition": True # Minta info nutrisi juga
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Debug: Print response jika ada masalah
        if not data:
            print(f"Error: Response kosong untuk recipe ID {id_resep}")
            return None
        
        return data
    except requests.exceptions.Timeout:
        print(f"Error: Request timeout untuk recipe ID {id_resep}")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"Error HTTP {response.status_code} untuk recipe ID {id_resep}: {e}")
        return None
    except Exception as e:
        print(f"Error API Detail untuk recipe ID {id_resep}: {e}")
        return None