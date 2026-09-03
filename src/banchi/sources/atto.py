"""Il taglio orizzontale: lo sviluppo completo di un atto in Aula.

Lega i metadati LOD (camera_lod.py, chi/quando/che gruppo) al testo
pronunciato (resoconto_stenografico.py, cosa) usando l'ancora del resoconto
come chiave — il ponte che dc:relation fornisce già (vedi docs/decisioni.md,
2026-08-05 — "Il ponte LOD -> testo è verificato end-to-end").
"""

from banchi.model.intervento import Intervento
from banchi.sources.camera_lod import interventi_atto
from banchi.sources.resoconto_stenografico import turni_seduta


def sviluppo_atto(numero: str) -> list[Intervento]:
    """Tutti gli interventi d'Aula di un atto, testo incluso, in ordine
    cronologico attraverso le sedute del suo iter."""
    righe = interventi_atto(numero)

    per_seduta: dict[str, list[dict]] = {}
    for r in righe:
        per_seduta.setdefault(r["id_seduta"], []).append(r)

    interventi: list[tuple[tuple, Intervento]] = []
    for id_seduta, righe_seduta in per_seduta.items():
        turni = turni_seduta(id_seduta)
        ordine = {ancora: i for i, ancora in enumerate(turni)}

        for r in righe_seduta:
            t = turni.get(r["ancora"])
            iv = Intervento(
                ancora=r["ancora"], id_seduta=id_seduta,
                data=r.get("data") or "", deputato_uri=r.get("dep"),
                deputato_nome=r.get("nome"), gruppo_sigla=r.get("gruppo_sigla"),
            )
            if t:
                iv.oratore = t["oratore"]
                iv.ruolo = t["ruolo"]
                iv.presidenza = t["presidenza"]
                iv.testo = t["testo"]
                iv.trovato = True
            chiave = (iv.data, id_seduta, ordine.get(r["ancora"], 1 << 30))
            interventi.append((chiave, iv))

    interventi.sort(key=lambda coppia: coppia[0])
    return [iv for _, iv in interventi]
