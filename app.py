import streamlit as st
from src.data_manager import authenticate_user, register_user
# Import dengan alias biar jelas
from src.api_client import cari_resep_spoonacular, dapatkan_resep_random as client_dapatkan_resep_random, dapatkan_detail_resep
import os

# --- KONFIGURASI HALAMAN ---
st.set_page_config(layout="wide", page_title="Resep Hari Ini")

# --- FUNGSI UTILITY & CACHE ---
@st.cache_data(ttl=3600)
def get_cached_random():
    """Wrapper untuk mengambil resep random dengan cache"""
    # Cek API Key dulu
    api_key = st.secrets.get("SPOONACULAR_API_KEY")
    if not api_key:
        api_key = os.getenv("SPOONACULAR_API_KEY")
    
    if not api_key:
        return [] # Return list kosong kalau ga ada key

    try:
        # Panggil fungsi asli yang sudah di-import sebagai client_...
        return client_dapatkan_resep_random(jumlah=20, api_key=api_key)
    except Exception:
        return []

def tampilkan_grid_resep(daftar_resep):
    """Menampilkan resep dalam bentuk Grid 3 Kolom"""
    if not daftar_resep:
        st.warning("Tidak ada data resep untuk ditampilkan.")
        return

    jumlah_kolom = 3
    rows = [daftar_resep[i:i + jumlah_kolom] for i in range(0, len(daftar_resep), jumlah_kolom)]

    for row in rows:
        cols = st.columns(jumlah_kolom)
        for i, resep in enumerate(row):
            with cols[i]:
                # Tampilkan Gambar
                if resep.get('image'):
                    st.image(resep['image'], use_container_width=True)
                
                # Judul
                st.subheader(resep.get('title', 'Tanpa Judul'))
                
                # Info Kalori
                kalori_text = ""
                if 'nutrition' in resep and 'nutrients' in resep['nutrition']:
                    nutrients = resep['nutrition']['nutrients']
                    if isinstance(nutrients, list) and len(nutrients) > 0:
                        kalori = nutrients[0]
                        kalori_text = f"🔥 {kalori['amount']:.0f} {kalori['unit']}"
                
                if kalori_text:
                    st.info(kalori_text)
                
                # Tombol Detail
                if st.button("Lihat Resep", key=f"details_{resep['id']}", use_container_width=True):
                    st.session_state['view'] = 'detail'
                    st.session_state['selected_recipe_id'] = resep['id']
                    st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)

def tampilkan_halaman_detail(recipe_id):
    """Menampilkan detail satu resep"""
    if st.button("<- Kembali ke Daftar Resep"):
        st.session_state['view'] = 'grid'
        st.session_state['selected_recipe_id'] = None
        st.rerun()

    with st.spinner("Mengambil detail resep..."):
        detail_resep = dapatkan_detail_resep(recipe_id)

    if detail_resep:
        st.title(detail_resep['title'])
        if detail_resep.get('image'):
            st.image(detail_resep['image'])

        st.subheader("Ringkasan")
        st.markdown(detail_resep.get('summary', 'Ringkasan tidak tersedia.'), unsafe_allow_html=True)

        st.subheader("Bahan-bahan")
        if detail_resep.get('extendedIngredients'):
            for ingredient in detail_resep['extendedIngredients']:
                st.write(f"- {ingredient['original']}")
        else:
            st.write("Bahan-bahan tidak tersedia.")

        st.subheader("Instruksi")
        st.markdown(detail_resep.get('instructions', 'Instruksi tidak tersedia.'), unsafe_allow_html=True)
    else:
        st.error("Gagal memuat detail resep.")

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
    st.session_state['view'] = 'grid'
    st.session_state['selected_recipe_id'] = None

# --- STATE MANAGEMENT ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = ""
if 'view' not in st.session_state:
    st.session_state['view'] = 'grid'
if 'selected_recipe_id' not in st.session_state:
    st.session_state['selected_recipe_id'] = None

# --- MAIN UI ---
st.title("Resep Hari Ini")

if st.session_state['logged_in']:
    # SIDEBAR
    st.sidebar.title("Navigasi")
    st.sidebar.write(f"Halo, **{st.session_state['username']}**")
    if st.sidebar.button("Logout"):
        handle_logout()
        st.rerun()

    # MAIN CONTENT
    if st.session_state['view'] == 'grid':
        st.header(f"Mau Masak Apa Hari Ini, {st.session_state['username']}?")
        st.write("Cari inspirasi menu masakan dari bahan yang kamu punya.")

        tab_cari, tab_ai = st.tabs(["🍽️ Daftar Menu & Pencarian", "🤖 Tanya Chef AI"])
        
        with tab_cari:
            # Input Pencarian
            col_input, col_btn = st.columns([3, 1])
            with col_input:
                input_bahan_string = st.text_input(
                    "Masukkan bahan:",
                    placeholder="Contoh: chicken, rice, egg (Gunakan Bahasa Inggris)",
                    label_visibility="collapsed"
                )
            with col_btn:
                cari_clicked = st.button("Cari Menu", use_container_width=True)
            
            # Filter
            with st.expander("Filter Pencarian (Diet, Kalori, Jenis)"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    filter_diet = st.selectbox("Jenis Diet", ["Semua", "Vegetarian", "Vegan", "Gluten Free", "Ketogenic"])
                with c2:
                    filter_tipe = st.selectbox("Tipe Makanan", ["Semua", "Main Course", "Breakfast", "Dessert", "Salad", "Soup"])
                with c3:
                    filter_kalori = st.slider("Maksimal Kalori", 50, 1000, 1000, step=50)

            st.markdown("---")

            # Logika Pencarian vs Rekomendasi
            if cari_clicked and input_bahan_string:
                # --- MODE PENCARIAN ---
                bahan_list = [bahan.strip() for bahan in input_bahan_string.split(',')]
                
                status_text = f"🔍 Mencari: **{input_bahan_string}**"
                if filter_diet != "Semua": status_text += f" | Diet: {filter_diet}"
                
                st.write(status_text)
                
                with st.spinner("Mencari resep..."):
                    hasil_resep = cari_resep_spoonacular(
                        bahan_list, 
                        diet=filter_diet, 
                        tipe=filter_tipe, 
                        max_kalori=filter_kalori
                    )
                
                if hasil_resep:
                    tampilkan_grid_resep(hasil_resep)
                else:
                    st.warning("Tidak ditemukan resep. Coba kurangi filter atau ganti bahan.")
            
            else:
                # --- MODE REKOMENDASI (DEFAULT) ---
                st.subheader("✨ Inspirasi Menu Buat Kamu")
                
                with st.spinner("Mengambil rekomendasi chef..."):
                    # Panggil fungsi cache yang sudah dibenerin di atas
                    resep_random = get_cached_random()
                
                if resep_random:
                    tampilkan_grid_resep(resep_random)
                else:
                    st.info("API Key belum diset atau kuota habis. Masukkan API Key di .env")

        with tab_ai:
            st.subheader("Asisten Gizi")
            st.info("Fitur ini akan segera hadir!")
            st.text_input("Tanya sesuatu...")
            st.button("Kirim")

    elif st.session_state['view'] == 'detail':
        tampilkan_halaman_detail(st.session_state['selected_recipe_id'])

else:
    # --- HALAMAN LOGIN/REGISTER ---
    st.info("Silakan Login atau Daftar untuk melihat menu resep.")
    tab_login, tab_signup = st.tabs(["Login", "Daftar"])
    
    with tab_login:
        with st.form("login_form"):
            st.subheader("Login Pengguna")
            login_user = st.text_input("Username")
            login_pass = st.text_input("Password", type="password")
            if st.form_submit_button("Masuk"):
                handle_login(login_user, login_pass)

    with tab_signup:
        with st.form("signup_form"):
            st.subheader("Daftar Akun Baru")
            s_user = st.text_input("Username")
            s_pass = st.text_input("Password", type="password")
            s_confirm = st.text_input("Konfirmasi Password", type="password")
            if st.form_submit_button("Daftar"):
                if s_pass != s_confirm:
                    st.error("Password beda!")
                else:
                    res = register_user(s_user, s_pass)
                    if "berhasil" in res: st.success(res)
                    else: st.error(res)