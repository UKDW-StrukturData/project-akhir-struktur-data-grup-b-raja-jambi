import streamlit as st
from src.bookmark import add_bookmark
from src.pdf_utils import generate_pdf_bytes


def tampilkan_grid_resep_ai_summary(daftar_resep, source="ai"):
    """
    Menampilkan resep dari AI search dalam format yang lebih ringkas (1 kolom)
    dengan detail nutrisi: kalori, protein, lemak, carbs, harga estimasi.
    """
    if not daftar_resep:
        st.warning("Belum ada resep.")
        return
    
    current_user = st.session_state.get('username')
    
    for resep in daftar_resep:
        with st.container(border=True):
            col_img, col_info = st.columns([1, 2])
            
            # Kolom Gambar
            with col_img:
                if resep.get('image'):
                    st.image(resep['image'], use_container_width=True)
            
            # Kolom Info & Nutrisi
            with col_info:
                st.subheader(resep.get('title', 'Tanpa Judul'))
                
                # Extract nutrisi
                protein = fat = carbs = kalori = 0
                if 'nutrition' in resep and 'nutrients' in resep['nutrition']:
                    nutrients = resep['nutrition']['nutrients']
                    for nutrient in nutrients:
                        name = nutrient.get('name', '').lower()
                        value = nutrient.get('amount', 0)
                        if 'protein' in name:
                            protein = round(value, 1)
                        elif 'fat' in name and 'saturated' not in name:
                            fat = round(value, 1)
                        elif 'carbohydrates' in name:
                            carbs = round(value, 1)
                        elif 'calories' in name or 'energy' in name:
                            kalori = round(value, 1)
                
                # Estimasi harga (formula sederhana: kalori * 0.1 rupiah per kalori)
                harga_estimate = max(15000, kalori * 100)  # min 15k, atau kalori*100
                
                # Tampilkan ringkasan nutrisi
                st.markdown(f"""
**📊 Nutrisi (per serving):**
- 🔥 Kalori: **{kalori:.0f} kcal**
- 🥚 Protein: **{protein:.1f}g**
- 🧈 Lemak: **{fat:.1f}g**  
- 🌾 Karbohidrat: **{carbs:.1f}g**

**💰 Estimasi Harga: Rp {harga_estimate:,.0f}**
""")
                
                # Rating (jika ada)
                rating = resep.get('rating', 0)
                if rating:
                    st.caption(f"⭐ Rating: {rating:.1f}/5")
                
                # Tombol Aksi
                col_lihat, col_simpan, col_pdf = st.columns(3)
                
                with col_lihat:
                    key_lihat = f"det_{resep['id']}_{source}"
                    if st.button("👁️ Lihat", key=key_lihat, use_container_width=True):
                        st.session_state['view'] = 'detail'
                        st.session_state['selected_recipe_id'] = resep['id']
                        st.rerun()
                
                with col_simpan:
                    key_simpan = f"sav_{resep['id']}_{source}"
                    if st.button("❤️ Simpan", key=key_simpan, use_container_width=True):
                        if current_user:
                            if add_bookmark(current_user, resep['id']):
                                st.toast("Tersimpan!", icon="✅")
                            else:
                                st.toast("Sudah di favorit.", icon="ℹ️")
                        else:
                            st.error("Login dulu!")
                
                with col_pdf:
                    try:
                        pdf_data = generate_pdf_bytes(resep)
                        nama_file = resep['title'].replace(" ", "_").lower() + ".pdf"
                        st.download_button(label="📄 PDF", data=pdf_data, file_name=nama_file, 
                                         mime="application/pdf", use_container_width=True, key=f"pdf_{resep['id']}_{source}")
                    except Exception as e:
                        st.caption(f"PDF error")
