import streamlit as st
from src.data_manager import authenticate_user, register_user
from src.api_client import cari_resep_spoonacular, dapatkan_resep_random as client_dapatkan_resep_random, dapatkan_detail_resep
from src.bookmark import add_bookmark, remove_bookmark, get_user_bookmarks
from src.history import add_to_history, get_user_history, get_user_history_detailed, clear_user_history
# Import modul PDF yang baru dibuat
from src.pdf_utils import generate_pdf_bytes
import plotly.graph_objects as go
from src.ai_helper import tanya_chef_ai, get_chat_history, add_chat_message, clear_chat_history, ai_search_recipes
from src import ai_helper

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


# Caching wrapper for AI calls to reduce repeated external requests
@st.cache_data(ttl=3600)
def cached_tanya_chef_ai(prompt, username, api_key_marker):
    try:
        return tanya_chef_ai(prompt, username)
    except Exception as e:
        return f"[Error saat memanggil AI: {e}]"


@st.cache_data(ttl=3600)
def cached_ai_search_recipes(query, username, max_results=5, api_key_marker=None):
    try:
        return ai_search_recipes(query, username, max_results=max_results)
    except Exception as e:
        print(f"AI search error: {e}")
        return []


def create_nutrition_pie_chart(resep_data):
    """
    Membuat 2 pie chart nutrisi dari data resep.
    Chart 1: Komposisi nutrisi (Protein, Lemak, Karbohidrat) dalam gram
    Chart 2: Distribusi kalori dari masing-masing nutrisi
    """
    try:
        nutrition_data = resep_data.get('nutrition', {})
        nutrients = nutrition_data.get('nutrients', [])
        
        # Extract nutrisi utama
        protein = 0
        fat = 0
        carbs = 0
        
        for nutrient in nutrients:
            name = nutrient.get('name', '').lower()
            value = nutrient.get('amount', 0)
            
            if 'protein' in name:
                protein = round(value, 1)
            elif 'fat' in name and 'saturated' not in name:
                fat = round(value, 1)
            elif 'carbohydrates' in name:
                carbs = round(value, 1)
        
        # Jika ada data nutrisi
        if protein > 0 or fat > 0 or carbs > 0:
            # CHART 1: Komposisi Nutrisi (gram)
            labels_1 = ['Protein', 'Lemak', 'Karbohidrat']
            values_1 = [protein, fat, carbs]
            colors = ['#FF6B6B', '#FFA500', '#4ECDC4']
            
            fig1 = go.Figure(data=[go.Pie(
                labels=labels_1,
                values=values_1,
                marker=dict(colors=colors),
                textposition='inside',
                textinfo='label+value+percent',
                hovertemplate='<b>%{label}</b><br>%{value}g<br>%{percent}<extra></extra>'
            )])
            
            fig1.update_layout(
                title="Rincian Nutrisi per serving",
                height=400,
                showlegend=True
            )
            
            # CHART 2: Distribusi Kalori dari Nutrisi
            # Protein: 4 kcal/g, Fat: 9 kcal/g, Carbs: 4 kcal/g
            calories_protein = protein * 4
            calories_fat = fat * 9
            calories_carbs = carbs * 4
            
            labels_2 = ['Protein', 'Lemak', 'Karbohidrat']
            values_2 = [calories_protein, calories_fat, calories_carbs]
            
            # Filter out zero values untuk chart
            labels_2_filtered = [l for l, v in zip(labels_2, values_2) if v > 0]
            values_2_filtered = [v for v in values_2 if v > 0]
            colors_filtered = [c for l, c in zip(labels_2, colors) if l in labels_2_filtered]
            
            fig2 = go.Figure(data=[go.Pie(
                labels=labels_2_filtered,
                values=values_2_filtered,
                marker=dict(colors=colors_filtered),
                textposition='inside',
                textinfo='label+percent+value',
                hovertemplate='<b>%{label}</b><br>%{value:.0f} kcal<br>%{percent}<extra></extra>'
            )])
            
            fig2.update_layout(
                title="Distribusi Kalori dari Nutrisi",
                height=400,
                showlegend=True
            )
            
            return fig1, fig2, protein, fat, carbs
        else:
            return None, None, 0, 0, 0
    except Exception as e:
        print(f"Error creating nutrition chart: {e}")
        return None, None, 0, 0, 0

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
        
        # Tampilkan Pie Chart Nutrisi
        st.markdown("---")
        st.subheader("📊 Analisis Nutrisi")
        
        fig1, fig2, protein, fat, carbs = create_nutrition_pie_chart(detail_resep)
        if fig1 and fig2:
            # Tampilkan kedua chart side by side
            col_chart1, col_chart2 = st.columns(2)
            with col_chart1:
                st.plotly_chart(fig1, use_container_width=True)
            with col_chart2:
                st.plotly_chart(fig2, use_container_width=True)
            
            # Tampilkan statistik tambahan
            col_n1, col_n2, col_n3 = st.columns(3)
            with col_n1:
                st.metric("Protein", f"{protein}g")
            with col_n2:
                st.metric("Lemak", f"{fat}g")
            with col_n3:
                st.metric("Karbohidrat", f"{carbs}g")
        else:
            st.info("Data nutrisi tidak tersedia untuk resep ini.")
        
        st.markdown("---")
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
if 'hasil_pencarian_ai' not in st.session_state:
    st.session_state['hasil_pencarian_ai'] = None

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

        # TAB 4: AI (TANYA CHEF AI)
        with tab_ai:
            st.subheader("🤖 Tanya Chef AI")

            # Indikator singkat ketersediaan AI eksternal (debugging)
            try:
                ai_available = bool(ai_helper.HAS_GENAI and ai_helper.API_KEY)
            except Exception:
                ai_available = False
            st.caption(f"AI eksternal tersedia: {ai_available}")


            current_user = st.session_state.get('username')
            if not current_user:
                st.warning("Login diperlukan untuk menyimpan percakapan.")

            # -- AI Recipe Search UI --
            st.markdown("**Cari Resep dengan AI (masukkan bahan atau tipe masakan):**")
            ai_search_input = st.text_input("Contoh: ayam, tomat atau 'soto ayam'", key="ai_search_input")
            if st.button("Cari dengan AI", key="ai_search_btn", use_container_width=True):
                if not ai_search_input or not ai_search_input.strip():
                    st.warning("Masukkan bahan atau nama resep untuk dicari.")
                else:
                    with st.spinner("Chef AI sedang mencari resep..."):
                        try:
                            hasil_ai = cached_ai_search_recipes(ai_search_input.strip(), current_user, max_results=12, api_key_marker=ai_helper.API_KEY)
                            st.session_state['hasil_pencarian_ai'] = hasil_ai
                        except Exception as e:
                            st.error(f"Pencarian AI gagal: {e}")

            # Jika ada hasil pencarian AI, tampilkan dengan grid resep penuh (view, bookmark, PDF, history)
            if st.session_state.get('hasil_pencarian_ai'):
                st.markdown("---")
                st.subheader("🎯 Hasil Pencarian AI")
                if st.button("❌ Hapus hasil pencarian AI", key="clear_ai_search"):
                    st.session_state['hasil_pencarian_ai'] = None
                    st.rerun()
                tampilkan_grid_resep(st.session_state['hasil_pencarian_ai'], source="ai_search")

            col_left, col_right = st.columns([3, 1])
            with col_right:
                if st.button("🧹 Bersihkan Riwayat AI", use_container_width=True):
                    if clear_chat_history(current_user):
                        st.success("Riwayat obrolan AI dibersihkan.")
                        st.rerun()
                    else:
                        st.info("Tidak ada riwayat untuk dibersihkan.")

            # Tampilkan riwayat chat (terbaru di bawah)
            chat_history = get_chat_history(current_user)
            if chat_history:
                with st.expander("Riwayat Percakapan (terbaru 50)", expanded=True):
                    for msg in chat_history[-50:]:
                        role = msg.get('role', 'user')
                        text = msg.get('text', '')
                        ts = msg.get('timestamp', '')
                        if role == 'user':
                            st.markdown(f"**Kamu**  {text}")
                            if ts: st.caption(ts)
                        else:
                            st.markdown(f"**Chef AI**  {text}")
                            if ts: st.caption(ts)
            else:
                st.info("Belum ada percakapan. Tanyakan sesuatu kepada Chef AI!")

            st.markdown("---")
            st.subheader("Tanyakan kepada Chef AI")
            ai_input = st.text_area("Tulis pertanyaanmu di sini...", key="ai_input", height=140)
            send_col, _ = st.columns([1, 3])
            with send_col:
                if st.button("Kirim", key="ai_send", use_container_width=True):
                    if not ai_input or not ai_input.strip():
                        st.warning("Tulis pertanyaan dulu ya.")
                    else:
                        with st.spinner("Menghubungi Chef AI..."):
                            try:
                                answer = cached_tanya_chef_ai(ai_input.strip(), current_user, api_key_marker=ai_helper.API_KEY)
                                st.success("Chef AI sudah merespon — lihat riwayat di atas.")
                                # Tampilkan jawaban langsung
                                st.markdown("**Jawaban Chef AI:**")
                                st.markdown(answer)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Gagal memproses pertanyaan: {e}")
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
