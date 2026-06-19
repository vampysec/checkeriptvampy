import requests
import sys
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

def is_url_valid(url, timeout=8):
    try:
        headers = {'User-Agent': 'VLC/3.0.20 LibVLC/3.0.20'}
        # Primer intento con HEAD
        response = requests.head(url, timeout=timeout, headers=headers, allow_redirects=True)
        if response.status_code in [200, 206, 302, 301]:
            return True
        # Segundo intento con GET pequeño
        response = requests.get(url, timeout=timeout, headers=headers, stream=True, allow_redirects=True)
        if response.status_code in [200, 206]:
            response.raw.read(1024)
            return True
        return False
    except:
        return False

def parse_m3u(content):
    channels = []
    lines = content.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('#EXTINF'):
            name_match = re.search(r',(.+)$', line)
            name = name_match.group(1).strip() if name_match else "Sin nombre"
            i += 1
            if i < len(lines):
                url = lines[i].strip()
                if url and not url.startswith('#'):
                    channels.append({"name": name, "url": url})
        i += 1
    return channels

def main():
    if len(sys.argv) < 2:
        print("Uso: python k.py <url_o_archivo.m3u>")
        print("Ejemplo: python k.py https://iptv-org.github.io/iptv/index.m3u")
        sys.exit(1)

    input_path = sys.argv[1]
    print(f"{BOLD}Cargando lista IPTV...{RESET}")

    # Cargar la lista
    if input_path.startswith(('http://', 'https://')):
        try:
            r = requests.get(input_path, timeout=25)
            r.raise_for_status()
            content = r.text
        except Exception as e:
            print(f"Error al descargar: {e}")
            sys.exit(1)
    else:
        with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

    channels = parse_m3u(content)
    print(f"{BOLD}Canales encontrados: {len(channels)}{RESET}\n")

    working = []
    with ThreadPoolExecutor(max_workers=25) as executor:
        future_to_ch = {executor.submit(is_url_valid, ch["url"]): ch for ch in channels}
        
        for future in as_completed(future_to_ch):
            ch = future_to_ch[future]
            try:
                if future.result():
                    print(f"{GREEN}✅ {ch['name']}{RESET}")
                    working.append(ch)
                else:
                    print(f"{RED}❌ {ch['name']}{RESET}")
            except:
                print(f"{RED}❌ {ch['name']}{RESET}")

    print("\n" + "="*60)
    print(f"{GREEN}✅ Canales que jalan: {len(working)} / {len(channels)}{RESET}")
    
    # Guardar lista buena
    with open("iptv_verde.m3u", 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        for ch in working:
            f.write(f'#EXTINF:-1,{ch["name"]}\n{ch["url"]}\n')
    
    print(f"{GREEN}Lista buena guardada como: iptv_verde.m3u{RESET}")

if __name__ == "__main__":
    main()