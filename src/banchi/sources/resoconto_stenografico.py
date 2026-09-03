"""Resoconto stenografico di una seduta: download in cache e parsing dei turni.

Il parsing è portato da spike/02_viewer_seduta.py, che ha verificato la
struttura del resoconto guardandola (vedi docs/decisioni.md, 2026-08-05 —
"Il rumore è la presidenza, non la brevità"). Qui non genera una pagina: for-
nisce i turni indicizzati per ancora, così sources/atto.py può agganciarci
i metadati LOD.

Cache: un resoconto di una seduta chiusa non cambia mai (o meglio: si
considera definitivo appena prelevato, vedi docs/decisioni.md 2026-09-03).
Si scarica una volta sola.
"""

import html
import re
from pathlib import Path

from banchi.sources._http import scarica

RAW = Path(__file__).resolve().parents[3] / "data" / "raw"

ASHX = (
    "https://documenti.camera.it/apps/commonServices/getDocumento.ashx"
    "?idlegislatura=19&sezione=assemblea&tipoDoc=stenografico"
    "&idSeduta={id_seduta}&nomefile=stenografico"
)


def _percorso_cache(id_seduta: str) -> Path:
    return RAW / f"sed{id_seduta}_stenografico.raw"


def scarica_seduta(id_seduta: str) -> Path:
    """Garantisce il resoconto in cache, scaricandolo solo se manca."""
    percorso = _percorso_cache(id_seduta)
    if not percorso.exists():
        RAW.mkdir(parents=True, exist_ok=True)
        contenuto = scarica(ASHX.format(id_seduta=id_seduta))
        percorso.write_text(contenuto, encoding="utf-8")
    return percorso


def _testo_piano(frammento: str) -> str:
    frammento = re.sub(r"<[^>]+>", " ", frammento)
    frammento = html.unescape(frammento)
    return re.sub(r"\s+", " ", frammento).strip()


_PATTERN_P = re.compile(
    r'<p class="(intervento|interventoVirtuale)"'
    r'(?:\s+id="([^"]*)")?[^>]*>(.*?)</p>',
    re.S,
)


def turni_seduta(id_seduta: str) -> dict[str, dict]:
    """Turni di parola della seduta, indicizzati per ancora.

    Ogni valore ha: oratore, gruppo, ruolo, presidenza, testo. Le continua-
    zioni (interventoVirtuale) sono già accorpate al turno che aprono.
    """
    sorgente = scarica_seduta(id_seduta).read_text("utf-8", "replace")

    turni: dict[str, dict] = {}
    ultimo_id: str | None = None

    for m in _PATTERN_P.finditer(sorgente):
        classe, ident, corpo = m.group(1), m.group(2) or "", m.group(3)
        piano = _testo_piano(corpo)
        if not piano:
            continue

        if classe == "interventoVirtuale":
            if ultimo_id and ultimo_id in turni:
                turni[ultimo_id]["paragrafi"].append(piano)
            continue

        # classe == "intervento": apre un turno. Vedi spike/02 per il
        # perché di questo parsing (due nomi per lo stesso oratore, la
        # presidenza si riconosce dall'etichetta non dall'anagrafico).
        oratore = etichetta = gruppo = ruolo = ""
        a = re.search(
            r'<a[^>]*title="Vai alla scheda personale:\s*([^"]+)"[^>]*>(.*?)</a>',
            corpo, re.S)
        if a:
            oratore = html.unescape(a.group(1)).strip()
            etichetta = _testo_piano(a.group(2))
        g = re.search(r"\(\s*<span[^>]*>([^<]{1,40})</span>\s*\)", corpo)
        if g:
            gruppo = html.unescape(g.group(1)).strip()
        r = re.search(r"<em>([^<]{1,60})</em>", corpo)
        if r:
            ruolo = html.unescape(r.group(1)).strip()

        if etichetta:
            taglio = re.match(
                re.escape(etichetta) + r"\s*(\([^)]*\))?\s*(,[^.]{0,60})?\s*\.\s*",
                piano)
            if taglio:
                piano = piano[taglio.end():]
            elif piano.startswith(etichetta):
                piano = piano[len(etichetta):].lstrip(" ,.")

        turni[ident] = {
            "oratore": oratore or etichetta, "gruppo": gruppo, "ruolo": ruolo,
            "presidenza": etichetta.upper().startswith("PRESIDENT"),
            "paragrafi": [piano],
        }
        ultimo_id = ident

    for t in turni.values():
        t["testo"] = " ".join(p for p in t["paragrafi"] if p).strip()
        del t["paragrafi"]

    return turni
