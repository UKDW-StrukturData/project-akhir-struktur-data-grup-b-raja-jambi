import streamlit as st
from src.data_manager import authenticate_user, register_user
# 1. KITA TAMBAHKAN IMPORT INI
from src.api_client import cari_resep_spoonacular 

# (Kita akan butuh ini nanti)
# from src.gemini_client import tanya_ai_gemini 

# Judul Aplikasi (sesuai proposal)
st.title("🍳 Resep hari ini")

# Inisialisasi session state untuk status login
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = ""

# --- FUNGSI UNTUK PROSES LOGIN DAN LOGOUT ---
def handle_login(username, password):
    if authenticate_user(username, password):
        st.session_state['logged_in'] = True
        st.session_state['username'] = username
        st.rerun() 
    else:
        st.error("Username atau password salah.")

def handle_logout():
    st.session_state['logged_in'] = False
    st.session_state['username'] = ""
    st.rerun() 

# --- TAMPILAN UTAMA ---

if st.session_state['logged_in']:
    # === HALAMAN SETELAH LOGIN (DASHBOARD UTAMA ANDA) ===
    
    # --- Sidebar ---
    st.sidebar.success(f"Login sebagai: {st.session_state['username']}")
    st.sidebar.button("Logout", on_click=handle_logout)
    
    st.header(f"Halo {st.session_state['username']}, mau masak apa hari ini?")
    
    tab_cari, tab_ai = st.tabs(["🔍 Pencarian Resep", "🤖 Tanya AI (Gemini)"])
    
    # --- Tab 1: Pencarian Resep ---
    with tab_cari:
        st.subheader("Cari Resep Berdasarkan Bahan")
        
        input_bahan_string = st.text_input(
            "Masukkan bahan-bahan yang Anda miliki (pisahkan dengan koma):", 
            placeholder="Contoh: chicken, soy sauce, rice"
        )
        
        if st.button("Cari Resep"):
            if not input_bahan_string:
                st.warning("Silakan masukkan bahan terlebih dahulu.")
            else:
                bahan_list = [bahan.strip() for bahan in input_bahan_string.split(',')]
                
                # ===================================================
                # 2. MENGGANTI PLACEHOLDER DENGAN PANGGILAN API ASLI
                # ===================================================
                with st.spinner("Mencari resep yang sesuai... 👩‍🍳"):
                    hasil_resep = cari_resep_spoonacular(bahan_list)

                # --- Tampilkan Hasil ---
                if hasil_resep:
                    st.success(f"Kami menemukan {len(hasil_resep)} resep!")
                    
                    # 3. KITA BUAT TAMPILAN HASILNYA (BUKAN JSON LAGI)
                    # (Kita akan buat 3 kolom agar rapi)
                    columns = st.columns(3) 
                    
                    for i, resep in enumerate(hasil_resep):
                        # Taruh tiap resep di kolomnya masing-masing
                        with columns[i % 3]: 
                            st.subheader(resep['title'])
                            st.image(resep['image'])
                            
                            # Cek data nutrisi (Kalori)
                            if 'nutrition' in resep and 'nutrients' in resep['nutrition']:
                                kalori_info = resep['nutrition']['nutrients'][0]
                                st.metric(
                                    label=f"{kalori_info['name']} ({kalori_info['unit']})", 
                                    value=kalori_info['amount']
                                )
                            
                            # Tombol untuk melihat detail (opsional)
                            st.link_button("Lihat Detail", f"https://spoonacular.com/recipes/{resep['title'].replace(' ', '-')}-{resep['id']}")

                else:
                    st.error("Maaf, tidak ada resep yang ditemukan dengan bahan tersebut.")
                    st.info("Info: API mungkin tidak menemukan resep jika bahannya terlalu spesifik atau tidak ada di databasenya.")

    # --- Tab 2: Tanya AI (Gemini) ---
    with tab_ai:
        st.subheader("Tanya AI (Gemini)")
        st.write("Ada pertanyaan soal nutrisi, alternatif bahan, atau tips memasak? Tanyakan di sini!")
        
        ai_prompt = st.text_input("Ketik pesan Anda...", key="ai_input")
        
        if st.button("Kirim ke AI"):
            # (Ini masih placeholder, kita akan kerjakan nanti)
            st.warning("Fitur AI (Gemini) belum terhubung.")

else:
    # === HALAMAN LOGIN / SIGN UP ===
    st.info("Silakan login atau sign up untuk melanjutkan")
    
    tab_login, tab_signup = st.tabs(["🔒 Login", "✍️ Sign Up"])
    
    with tab_login:
        # (Kode login Anda...)
        st.subheader("Silakan Login")
        with st.form("login_form"):
            login_user = st.text_input("Username")
            login_pass = st.text_input("Password", type="password")
            login_submitted = st.form_submit_button("Login")
            
            if login_submitted:
                handle_login(login_user, login_pass)

    with tab_signup:
        # (Kode sign up Anda...)
        st.subheader("Buat Akun Baru")
        with st.form("signup_form"):
            signup_user = st.text_input("Username Baru")
            signup_pass = st.text_input("Password Baru", type="password")
            signup_pass_confirm = st.text_input("Konfirmasi Password", type="password")
            signup_submitted = st.form_submit_button("Sign Up")
            
            if signup_submitted:
                if not signup_user or not signup_pass or not signup_pass_confirm:
                    st.warning("Semua kolom harus diisi.")
                elif signup_pass != signup_pass_confirm:
                    st.error("Password dan konfirmasi password tidak cocok.")
                else:
                    result = register_user(signup_user, signup_pass)
                    if result == "Registrasi berhasil!":
                        st.success(result + " Silakan login.")
                    else:
                        st.error(result)