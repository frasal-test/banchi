"""Metadati LOD di un atto: interventi d'Aula e appartenenza ai gruppi.

Adattato da spike/01_estrai_un_provvedimento.py, che ha verificato la catena
atto -> dibattito -> discussione -> intervento per la XIX legislatura
(vedi docs/fonti.md).
"""

import re
from collections import defaultdict
from urllib.parse import urlparse, parse_qs

from banchi.sources._http import sparql

# dc:title sul gruppo porta il nome pieno con l'intervallo di date incollato
# (es. "MISTO (MISTO) (19.03.2013..."). dcterms:alternative è la sigla pulita
# (verificato 2026-09-03 ispezionando i predicati di un nodo gruppo).

LEG = "http://dati.camera.it/ocd/legislatura.rdf/repubblica_19"


def _ancora_e_seduta(rel: str) -> tuple[str, str] | tuple[None, None]:
    """Estrae (ancora, idSeduta) dall'URL in dc:relation dell'intervento."""
    qs = parse_qs(urlparse(rel).query)
    id_seduta = qs.get("idSeduta", [None])[0]
    ancora = qs.get("ancora", [None])[0]
    if not ancora:
        m = re.search(r"#(\S+)$", rel)
        ancora = m.group(1) if m else None
    if not ancora or not id_seduta:
        return None, None
    return ancora, id_seduta


def mappa_adesioni() -> dict[str, list[dict]]:
    """Appartenenza ai gruppi per deputato, per intervallo di date.

    Interrogazione indipendente da qualsiasi nodo `intervento`: è per
    persona, non per turno. Serve sia a `interventi_atto()` sia a risolvere
    il gruppo dei turni che il LOD non collega a nessun intervento (vedi
    `gruppo_per_data()` e docs/decisioni.md, 2026-09-04 — "Turni recuperati
    dal resoconto").
    """
    adesioni = sparql(f"""
PREFIX dcterms: <http://purl.org/dc/terms/>
SELECT DISTINCT ?dep ?gruppo ?sigla ?inizio ?fine WHERE {{
  ?dep rdf:type ocd:deputato .
  ?dep ocd:rif_leg <{LEG}> .
  ?dep ocd:aderisce ?ad .
  ?ad ocd:rif_gruppoParlamentare ?gruppo .
  ?ad ocd:startDate ?inizio .
  OPTIONAL {{ ?ad ocd:endDate ?fine }}
  OPTIONAL {{ ?gruppo dcterms:alternative ?sigla }}
}}
""")
    per_dep = defaultdict(list)
    for a in adesioni:
        per_dep[a["dep"]].append(a)
    return per_dep


def gruppo_per_data(per_dep: dict[str, list[dict]], dep: str | None,
                     data: str | None) -> tuple[str | None, str | None]:
    """Sigla e uri del gruppo a cui aderiva `dep` alla data `data`."""
    if not dep or not data:
        return None, None
    for a in per_dep.get(dep, []):
        fine = a.get("fine") or "99999999"
        if a["inizio"] <= data <= fine:
            return a.get("sigla"), a.get("gruppo")
    return None, None


def interventi_atto(numero: str) -> list[dict]:
    """Righe grezze (metadati LOD) degli interventi d'Aula di un atto Camera.

    Ogni riga ha: ancora, id_seduta, data, dep (uri), nome, gruppo_sigla,
    gruppo_uri.
    Non contiene il testo pronunciato: quello va preso dal resoconto
    stenografico della seduta (vedi resoconto_stenografico.py).
    """
    atto = f"http://dati.camera.it/ocd/attocamera.rdf/ac19_{numero}"

    interventi = sparql(f"""
SELECT DISTINCT ?disc ?data ?interv ?dep ?nome ?rel WHERE {{
  {{ ?dib ocd:rif_attoCamera <{atto}> }} UNION {{ <{atto}> ocd:rif_dibattito ?dib }}
  ?dib  ocd:rif_discussione ?disc .
  ?disc ocd:rif_intervento ?interv .
  ?interv dc:relation ?rel .
  FILTER(CONTAINS(STR(?rel), "sezione=assemblea"))
  OPTIONAL {{ ?disc dc:date ?data }}
  OPTIONAL {{ ?interv ocd:rif_deputato ?dep }}
  OPTIONAL {{ ?interv dc:title ?nome }}
}}
""")

    per_dep = mappa_adesioni()

    righe = []
    for i in interventi:
        ancora, id_seduta = _ancora_e_seduta(i.get("rel", ""))
        if not ancora:
            continue
        gruppo_sigla, gruppo_uri = gruppo_per_data(
            per_dep, i.get("dep"), i.get("data"))
        riga = {
            "ancora": ancora, "id_seduta": id_seduta,
            "data": i.get("data"), "dep": i.get("dep"), "nome": i.get("nome"),
            "gruppo_sigla": gruppo_sigla,
            "gruppo_uri": gruppo_uri,
        }
        righe.append(riga)
    return righe
