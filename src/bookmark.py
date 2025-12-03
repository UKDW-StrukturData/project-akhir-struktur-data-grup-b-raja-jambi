import json
import os

# Lokasi file penyimpanan bookmark
DATA_FOLDER = 'data'
BOOKMARK_FILE = os.path.join(DATA_FOLDER, 'bookmarks.json')

def ensure_data_exists():
    """Memastikan folder data dan file json tersedia"""
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)
    if not os.path.exists(BOOKMARK_FILE):
        with open(BOOKMARK_FILE, 'w') as f:
            json.dump({}, f)

def load_bookmarks():
    """Mengambil semua data bookmark"""
    ensure_data_exists()
    try:
        with open(BOOKMARK_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {}

def save_bookmarks(data):
    """Menyimpan data bookmark"""
    ensure_data_exists()
    with open(BOOKMARK_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def add_bookmark(username, recipe_data):
    """Menambah bookmark untuk user tertentu"""
    data = load_bookmarks()
    if username not in data:
        data[username] = []
    
    # Cek duplikasi (biar gak simpen resep yg sama 2x)
    existing_ids = [r['id'] for r in data[username]]
    if recipe_data['id'] not in existing_ids:
        # Kita simpan data pentingnya aja biar hemat storage
        clean_data = {
            'id': recipe_data['id'],
            'title': recipe_data.get('title'),
            'image': recipe_data.get('image'),
            'nutrition': recipe_data.get('nutrition')
        }
        data[username].append(clean_data)
        save_bookmarks(data)
        return True
    return False

def remove_bookmark(username, recipe_id):
    """Menghapus bookmark"""
    data = load_bookmarks()
    if username in data:
        # Filter list, buang yang ID-nya cocok
        data[username] = [r for r in data[username] if r['id'] != recipe_id]
        save_bookmarks(data)
        return True
    return False

def get_user_bookmarks(username):
    """Ambil list bookmark milik user tertentu"""
    data = load_bookmarks()
    return data.get(username, [])