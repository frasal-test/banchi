"""Il taglio orizzontale: lo sviluppo completo di un atto in Aula.

Lega i metadati LOD (camera_lod.py, chi/quando/che gruppo) al testo
pronunciato (resoconto_stenografico.py, cosa) usando l'ancora del resoconto
come chiave — il ponte che dc:relation fornisce già (vedi docs/decisioni.md,
2026-08-05 — "Il ponte LOD -> testo è verificato end-to-end").
"""

from banchi.model.intervento import Intervento
from banchi.sources.camera_lod import gruppo_per_data, interventi_atto, mappa_adesioni
from banchi.sources.resoconto_stenografico import turni_seduta


def _blocco(ancora: str) -> str:
    """Il prefisso tit/sub di un'ancora, senza il numero d'intervento finale
    (es. sed0028.stenografico.tit00050.sub00050.int00020 ->
    sed0028.stenografico.tit00050.sub00050) — l'unità con cui si riconosce
    se un turno appartiene allo stesso blocco tematico di un altro."""
    parti = ancora.split(".")
    if parti[-1].startswith("int"):
        parti = parti[:-1]
    return ".".join(parti)


def sviluppo_atto(numero: str) -> list[Intervento]:
    """Tutti gli interventi d'Aula di un atto, testo incluso, in ordine
    cronologico attraverso le sedute del suo iter.

    Include anche i turni che il grafo LOD non collega a nessun nodo
    `intervento` (buco nel dato ufficiale, non nel nostro parsing — vedi
    docs/decisioni.md, 2026-09-04 — "Turni recuperati dal resoconto"),
    quando cadono nello stesso blocco tit/sub di un turno già confermato
    dal LOD per questo atto. Sono marcati `dedotto=True`: è un'inferenza
    nostra sulla struttura del documento, non un dato che Camera dichiara.
    """
    righe = interventi_atto(numero)
    per_dep = mappa_adesioni()

    per_seduta: dict[str, list[dict]] = {}
    for r in righe:
        per_seduta.setdefault(r["id_seduta"], []).append(r)

    interventi: list[tuple[tuple, Intervento]] = []
    for id_seduta, righe_seduta in per_seduta.items():
        turni = turni_seduta(id_seduta)
        ordine = {ancora: i for i, ancora in enumerate(turni)}
        data_seduta = righe_seduta[0].get("data") or ""
        confermate = {r["ancora"] for r in righe_seduta}
        blocchi_atto = {_blocco(a) for a in confermate}

        for r in righe_seduta:
            t = turni.get(r["ancora"])
            iv = Intervento(
                ancora=r["ancora"], id_seduta=id_seduta,
                data=r.get("data") or "", deputato_uri=r.get("dep"),
                deputato_nome=r.get("nome"), gruppo_sigla=r.get("gruppo_sigla"),
                gruppo_uri=r.get("gruppo_uri"),
            )
            if t:
                iv.oratore = t["oratore"]
                iv.ruolo = t["ruolo"]
                iv.presidenza = t["presidenza"]
                iv.pubblicato_in_calce = t["pubblicato_in_calce"]
                iv.testo = t["testo"]
                iv.trovato = True
            chiave = (iv.data, id_seduta, ordine.get(r["ancora"], 1 << 30))
            interventi.append((chiave, iv))

        for ancora, t in turni.items():
            if ancora in confermate or _blocco(ancora) not in blocchi_atto:
                continue
            gruppo_sigla, gruppo_uri = gruppo_per_data(
                per_dep, t["deputato_uri"], data_seduta)
            iv = Intervento(
                ancora=ancora, id_seduta=id_seduta, data=data_seduta,
                deputato_uri=t["deputato_uri"], deputato_nome=None,
                gruppo_sigla=gruppo_sigla, gruppo_uri=gruppo_uri,
                oratore=t["oratore"], ruolo=t["ruolo"],
                presidenza=t["presidenza"],
                pubblicato_in_calce=t["pubblicato_in_calce"],
                testo=t["testo"], trovato=True, dedotto=True,
            )
            chiave = (iv.data, id_seduta, ordine.get(ancora, 1 << 30))
            interventi.append((chiave, iv))

    interventi.sort(key=lambda coppia: coppia[0])
    return [iv for _, iv in interventi]
