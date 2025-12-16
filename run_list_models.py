import os
import sys
from pathlib import Path

# Load .env manually if present
env_path = Path(__file__).with_name('.env')
if env_path.exists():
    for line in env_path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' in line:
            k, v = line.split('=', 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if k not in os.environ:
                os.environ[k] = v

GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')

if not GOOGLE_API_KEY:
    print('No GOOGLE_API_KEY found in environment or .env. Aborting.')
    sys.exit(2)

try:
    import google.generativeai as genai
except Exception as e:
    print('google-generativeai library is not installed or failed to import:')
    print(e)
    print('\nInstall it in your venv with:')
    print('  pip install google-generativeai')
    sys.exit(3)

# Try legacy configure -> list_models
try:
    # Some versions use genai.configure
    if hasattr(genai, 'configure'):
        genai.configure(api_key=GOOGLE_API_KEY)
        models = genai.list_models()
    else:
        # Newer versions may expose Client
        try:
            from google.generativeai import Client
            client = Client(api_key=GOOGLE_API_KEY)
            models = client.list_models()
        except Exception:
            # fallback to calling list_models on module
            models = genai.list_models()

    # Print models info
    if models is None:
        print('No models returned (None).')
        sys.exit(0)

    # models could be a dict with 'models' key or an iterable/generator
    if isinstance(models, dict) and 'models' in models:
        items = models['models']
    else:
        items = models

    # Ensure we can iterate over items and count safely
    try:
        # convert generators/iterables to list for safe printing
        items_list = list(items)
    except TypeError:
        items_list = [items]

    print(f"Found {len(items_list)} models:\n")
    for m in items_list:
        # m might be a dict or object
        mid = None
        methods = None
        try:
            if isinstance(m, dict):
                mid = m.get('name') or m.get('id') or m.get('model')
                methods = m.get('metadata', {}).get('supportedMethods') or m.get('capabilities') or m.get('supported_methods')
            else:
                # try attribute access
                mid = getattr(m, 'name', None) or getattr(m, 'id', None) or str(m)
                methods = getattr(m, 'supportedMethods', None) or getattr(m, 'capabilities', None) or getattr(m, 'supported_methods', None)
        except Exception:
            mid = str(m)

        print('-', mid)
        if methods:
            print('  supported methods:', methods)

except Exception as e:
    print('Error while calling list_models:')
    print(e)
    sys.exit(1)
