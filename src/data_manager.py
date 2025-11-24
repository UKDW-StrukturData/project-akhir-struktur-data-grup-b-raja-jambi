import pandas as pd # Library Pandas: Untuk membaca dan mengedit file Excel
import os           # Library OS: Untuk mengatur lokasi file di komputer

# Menentukan lokasi file database (users.xlsx) di dalam folder data
DB_PATH = os.path.join("data", "users.xlsx")

def load_user_db():
    """
    Fungsi untuk Membaca Database Pengguna.
    Mencoba membuka file Excel. Jika file tidak ada atau rusak,
    dia akan membuat tabel kosong baru agar aplikasi tidak error.
    """
    if os.path.exists(DB_PATH):
        try:
            # Buka file Excel dengan engine openpyxl
            return pd.read_excel(DB_PATH, engine='openpyxl')
        except Exception as e:
            print(f"File rusak/kosong, buat baru. Error: {e}")
            return pd.DataFrame(columns=["username", "password"])
    else:
        # Jika file belum ada, buat tabel kosong dengan kolom username & password
        return pd.DataFrame(columns=["username", "password"])

def save_user_db(df):
    """
    Fungsi untuk Menyimpan Database.
    Menulis data (DataFrame) kembali ke file Excel users.xlsx.
    """
    df.to_excel(DB_PATH, index=False, engine='openpyxl')

def authenticate_user(username, password):
    """
    Fungsi Login.
    Mengecek apakah username ada di Excel dan passwordnya cocok.
    """
    df_users = load_user_db() # 1. Baca data terbaru
    
    # 2. Cari baris yang username-nya sama dengan input
    user = df_users[df_users["username"] == username]
    
    if not user.empty:
        # 3. Jika ketemu, cek passwordnya
        if str(user.iloc[0]["password"]) == str(password):
            return True # Login Sukses
    
    return False # Login Gagal

def register_user(username, password):
    """
    Fungsi Pendaftaran.
    Menambah pengguna baru ke baris paling bawah Excel.
    """
    df_users = load_user_db() # 1. Baca data lama
    
    # 2. Cek apakah username sudah dipakai
    if not df_users[df_users["username"] == username].empty:
        return "Username sudah terdaftar."
    
    # 3. Buat baris data baru
    new_user = pd.DataFrame([{"username": username, "password": password}])
    
    # 4. Gabungkan data lama + data baru
    df_updated = pd.concat([df_users, new_user], ignore_index=True)
    
    # 5. Simpan ke file Excel
    save_user_db(df_updated)
    return "Registrasi berhasil!"