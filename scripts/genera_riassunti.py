#!/usr/bin/env python3
"""Genera i riassunti dei turni via LLM locale (Ollama), un atto alla volta.

Cache su disco in data/raw/riassunti/, un file per turno (chiave: ancora +
hash del testo) — non chiama mai il modello due volte per lo stesso testo.
Non tocca web/data/: iniettare il campo nei JSON del sito è un passo
successivo, separato (vedi docs/decisioni.md, 2026-09-04).

Uso:
    python scripts/genera_riassunti.py 1114

Richiede un server Ollama raggiungibile su OLLAMA_HOST (default
http://localhost:11434) con il modello MODELLO già scaricato.
"""

import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB_DATA = ROOT / "web" / "data"
CACHE_DIR = ROOT / "data" / "raw" / "riassunti"

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
MODELLO = "gemma4:12b"
SOGLIA_PAROLE = 250

PROMPT_TEMPLATE = """Riassumi il seguente intervento parlamentare in 200-300 parole, in italiano.

Regole:
- Riporta il contenuto e la struttura argomentativa di chi parla: quali punti solleva, in che ordine, con quale tono retorico.
- Non esprimere giudizi di verità sulle affermazioni fattuali citate nell'intervento: non correggere, non validare, non commentare se sono vere o false.
- Non aggiungere opinioni o valutazioni tue.
- Scrivi in prosa continua, senza titoli né elenchi puntati.

Intervento:
\"\"\"
{testo}
\"\"\"
"""


def _hash_testo(testo: str) -> str:
    return hashlib.sha256(testo.encode("utf-8")).hexdigest()


def _chiama_ollama(testo: str) -> str:
    payload = {
        "model": MODELLO,
        "prompt": PROMPT_TEMPLATE.format(testo=testo),
        "stream": False,
    }
    req = urllib.request.Request(
        f"{OLLAMA_HOST}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        return json.loads(resp.read())["response"].strip()


def genera(numero_camera: str) -> None:
    sviluppo_path = WEB_DATA / f"atto_{numero_camera}_sviluppo.json"
    interventi = json.loads(sviluppo_path.read_text("utf-8"))["interventi"]

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    sopra_soglia = 0
    generati = 0
    riusati = 0
    falliti = 0

    for iv in interventi:
        testo = iv["testo"]
        n_parole = len(testo.split())
        if n_parole < SOGLIA_PAROLE:
            continue
        sopra_soglia += 1

        ancora = iv["ancora"]
        hash_testo = _hash_testo(testo)
        cache_path = CACHE_DIR / f"{ancora}.json"

        if cache_path.exists():
            cache = json.loads(cache_path.read_text("utf-8"))
            if cache.get("hash_testo") == hash_testo:
                riusati += 1
                continue

        print(f"  genero {ancora} ({n_parole} parole)...", flush=True)
        try:
            riassunto = _chiama_ollama(testo)
        except (urllib.error.URLError, TimeoutError, KeyError) as e:
            print(f"  FALLITO {ancora}: {e}", file=sys.stderr)
            falliti += 1
            continue

        cache_path.write_text(
            json.dumps(
                {
                    "ancora": ancora,
                    "hash_testo": hash_testo,
                    "modello": MODELLO,
                    "generato_il": datetime.now(timezone.utc).isoformat(),
                    "parole_originale": n_parole,
                    "riassunto": riassunto,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        generati += 1

    print(
        f"{numero_camera}: {len(interventi)} interventi, {sopra_soglia} sopra soglia "
        f"({SOGLIA_PAROLE} parole) -> {generati} generati, {riusati} già in cache, "
        f"{falliti} falliti"
    )


def main() -> None:
    if len(sys.argv) != 2:
        print("Uso: python scripts/genera_riassunti.py <numero_camera>", file=sys.stderr)
        sys.exit(1)
    genera(sys.argv[1])


if __name__ == "__main__":
    main()
