import pandas as pd
import os

 
DB_PATH = os.path.join("data", "users.xlsx")

def load_user_db():
    """Memuat database pengguna dari file Excel."""
    if os.path.exists(DB_PATH):
        try:
 
            return pd.read_excel(DB_PATH, engine='openpyxl')
        except Exception as e:
 
            print(f"File users.xlsx kosong. Membuat DataFrame baru. (Error: {e})")
            return pd.DataFrame(columns=["username", "password"])
    else:
 
        return pd.DataFrame(columns=["username", "password"])

def save_user_db(df):
    """Menyimpan DataFrame kembali ke file Excel."""
    df.to_excel(DB_PATH, index=False)

def authenticate_user(username, password):
    """Mengecek apakah username dan password cocok."""
    df_users = load_user_db()
    

    user = df_users[df_users["username"] == username]
    
    if not user.empty:
 
        if user.iloc[0]["password"] == password:
            return True 
    
    return False 

def register_user(username, password):
    """Mendaftarkan pengguna baru."""
    df_users = load_user_db()
    
 
    if not df_users[df_users["username"] == username].empty:
        return "Username sudah terdaftar."
    
 
    new_user = pd.DataFrame([{"username": username, "password": password}])
    df_updated = pd.concat([df_users, new_user], ignore_index=True)
    
 
    save_user_db(df_updated)
    return "Registrasi berhasil!"