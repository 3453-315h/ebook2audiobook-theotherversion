import os
import json
import urllib.request
import urllib.error
import hashlib

# Argos Translate Package Index URL
INDEX_URL = "https://raw.githubusercontent.com/argosopentech/argospm-index/main/index.json"
CACHE_DIR = "argos_cache"

def download_models():
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
        print(f"Created directory: {CACHE_DIR}")

    print("Fetching package index...")
    try:
        with urllib.request.urlopen(INDEX_URL) as response:
            data = json.loads(response.read().decode())
    except Exception as e:
        print(f"Error fetching index: {e}")
        return

    packages = data.get("packages", [])
    print(f"Found {len(packages)} total packages in index.")

    # Filter for English <-> X packages
    # Argos packages have 'from_code' and 'to_code'
    download_list = []
    
    # We want ANY package involving English (en)
    # The user said "offline language download... included them all"
    # Usually this means English to Others and Others to English.
    
    for pkg in packages:
        from_code = pkg.get("from_code")
        to_code = pkg.get("to_code")
        
        if from_code == "en" or to_code == "en":
            # Check links
            links = pkg.get("links", [])
            if not links:
                continue
            
            # Use the first link
            url = links[0]
            filename = os.path.basename(url)
            
            # Construct a target filename that describes the pair for clarity?
            # Actually, standard Argos filenames are like 'translate-en_es-1.0.argosmodel'
            # We should keep the original filename for simplicity, or use standard naming.
            # Let's trust the filename in the URL.
            
            download_list.append({
                "url": url,
                "filename": filename,
                "from": from_code,
                "to": to_code,
                "size_mb": 90 # Approximate default
            })

    print(f"Identified {len(download_list)} packages involving English.")
    print(f"Target directory: {os.path.abspath(CACHE_DIR)}")
    
    for i, item in enumerate(download_list):
        url = item["url"]
        filename = item["filename"]
        filepath = os.path.join(CACHE_DIR, filename)
        
        print(f"[{i+1}/{len(download_list)}] Checking {filename} ({item['from']}->{item['to']})...")
        
        if os.path.exists(filepath):
            print(f"  - Already exists. Skipping.")
            continue
            
        print(f"  - Downloading from {url}...")
        try:
            urllib.request.urlretrieve(url, filepath)
            print(f"  - Download complete.")
        except Exception as e:
            print(f"  - Failed to download: {e}")

    print("\nAll downloads processed.")
    print(f"Models are stored in '{CACHE_DIR}'.")
    print("These will be automatically installed when the Docker container starts if the volume is mapped.")

if __name__ == "__main__":
    print("Argos Offline Model Downloader")
    print("------------------------------")
    download_models()
