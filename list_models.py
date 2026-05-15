import urllib.request
import json
import os
import sys

def list_models():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not set.")
        return

    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            print("\n✅ Connection successful! Available models:\n")
            for model in data.get('models', []):
                name = model.get('name', '').replace('models/', '')
                display_name = model.get('displayName', 'Unknown')
                print(f"  - {name} ({display_name})")
    except Exception as e:
        print(f"❌ Error listing models: {e}")

if __name__ == "__main__":
    list_models()
