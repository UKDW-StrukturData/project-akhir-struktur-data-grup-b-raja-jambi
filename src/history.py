import json
import os
from datetime import datetime

# --- KONFIGURASI FILE ---
DATA_FOLDER = 'data'
HISTORY_FILE = os.path.join(DATA_FOLDER, 'history.json')

def ensure_data_exists():
    """
    Memastikan folder 'data' dan file 'history.json' tersedia.
    Jika tidak ada, akan dibuat otomatis.
    """
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)
    
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'w') as f:
            json.dump({}, f)

def load_history():
    """
    Membaca seluruh data history dari file JSON.
    """
    ensure_data_exists()
    try:
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_history(data):
    """
    Menulis kembali data ke file JSON.
    """
    ensure_data_exists()
    with open(HISTORY_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def add_to_history(username, recipe_id):
    """
    Menambahkan ID resep ke history user.
    Menyimpan ID dan timestamp kapan resep dilihat.
    
    Format data:
    {
        "username": [
            {"recipe_id": 12345, "viewed_at": "2025-12-16 10:30:45"},
            ...
        ]
    }
    """
    if not username:
        return False

    data = load_history()
    
    # Buat list kosong jika user belum punya history
    if username not in data:
        data[username] = []
    
    try:
        rid = int(recipe_id)
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Cek apakah recipe_id sudah ada di history
        # Jika sudah ada, pindahkan ke posisi teratas (update timestamp)
        for item in data[username]:
            if item.get("recipe_id") == rid:
                data[username].remove(item)
                break
        
        # Tambahkan ke bagian paling atas (most recent)
        data[username].insert(0, {
            "recipe_id": rid,
            "viewed_at": current_time
        })
        
        # Simpan hanya 20 history terbaru per user
        data[username] = data[username][:20]
        
        save_history(data)
        return True
            
    except ValueError:
        print(f"Error: ID resep '{recipe_id}' tidak valid.")
        return False

def get_user_history(username):
    """
    Mengambil history resep user.
    Mengembalikan list ID resep yang paling baru dilihat (sorted by time).
    """
    data = load_history()
    history_data = data.get(username, [])
    
    # Extract hanya recipe_id dari history
    return [item.get("recipe_id") for item in history_data if item.get("recipe_id")]

def get_user_history_detailed(username):
    """
    Mengambil history lengkap dengan timestamp untuk tampilan.
    """
    data = load_history()
    return data.get(username, [])

def clear_user_history(username):
    """
    Menghapus semua history user.
    """
    if not username:
        return False

    data = load_history()
    
    if username in data:
        data[username] = []
        save_history(data)
        return True
    
    return False
