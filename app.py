import streamlit as st
from src.data_manager import authenticate_user, register_user
from src.api_client import cari_resep_spoonacular, dapatkan_resep_random as client_dapatkan_resep_random, dapatkan_detail_resep
from src.bookmark import add_bookmark, remove_bookmark, get_user_bookmarks
from src.history import add_to_history, get_user_history, get_user_history_detailed, clear_user_history
# Import modul PDF yang baru dibuat
from src.pdf_utils import generate_pdf_bytes

# --- KONFIGURASI HALAMAN ---
st.set_page_config(layout="wide", page_title="Resep Hari Ini")

# --- FUNGSI UTILITY & CACHE ---
@st.cache_data(ttl=3600)
def get_cached_random():
    """Wrapper untuk mengambil resep random dengan cache"""
    try:
        # Function dari api_client.py sudah handle API key dari berbagai sumber
        return client_dapatkan_resep_random(jumlah=12)
    except Exception as e:
        print(f"Error getting cached random: {e}")
        return []

def tampilkan_grid_resep(daftar_resep, mode_hapus=False, source="umum"):
    """
    Menampilkan resep dalam bentuk Grid (3 kolom).
    """
    if not daftar_resep:
        st.warning("Belum ada resep di sini.")
        return

    jumlah_kolom = 3
    rows = [daftar_resep[i:i + jumlah_kolom] for i in range(0, len(daftar_resep), jumlah_kolom)]

    current_user = st.session_state.get('username')

    for row in rows:
        cols = st.columns(jumlah_kolom)
        for i, resep in enumerate(row):
            with cols[i]:
                with st.container(border=True):
                    # Gambar
                    if resep.get('image'):
                        st.image(resep['image'], use_container_width=True)
                    
                    # Judul
                    st.subheader(resep.get('title', 'Tanpa Judul'))
                    
                    # Info Kalori (Opsional)
                    kalori_text = ""
                    if 'nutrition' in resep and 'nutrients' in resep['nutrition']:
                        nutrients = resep['nutrition']['nutrients']
                        if isinstance(nutrients, list) and len(nutrients) > 0:
                            kalori = nutrients[0]
                            kalori_text = f"🔥 {kalori['amount']:.0f} {kalori['unit']}"
                    if kalori_text:
                        st.caption(kalori_text)
                    
                    # --- TOMBOL AKSI ---
                    c_btn1, c_btn2 = st.columns([1, 1])
                    
                    with c_btn1:
                        # Key unik gabungan ID resep + sumber
                        key_lihat = f"det_{resep['id']}_{source}"
                        if st.button("Lihat", key=key_lihat, use_container_width=True):
                            st.session_state['view'] = 'detail'
                            st.session_state['selected_recipe_id'] = resep['id']
                            st.rerun()
                    
                    with c_btn2:
                        if mode_hapus:
                            # Tombol Hapus (Khusus Tab Favorit)
                            key_hapus = f"rm_{resep['id']}_{source}"
                            if st.button("🗑️ Hapus", key=key_hapus, type="primary", use_container_width=True):
                                remove_bookmark(current_user, resep['id'])
                                st.toast("Resep dihapus dari favorit!", icon="🗑️")
                                st.rerun()
                        else:
                            # Tombol Simpan (Tab Cari/Home)
                            key_simpan = f"sav_{resep['id']}_{source}"
                            if st.button("❤️ Simpan", key=key_simpan, use_container_width=True):
                                if current_user:
                                    # PENTING: Simpan ID saja!
                                    if add_bookmark(current_user, resep['id']):
                                        st.toast("Resep berhasil disimpan!", icon="✅")
                                    else:
                                        st.toast("Resep ini sudah ada di favoritmu.", icon="ℹ️")
                                else:
                                    st.error("Login dulu bos!")

def tampilkan_halaman_detail(recipe_id):
    """
    Menampilkan detail satu resep + TOMBOL DOWNLOAD PDF
    """
    if st.button("<- Kembali"):
        st.session_state['view'] = 'grid'
        st.session_state['selected_recipe_id'] = None
        st.rerun()

    with st.spinner("Mengambil detail resep..."):
        try:
            detail_resep = dapatkan_detail_resep(recipe_id)
        except Exception as e:
            st.error(f"Error mengambil detail resep: {e}")
            detail_resep = None

    if detail_resep:
        # ===== CATAT KE HISTORY =====
        current_user = st.session_state.get('username')
        if current_user:
            try:
                add_to_history(current_user, recipe_id)
            except Exception as e:
                print(f"Error menambah history: {e}")
        
        st.title(detail_resep.get('title', 'Resep Tanpa Judul'))
        if detail_resep.get('image'):
            st.image(detail_resep['image'])
        
        # --- AREA TOMBOL AKSI (Simpan & PDF) ---
        col_btn1, col_btn2 = st.columns([1, 1])
        
        with col_btn1:
            if st.button("❤️ Simpan ke Favorit", key="save_detail_page", use_container_width=True):
                 add_bookmark(st.session_state['username'], detail_resep['id'])
                 st.success("Tersimpan!")

        with col_btn2:
            # Generate PDF secara real-time
            try:
                pdf_data = generate_pdf_bytes(detail_resep)
                
                # Buat nama file bersih (spasi jadi underscore)
                nama_file = detail_resep['title'].replace(" ", "_").lower() + ".pdf"
                
                st.download_button(
                    label="📄 Export ke PDF",
                    data=pdf_data,
                    file_name=nama_file,
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Gagal membuat PDF: {e}")
        # ---------------------------------------

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
        st.error(f"❌ Gagal memuat detail resep (ID: {recipe_id}). Cek koneksi internet atau API Key di .env")
        st.info("💡 Buka terminal dan cek pesan error untuk detail lebih lanjut.")

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
    st.session_state['hasil_pencarian'] = None

# --- STATE MANAGEMENT ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = ""
if 'view' not in st.session_state:
    st.session_state['view'] = 'grid'
if 'selected_recipe_id' not in st.session_state:
    st.session_state['selected_recipe_id'] = None
if 'hasil_pencarian' not in st.session_state:
    st.session_state['hasil_pencarian'] = None

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
        
        tab_cari, tab_history, tab_favorit, tab_ai = st.tabs(["🍽️ Cari Menu", "⏱️ Riwayat Lihat", "❤️ Favorit Saya", "🤖 Tanya Chef AI"])
        
        # TAB 1: PENCARIAN
        with tab_cari:
            st.write("Cari inspirasi menu masakan dari bahan yang kamu punya.")
            col_input, col_btn = st.columns([3, 1])
            with col_input:
                input_bahan_string = st.text_input(
                    "Masukkan bahan:",
                    placeholder="Contoh: chicken, rice, egg",
                    label_visibility="collapsed"
                )
            with col_btn:
                cari_clicked = st.button("Cari Menu", use_container_width=True)
            
            with st.expander("Filter Pencarian (Diet, Kalori, Jenis)"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    filter_diet = st.selectbox("Jenis Diet", ["Semua", "Vegetarian", "Vegan", "Gluten Free", "Ketogenic"])
                with c2:
                    filter_tipe = st.selectbox("Tipe Makanan", ["Semua", "Main Course", "Breakfast", "Dessert", "Salad", "Soup"])
                with c3:
                    filter_kalori = st.slider("Maksimal Kalori", 50, 1000, 1000, step=50)

            st.markdown("---")

            if cari_clicked and input_bahan_string:
                bahan_list = [bahan.strip() for bahan in input_bahan_string.split(',')]
                
                status_text = f"🔍 Mencari: **{input_bahan_string}**"
                if filter_diet != "Semua": status_text += f" | Diet: {filter_diet}"
                st.info(status_text)
                
                with st.spinner("Mencari resep..."):
                    hasil_resep = cari_resep_spoonacular(
                        bahan_list, 
                        diet=filter_diet, 
                        tipe=filter_tipe, 
                        max_kalori=filter_kalori
                    )
                    st.session_state['hasil_pencarian'] = hasil_resep
            
            if st.session_state['hasil_pencarian'] is not None:
                if st.button("❌ Hapus Pencarian & Kembali"):
                    st.session_state['hasil_pencarian'] = None
                    st.rerun()
                tampilkan_grid_resep(st.session_state['hasil_pencarian'], source="cari")
            
            else:
                st.subheader("✨ Inspirasi Menu Buat Kamu")
                with st.spinner("Mengambil rekomendasi chef..."):
                    resep_random = get_cached_random()
                if resep_random:
                    tampilkan_grid_resep(resep_random, source="rekomen")
                else:
                    st.info("API Key belum diset atau kuota habis.")

        # TAB 2: HISTORY (RIWAYAT LIHAT)
        with tab_history:
            st.subheader("Riwayat Resep yang Sudah Dilihat")
            
            # 1. Ambil list ID history user
            list_id_history = get_user_history(st.session_state['username'])
            history_detailed = get_user_history_detailed(st.session_state['username'])
            
            data_history_lengkap = []
            
            if list_id_history:
                # 2. Loop ID untuk ambil data lengkap dari API
                with st.spinner(f"Memuat {len(list_id_history)} resep dari riwayat..."):
                    for rid in list_id_history:
                        try:
                            detail = dapatkan_detail_resep(rid)
                            if detail:
                                data_history_lengkap.append(detail)
                        except Exception:
                            pass # Skip jika gagal load
                
                if data_history_lengkap:
                    # 3. Tampilkan dengan info timestamp
                    col_hapus, col_info = st.columns([1, 3])
                    with col_hapus:
                        if st.button("🗑️ Hapus Semua", use_container_width=True):
                            clear_user_history(st.session_state['username'])
                            st.success("Riwayat dihapus!")
                            st.rerun()
                    
                    with col_info:
                        st.caption(f"📊 Total: {len(list_id_history)} resep dilihat")
                    
                    st.markdown("---")
                    
                    # Tampilkan grid dengan timestamp
                    tampilkan_grid_resep(data_history_lengkap, source="history")
                    
                    # Tampilkan info timestamp di bawah
                    if history_detailed:
                        st.markdown("---")
                        with st.expander("📅 Detail Waktu Lihat"):
                            for item in history_detailed[:10]:  # Tampilkan 10 terbaru
                                st.caption(f"📌 ID {item.get('recipe_id')} - Dilihat: {item.get('viewed_at')}")
                else:
                    st.error("Gagal memuat detail resep (Cek koneksi internet).")
            else:
                st.info("Kamu belum melihat resep apapun. Coba cari dan lihat beberapa resep di tab 'Cari Menu'!")

        # TAB 3: FAVORIT (LOGIKA BARU)
        with tab_favorit:
            st.subheader("Koleksi Resep Favoritmu")
            
            # 1. Ambil list ID bookmark user
            list_id_bookmark = get_user_bookmarks(st.session_state['username'])
            
            data_bookmark_lengkap = []
            
            if list_id_bookmark:
                # 2. Loop ID untuk ambil data lengkap dari API
                with st.spinner(f"Memuat {len(list_id_bookmark)} resep favorit dari database Raja Iblis..."):
                    # Kita loop satu-satu untuk fetch detail
                    for rid in list_id_bookmark:
                        try:
                            detail = dapatkan_detail_resep(rid)
                            if detail:
                                data_bookmark_lengkap.append(detail)
                        except Exception:
                            pass # Skip jika gagal load
                
                if data_bookmark_lengkap:
                    # 3. Tampilkan hasilnya
                    tampilkan_grid_resep(data_bookmark_lengkap, mode_hapus=True, source="fav")
                else:
                    st.error("Gagal memuat detail resep (Cek koneksi internet).")
            else:
                st.info("Kamu belum menyimpan resep apapun. Klik tombol ❤️ pada resep untuk menyimpan.")

        # TAB 4: AI (COMING SOON)
        with tab_ai:
            st.subheader("Asisten Gizi")
            st.info("Fitur 'Chef AI' sedang dalam perbaikan oleh teman Rio. Ditunggu ya!")

    elif st.session_state['view'] == 'detail':
        tampilkan_halaman_detail(st.session_state['selected_recipe_id'])

else:
    # HALAMAN LOGIN / DAFTAR
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
