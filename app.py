import streamlit as st # Library utama untuk membuat website
from src.data_manager import authenticate_user, register_user
# from src.api_client import cari_resep_spoonacular, dapatkan_resep_random 

# 1. Konfigurasi Halaman (Judul di Tab Browser & Layout Lebar)
st.set_page_config(layout="wide", page_title="Resep Hari Ini")

st.title(" Resep Hari Ini")

# 2. Cek Status Login (Session State)
# Session State itu ingatan sementara browser. Kalau di-refresh, dia ingat kita sudah login.
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = ""

# --- FUNGSI BANTUAN TAMPILAN (GRID) ---
def tampilkan_grid_resep(daftar_resep):
    """Membuat tampilan kotak-kotak (Grid) 3 kolom untuk hasil resep."""
    jumlah_kolom = 3
    # Memotong daftar resep menjadi baris-baris (Chunking)
    rows = [daftar_resep[i:i + jumlah_kolom] for i in range(0, len(daftar_resep), jumlah_kolom)]

    for row in rows:
        cols = st.columns(jumlah_kolom) # Buat 3 kolom kosong
        for i, resep in enumerate(row):
            with cols[i]: # Isi setiap kolom
                # Tampilkan Gambar
                if resep.get('image'):
                    st.image(resep['image'], use_container_width=True)
                
                # Tampilkan Judul
                st.subheader(resep['title'])
                
                # Logika mengambil Kalori (karena struktur data API kadang beda)
                kalori_text = ""
                if 'nutrition' in resep and 'nutrients' in resep['nutrition']:
                    nutrients = resep['nutrition']['nutrients']
                    if isinstance(nutrients, list) and len(nutrients) > 0:
                        # Biasanya kalori ada di urutan pertama
                        kalori = nutrients[0] 
                        kalori_text = f"🔥 {kalori['amount']:.0f} {kalori['unit']}"
                
                if kalori_text:
                    st.info(kalori_text) # Tampilkan kotak biru info kalori
                
                # Tombol Link ke Website Resep
                link = f"https://spoonacular.com/recipes/{resep['title'].replace(' ', '-')}-{resep['id']}"
                st.link_button("Lihat Resep", link, use_container_width=True)
        st.markdown("<br>", unsafe_allow_html=True) # Jarak antar baris

# --- FUNGSI LOGIN / LOGOUT ---
def handle_login(username, password):
    # Cek ke Excel (lewat data_manager)
    if authenticate_user(username, password):
        st.session_state['logged_in'] = True # Set ingatan browser jadi True
        st.session_state['username'] = username
        st.rerun() # Refresh halaman agar masuk ke Dashboard
    else:
        st.error("Username atau password salah.")

def handle_logout():
    st.session_state['logged_in'] = False
    st.session_state['username'] = ""
 

# ==========================================
# === LOGIKA UTAMA APLIKASI (MAIN FLOW) ===
# ==========================================

if st.session_state['logged_in']:
    # Jika SUDAH Login, tampilkan Dashboard
    
    # Sidebar (Menu Samping)
    st.sidebar.title("Navigasi")
    st.sidebar.write(f"Halo, **{st.session_state['username']}**")
    st.sidebar.button("Logout", on_click=handle_logout)
    
    st.header(f"Mau Masak Apa Hari Ini, {st.session_state['username']}?")
    st.write("Cari inspirasi menu masakan dari bahan yang kamu punya.")

    # Membuat Tab (Menu Atas)
    tab_cari, tab_ai = st.tabs(["🍽️ Daftar Menu & Pencarian", "🤖 Tanya Chef AI"])
    
    # --- TAB 1: PENCARIAN ---
    with tab_cari:
        # Layout Input: Kolom Input (3 bagian) + Tombol (1 bagian)
        col_input, col_btn = st.columns([3, 1])
        with col_input:
            input_bahan_string = st.text_input(
                "Masukkan bahan:",
                placeholder= "Contoh: chicken, rice, egg (Gunakan Bahasa Inggris)",
                label_visibility="collapsed"
            )
        with col_btn:
            cari_clicked = st.button("Cari Menu", use_container_width=True)
        
        # === FITUR BARU: FILTER PENCARIAN ===
        with st.expander(" Filter Pencarian (Diet, Kalori, Jenis)"):
            c1, c2, c3 = st.columns(3)
            with c1:
                # Pilihan Diet
                filter_diet = st.selectbox("Jenis Diet", ["Semua", "Vegetarian", "Vegan", "Gluten Free", "Ketogenic"])
            with c2:
                # Pilihan Tipe Makanan
                filter_tipe = st.selectbox("Tipe Makanan", ["Semua", "Main Course", "Breakfast", "Dessert", "Salad", "Soup"])
            with c3:
                # Slider Kalori
                filter_kalori = st.slider("Maksimal Kalori", 50, 1000, 1000, step=50, help="Geser untuk membatasi kalori per porsi")

        st.markdown("---") 

        # === LOGIKA TAMPILAN ===
        if cari_clicked and input_bahan_string:
            # KONDISI 1: User mencari resep
            
            # Ubah input string "ayam, nasi" jadi list ["ayam", "nasi"]
            bahan_list = [bahan.strip() for bahan in input_bahan_string.split(',')]
            
            # Tampilkan pesan status
            status_text = f"🔍 Mencari: **{input_bahan_string}**"
            if filter_diet != "Semua": status_text += f" | Diet: {filter_diet}"
            if filter_kalori < 1000: status_text += f" | Max {filter_kalori} Kcal"
            st.write(status_text)
            
            with st.spinner("Mencari resep..."):
                # PANGGIL API DENGAN FILTER
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
            # KONDISI 2: Tampilan Awal (Rekomendasi Random)
            st.subheader("✨ Inspirasi Menu Buat Kamu")
            
            # Cache data random (Simpan 1 jam di memori biar hemat kuota API)
            @st.cache_data(ttl=3600) 
            def get_cached_random():
                return dapatkan_resep_random(jumlah=20)

            with st.spinner("Mengambil rekomendasi chef..."):
                resep_random = get_cached_random()
            
            if resep_random:
                tampilkan_grid_resep(resep_random)
            else:
                st.info("Siap mencari resep! Ketik bahan di atas.")

    # --- TAB 2: AI (Placeholder) ---
    with tab_ai:
        st.subheader("Asisten Gizi")
        st.info("belum ada")
        st.text_input("Tanya sesuatu...")
        st.button("Kirim")

else:
    # Jika BELUM Login, tampilkan form Login/Signup
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
