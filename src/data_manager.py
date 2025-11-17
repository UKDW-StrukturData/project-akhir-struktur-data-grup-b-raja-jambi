import pandas as pd
import os

# Tentukan path ke file Excel "database" Anda
DB_PATH = os.path.join("data", "users.xlsx")

# KODE BARU YANG BENAR
def load_user_db():
    """Memuat database pengguna dari file Excel."""
    if os.path.exists(DB_PATH):
        try:
            # Coba baca dengan engine openpyxl
            return pd.read_excel(DB_PATH, engine='openpyxl')
        except Exception as e:
            # Jika file ada TAPI KOSONG, pandas akan error.
            # Kita tangkap error itu dan buat DataFrame baru.
            print(f"File users.xlsx kosong. Membuat DataFrame baru. (Error: {e})")
            return pd.DataFrame(columns=["username", "password"])
    else:
        # Jika file tidak ada, buat DataFrame kosong
        return pd.DataFrame(columns=["username", "password"])

def save_user_db(df):
    """Menyimpan DataFrame kembali ke file Excel."""
    df.to_excel(DB_PATH, index=False)

def authenticate_user(username, password):
    """Mengecek apakah username dan password cocok."""
    df_users = load_user_db()
    
    # Cari pengguna
    user = df_users[df_users["username"] == username]
    
    if not user.empty:
        # Jika pengguna ditemukan, cek password
        if user.iloc[0]["password"] == password:
            return True # Login berhasil
    
    return False # Login gagal

def register_user(username, password):
    """Mendaftarkan pengguna baru."""
    df_users = load_user_db()
    
    # Cek apakah username sudah ada
    if not df_users[df_users["username"] == username].empty:
        return "Username sudah terdaftar."
    
    # Jika belum ada, tambahkan pengguna baru
    # Peringatan: Password disimpan sebagai plain text (tidak aman)
    new_user = pd.DataFrame([{"username": username, "password": password}])
    df_updated = pd.concat([df_users, new_user], ignore_index=True)
    
    # Simpan kembali ke Excel
    save_user_db(df_updated)
    return "Registrasi berhasil!"