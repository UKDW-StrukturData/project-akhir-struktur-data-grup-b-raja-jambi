import json
import os

# --- KONFIGURASI FILE ---
DATA_FOLDER = 'data'
BOOKMARK_FILE = os.path.join(DATA_FOLDER, 'bookmarks.json')

def ensure_data_exists():
    """
    Memastikan folder 'data' dan file 'bookmarks.json' tersedia.
    Jika tidak ada, akan dibuat otomatis.
    """
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)
    
    if not os.path.exists(BOOKMARK_FILE):
        with open(BOOKMARK_FILE, 'w') as f:
            # Inisialisasi dengan dictionary kosong
            json.dump({}, f)

def load_bookmarks():
    """
    Membaca seluruh data bookmark dari file JSON.
    """
    ensure_data_exists()
    try:
        with open(BOOKMARK_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_bookmarks(data):
    """
    Menulis kembali data ke file JSON.
    """
    ensure_data_exists()
    with open(BOOKMARK_FILE, 'w') as f:
        # indent=4 biar rapi kalau mau dibaca manusia, 
        # tapi karena isinya cuma angka, ini tetap hemat memori.
        json.dump(data, f, indent=4)

def add_bookmark(username, recipe_id):
    """
    Menambahkan ID resep ke daftar bookmark user.
    Hanya menyimpan angka (ID), bukan seluruh data resep.
    """
    if not username:
        return False

    data = load_bookmarks()
    
    # Buat list kosong jika user belum punya bookmark
    if username not in data:
        data[username] = []
    
    try:
        # Pastikan ID disimpan sebagai integer agar seragam
        rid = int(recipe_id)
        
        # Cek duplikasi: hanya simpan jika belum ada
        if rid not in data[username]:
            data[username].append(rid)
            save_bookmarks(data)
            return True
        else:
            # Sudah ada, anggap sukses tapi tidak nambah
            return False
            
    except ValueError:
        print(f"Error: ID resep '{recipe_id}' tidak valid.")
        return False

def remove_bookmark(username, recipe_id):
    """
    Menghapus ID resep dari daftar bookmark user.
    """
    if not username:
        return False

    data = load_bookmarks()
    
    if username in data:
        try:
            rid = int(recipe_id)
            if rid in data[username]:
                data[username].remove(rid)
                save_bookmarks(data)
                return True
        except ValueError:
            return False
            
    return False

def get_user_bookmarks(username):
    data = load_bookmarks()
    # Kembalikan list kosong [] jika user tidak ditemukan
    return data.get(username, [])