import urllib.request
from pathlib import Path

urls = {
    "hit.mp3": "https://www.soundjay.com/buttons/sounds/button-3.mp3",
    "miss.mp3": "https://www.soundjay.com/buttons/sounds/button-10.mp3",
    "sink.mp3": "https://www.soundjay.com/buttons/sounds/button-09.mp3"
}

out_dir = Path("frontend/assets/sounds")
out_dir.mkdir(parents=True, exist_ok=True)

for name, url in urls.items():
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response:
            with open(out_dir / name, "wb") as f:
                f.write(response.read())
        print(f"Descargado {name}")
    except Exception as e:
        print(f"Error descargando {name}: {e}")
