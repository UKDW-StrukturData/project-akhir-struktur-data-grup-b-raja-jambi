import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Optional import for Google Gemini; jika tidak ada, kita fallback ke responder sederhana
try:
    import google.generativeai as genai
    HAS_GENAI = True
except Exception:
    genai = None
    HAS_GENAI = False

# Load environment
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

# Preferensi model — akan mencoba satu per satu hingga berhasil
# Diurutkan: flash models dulu (murah, quota tinggi), pro models terakhir (mahal, quota rendah)
PREFERRED_MODELS = [
    'models/gemini-flash-latest',      # ✓ Termurah, quota tinggi di free tier
    'models/gemini-2.5-flash',         # ✓ Flash cepat, quota tinggi
    'models/gemini-2.0-flash',         # Backup flash model
    'models/gemini-2.5-pro',           # Pro lebih powerful tapi quota rendah
    'models/gemini-3-pro-preview',     # Pro preview, minimal quota
]
# Storage untuk chat AI (per user)
DATA_FOLDER = os.path.join("data")
AI_CHAT_FILE = os.path.join(DATA_FOLDER, "ai_chats.json")

def ensure_data_exists():
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)
    if not os.path.exists(AI_CHAT_FILE):
        with open(AI_CHAT_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f)

def load_ai_chats():
    ensure_data_exists()
    try:
        with open(AI_CHAT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def save_ai_chats(data):
    ensure_data_exists()
    with open(AI_CHAT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_chat_message(username, role, text):
    """Simpan satu pesan chat ke history user."""
    if not username:
        return False
    data = load_ai_chats()
    if username not in data:
        data[username] = []
    entry = {
        "role": role,
        "text": text,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    data[username].append(entry)
    # Keep last 100 messages max
    data[username] = data[username][-100:]
    save_ai_chats(data)
    return True

def get_chat_history(username):
    data = load_ai_chats()
    return data.get(username, [])

def clear_chat_history(username):
    data = load_ai_chats()
    if username in data:
        data[username] = []
        save_ai_chats(data)
        return True
    return False

def tanya_chef_ai(pertanyaan, username="Pengguna"):
    """
    Mengirim pertanyaan ke Google Gemini (jika tersedia) dengan persona Chef.
    Jika API key / library tidak tersedia, gunakan fallback sederhana.
    """
    # Simpan pertanyaan user
    add_chat_message(username, 'user', pertanyaan)

    # Jika Gemini tersedia dan API key ada, coba beberapa model dan batasi output
    if HAS_GENAI and API_KEY:
        try:
            genai.configure(api_key=API_KEY)
        except Exception:
            # configure mungkin tidak tersedia pada beberapa versi, lanjutkan
            pass

        # fungsi bantu: coba generate dengan beberapa strategy dan model
        def _try_generate(prompt_text, max_output_tokens=250, temperature=0.2):
            for model_name in PREFERRED_MODELS:
                try:
                    # Strategy A: module-level helper (newer/older lib variations)
                    if hasattr(genai, 'generate_text'):
                        try:
                            resp = genai.generate_text(model=model_name, prompt=prompt_text, max_output_tokens=max_output_tokens, temperature=temperature)
                            # berbagai bentuk respons
                            if hasattr(resp, 'text') and resp.text:
                                return resp.text
                            if isinstance(resp, dict):
                                # try nested candidates/content
                                cand = resp.get('candidates')
                                if cand and isinstance(cand, list):
                                    c0 = cand[0]
                                    return c0.get('content') or c0.get('text') or str(c0)
                                return resp.get('output') or str(resp)
                        except Exception:
                            pass

                    # Strategy B: GenerativeModel object
                    if hasattr(genai, 'GenerativeModel'):
                        try:
                            model = genai.GenerativeModel(model_name)
                            # older API had generate_content
                            if hasattr(model, 'generate_content'):
                                r = model.generate_content(prompt_text)
                                if hasattr(r, 'text') and r.text:
                                    return r.text
                                # some responses expose candidates
                                if hasattr(r, 'candidates') and r.candidates:
                                    cand = r.candidates[0]
                                    return getattr(cand, 'content', None) or getattr(cand, 'text', None) or str(cand)
                        except Exception:
                            pass

                    # Strategy C: Client object (another variant)
                    try:
                        from google.generativeai import Client
                        client = Client(api_key=API_KEY)
                        if hasattr(client, 'generate'):
                            r = client.generate(model=model_name, prompt=prompt_text, max_output_tokens=max_output_tokens)
                            # try common fields
                            if isinstance(r, dict):
                                if 'candidates' in r and r['candidates']:
                                    return r['candidates'][0].get('content') or r['candidates'][0].get('text')
                                return r.get('output') or str(r)
                    except Exception:
                        pass

                except Exception:
                    # kalau model tidak ada atau error, coba model berikutnya
                    continue
            return None

        prompt_khusus = f"""
You are Chef AI, a helpful cooking assistant and nutrition guide. Answer in Indonesian in a friendly tone.
User: {pertanyaan}
"""
        try:
            ans = _try_generate(prompt_khusus, max_output_tokens=250)
            if ans:
                add_chat_message(username, 'assistant', ans)
                return ans
            else:
                raise RuntimeError('No model returned content')
        except Exception as e:
            fallback = f"Maaf, Chef AI sedang tidak dapat dihubungi (Error: {e}). Saya coba jawab singkat: \n{simple_fallback_answer(pertanyaan)}"
            add_chat_message(username, 'assistant', fallback)
            return fallback

    # Fallback sederhana (tanpa AI eksternal)
    answer = simple_fallback_answer(pertanyaan)
    add_chat_message(username, 'assistant', answer)
    return answer

def simple_fallback_answer(prompt):
    """Respon sederhana ketika tidak ada AI eksternal.
    Memberikan jawaban ringkas berdasarkan keyword makanan umum.
    """
    p = prompt.lower()
    if 'ganti' in p or 'substitu' in p:
        return "Jika ingin mengganti bahan, coba gunakan bahan yang memiliki tekstur/kelembaban serupa. Contoh: yogurt tawar untuk sour cream, pisang matang untuk telur pada kue." 
    if 'berapa kalori' in p or 'kalori' in p:
        return "Untuk estimasi kalori, periksa nilai kalori per porsi pada detail resep atau gunakan tabel nutrisi. Saya bisa bantu jika Anda beri bahan & jumlahnya." 
    if 'cara' in p or 'bagaimana' in p or 'langkah' in p:
        return "Coba jelaskan langkah utama: siapkan bahan, panaskan wajan/oven, masak sesuai instruksi hingga matang. Untuk detail, sebutkan bagian yang ingin diketahui." 
    return "Maaf, saya belum terhubung ke AI eksternal. Coba tanyakan hal spesifik tentang resep atau bahan, mis. 'Bagaimana mengganti telur dalam kue?'"


def ai_search_recipes(user_input, username=None, max_results=5):
    """Gunakan Google Gemini (jika tersedia) untuk mengubah input pengguna
    menjadi beberapa query pencarian resep, lalu panggil `cari_resep_spoonacular`
    sebagai fallback/eksekutor pencarian. Mengembalikan list max 5 resep terbaik (sorted by rating).
    """
    # Simpan query ke chat history
    if username:
        add_chat_message(username, 'user', f"Mencari resep: {user_input}")

    # Prepare candidate queries
    queries = []

    if HAS_GENAI and API_KEY:
        try:
            # prepare prompt for generating search queries
            gen_prompt = f"""
You are Chef AI. The user gave this input (in Indonesian): "{user_input}".
Return a JSON object with a key `queries` whose value is a list of up to 5 short search phrases (in Indonesian), optimized for recipe search (ingredients, dish types). Example: {"queries": ["chicken rice", "ayam kecap"]}
Only output the JSON object and nothing else.
"""

            # try same helper function as above but with smaller tokens
            def _try_generate_queries(prompt_text):
                for model_name in PREFERRED_MODELS:
                    try:
                        # Strategy: try module-level generate_text
                        if hasattr(genai, 'generate_text'):
                            try:
                                r = genai.generate_text(model=model_name, prompt=prompt_text, max_output_tokens=200)
                                if hasattr(r, 'text') and r.text:
                                    return r.text
                                if isinstance(r, dict) and 'candidates' in r and r['candidates']:
                                    return r['candidates'][0].get('content') or r['candidates'][0].get('text')
                            except Exception:
                                pass

                        if hasattr(genai, 'GenerativeModel'):
                            try:
                                model = genai.GenerativeModel(model_name)
                                if hasattr(model, 'generate_content'):
                                    rr = model.generate_content(prompt_text)
                                    if hasattr(rr, 'text') and rr.text:
                                        return rr.text
                                    if hasattr(rr, 'candidates') and rr.candidates:
                                        cand = rr.candidates[0]
                                        return getattr(cand, 'content', None) or getattr(cand, 'text', None)
                            except Exception:
                                pass

                    except Exception:
                        continue
                return None

            text = _try_generate_queries(gen_prompt) or ''
            # Try to parse JSON from response
            try:
                obj = json.loads(text)
                if isinstance(obj.get('queries'), list):
                    queries = obj.get('queries')[:5]
            except Exception:
                # fallback to simple split by lines
                lines = [l.strip('- ').strip() for l in text.splitlines() if l.strip()]
                if lines:
                    queries = lines[:5]
        except Exception:
            queries = []

    # If no queries from Gemini, use the raw input as single query
    if not queries:
        queries = [user_input]

    # Now execute searches (use spoonacular client if available)
    recipes = []
    try:
        from src.api_client import cari_resep_spoonacular
    except Exception:
        cari_resep_spoonacular = None

    for q in queries:
        if not q or len(recipes) >= (max_results * 3):  # Fetch more, then filter
            break
        # Convert query string to bahan list (split by comma or space)
        if ',' in q:
            bahan_list = [s.strip() for s in q.split(',') if s.strip()]
        else:
            bahan_list = [s.strip() for s in q.split() if s.strip()]

        if cari_resep_spoonacular:
            try:
                found = cari_resep_spoonacular(bahan_list, diet=None, tipe=None, max_kalori=10000)
                if found:
                    for r in found:
                        if len(recipes) >= (max_results * 3):
                            break
                        # avoid duplicates by id
                        if not any(rr.get('id') == r.get('id') for rr in recipes):
                            recipes.append(r)
            except Exception:
                pass

    # Sort by rating (descending) and take top max_results
    recipes.sort(key=lambda r: r.get('rating', 0), reverse=True)
    recipes = recipes[:max_results]

    # If still empty, return empty list
    if username:
        add_chat_message(username, 'assistant', f"Menemukan {len(recipes)} resep terkait untuk: {user_input}")
    return recipes
