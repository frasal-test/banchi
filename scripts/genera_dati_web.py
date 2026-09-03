#!/usr/bin/env python3
"""Genera i JSON di sviluppo per web/, un atto alla volta.

Chiama la pipeline di produzione (src/banchi/sources/atto.py) e scrive
l'output nel formato statico che il frontend web/ si aspetta. Il taglio
orizzontale su un atto richiede una chiamata SPARQL più un download per
ogni seduta del suo iter (in cache su data/raw/, quindi rieseguibile senza
riscaricare nulla di già visto).

Uso:
    python scripts/genera_dati_web.py                # tutti gli atti del catalogo
    python scripts/genera_dati_web.py 705 1660        # solo questi numeri Camera
"""

import json
import re
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from banchi.sources.atto import sviluppo_atto  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CATALOGO = ROOT / "web" / "data" / "catalogo_atti.json"
OUT_DIR = ROOT / "web" / "data"


def _titolo_breve(titolo: str) -> str:
    t = re.sub(r"\s*\^\^http://www\.w3\.org/2001/XMLSchema#string\s*$", "", titolo).strip()
    t = t.split('"')[0].strip()
    m = re.search(r"\brecant[ei]\b", t, re.IGNORECASE)
    return (t[: m.start()] if m else t).rstrip(", ").strip()


def genera(numero_camera: str, titolo_catalogo: str) -> None:
    interventi = sviluppo_atto(numero_camera)
    sedute: list[str] = []
    for iv in interventi:
        if iv.id_seduta not in sedute:
            sedute.append(iv.id_seduta)
    payload = {
        "numero_camera": numero_camera,
        "titolo": _titolo_breve(titolo_catalogo),
        "sedute_coinvolte": sedute,
        "interventi": [asdict(iv) for iv in interventi],
    }
    dest = OUT_DIR / f"atto_{numero_camera}_sviluppo.json"
    dest.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{numero_camera}: {len(interventi)} interventi, {len(sedute)} sedute -> {dest.name}")


def _aggiorna_flag_disponibilita(catalogo: list[dict]) -> None:
    """Riscrive catalogo_atti.json con sviluppo_disponibile aggiornato in base
    ai file *_sviluppo.json presenti su disco — non solo quelli appena
    generati in questa esecuzione, così il flag resta corretto anche per
    run parziali (un sottoinsieme di numeri passato da riga di comando)."""
    disponibili = {
        p.name.removeprefix("atto_").removesuffix("_sviluppo.json")
        for p in OUT_DIR.glob("atto_*_sviluppo.json")
    }
    for a in catalogo:
        a["sviluppo_disponibile"] = a["numero_camera"] in disponibili
    CATALOGO.write_text(json.dumps(catalogo, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    catalogo = json.loads(CATALOGO.read_text("utf-8"))
    richiesti = set(sys.argv[1:]) or None
    for a in catalogo:
        numero = a["numero_camera"]
        if richiesti is not None and numero not in richiesti:
            continue
        genera(numero, a["titolo"])
    _aggiorna_flag_disponibilita(catalogo)


if __name__ == "__main__":
    main()
