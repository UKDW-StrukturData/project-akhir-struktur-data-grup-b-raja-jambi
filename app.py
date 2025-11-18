import streamlit as st
from src.data_manager import authenticate_user, register_user
 
# from src.api_client import cari_resep_spoonacular 

# Judul Aplikasi
st.title("Ini judul nya")

 
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = ""

#FUNGSI UNTUK PROSES LOGIN DAN LOGOUT
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

#tampilan utama
if st.session_state['logged_in']:

    st.sidebar.success(f"Login sebagai: {st.session_state['username']}")
    st.sidebar.button("Logout", on_click=handle_logout)
    
    st.header(f"Halo {st.session_state['username']}, mau masak apa hari ini?")
    
    tab_cari, tab_ai = st.tabs([" Pencarian menu", "🤖 Tanya AI (Gemini)"])
    
#tab
    with tab_cari:
        st.subheader("Cari Resep Berdasarkan Bahan")
        
        input_bahan_string = st.text_input(
            "Masukkan nama makanan", 
        )
        
        if st.button("Cari Resep"):
            if not input_bahan_string:
                st.warning("Silakan masukkan bahan terlebih dahulu.")
            else:
                bahan_list = [bahan.strip() for bahan in input_bahan_string.split(',')]
                
 
else:

    st.info("Silakan login atau sign up untuk melanjutkan")
    
    tab_login, tab_signup = st.tabs(["Login", "Sign Up"])
    
    with tab_login:

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