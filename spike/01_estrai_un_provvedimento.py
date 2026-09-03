"""
SPIKE 01 — Estrazione di un provvedimento reale, per guardare il dato.

Dato un atto Camera della XIX legislatura, tira giu' dal LOD la fase d'Aula:
sedute, interventi, deputato, gruppo parlamentare ALLA DATA dell'intervento,
e il link al resoconto stenografico con l'ancora del singolo intervento.

Salva il grezzo in data/raw/ e stampa un riassunto AGGREGATO PER GRUPPO,
che e' l'unita' di pubblicazione del progetto.

Non e' un client. E' uno spike: si legge, si impara, si butta.

Uso:
    python3 spike/01_estrai_un_provvedimento.py [numero_atto]
    python3 spike/01_estrai_un_provvedimento.py 705
"""

import json
import ssl
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

ENDPOINT = "https://dati.camera.it/sparql"
LEG = "http://dati.camera.it/ocd/legislatura.rdf/repubblica_19"
RAW = Path(__file__).resolve().parent.parent / "data" / "raw"

PREFIXES = """
PREFIX ocd:  <http://dati.camera.it/ocd/>
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dc:   <http://purl.org/dc/elements/1.1/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
"""


def contesto_ssl() -> ssl.SSLContext:
    """Vedi spike/00: su macOS serve il truststore di sistema, non certifi."""
    if sys.platform != "darwin":
        return ssl.create_default_context()
    pem = Path(tempfile.gettempdir()) / "banchi_system_roots.pem"
    if not pem.exists():
        out = subprocess.run(
            ["security", "find-certificate", "-a", "-p",
             "/Library/Keychains/System.keychain",
             "/System/Library/Keychains/SystemRootCertificates.keychain"],
            capture_output=True, text=True, check=True,
        ).stdout
        pem.write_text(out)
    return ssl.create_default_context(cafile=str(pem))


CTX = contesto_ssl()


def sparql(query: str) -> list[dict]:
    data = urllib.parse.urlencode({"query": PREFIXES + query}).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT, data=data,
        headers={"Accept": "application/sparql-results+json",
                 "Content-Type": "application/x-www-form-urlencoded",
                 "User-Agent": "banchi-spike/0 (data journalism)"},
    )
    with urllib.request.urlopen(req, timeout=300, context=CTX) as resp:
        res = json.loads(resp.read().decode("utf-8"))
    return [{k: v["value"] for k, v in r.items()}
            for r in res["results"]["bindings"]]


def estrai(numero: str) -> dict:
    atto = f"http://dati.camera.it/ocd/attocamera.rdf/ac19_{numero}"

    testata = sparql(f"""
SELECT ?titolo ?iniziativa WHERE {{
  <{atto}> rdfs:label ?titolo .
  OPTIONAL {{ <{atto}> ocd:iniziativa ?iniziativa }}
}} LIMIT 1
""")

    # Il filtro d'Aula e' la sezione dentro dc:relation: rif_assemblea NON
    # distingue Aula da commissione (vedi docs/decisioni.md).
    # Interventi e adesioni ai gruppi si prendono con DUE query separate e si
    # uniscono in Python: annidare l'appartenenza al gruppo dentro OPTIONAL
    # multipli fa perdere silenziosamente il deputato (variabile fuori scope
    # nel FILTER). Meglio due query semplici che una fragile.
    interventi = sparql(f"""
SELECT ?disc ?data ?seduta ?interv ?dep ?nome ?rel WHERE {{
  {{ ?dib ocd:rif_attoCamera <{atto}> }} UNION {{ <{atto}> ocd:rif_dibattito ?dib }}
  ?dib  ocd:rif_discussione ?disc .
  ?disc ocd:rif_intervento ?interv .
  ?interv dc:relation ?rel .
  FILTER(CONTAINS(STR(?rel), "sezione=assemblea"))
  OPTIONAL {{ ?disc dc:date ?data }}
  OPTIONAL {{ ?disc ocd:rif_seduta ?seduta }}
  OPTIONAL {{ ?interv ocd:rif_deputato ?dep }}
  OPTIONAL {{ ?interv dc:title ?nome }}
}}
""")

    # Appartenenza ai gruppi con le date: 52 deputati della XIX hanno cambiato
    # gruppo, quindi il gruppo va attribuito ALLA DATA dell'intervento.
    adesioni = sparql(f"""
SELECT ?dep ?gruppo ?sigla ?inizio ?fine WHERE {{
  ?dep rdf:type ocd:deputato .
  ?dep ocd:rif_leg <{LEG}> .
  ?dep ocd:aderisce ?ad .
  ?ad ocd:rif_gruppoParlamentare ?gruppo .
  ?ad ocd:startDate ?inizio .
  OPTIONAL {{ ?ad ocd:endDate ?fine }}
  OPTIONAL {{ ?gruppo dc:title ?sigla }}
}}
""")

    per_dep = defaultdict(list)
    for a in adesioni:
        per_dep[a["dep"]].append(a)

    for i in interventi:
        dep, data = i.get("dep"), i.get("data")
        if not dep or not data:
            continue
        for a in per_dep.get(dep, []):
            fine = a.get("fine") or "99999999"
            if a["inizio"] <= data <= fine:
                i["gruppo"] = a["gruppo"]
                i["sigla"] = a.get("sigla", "")
                break

    return {
        "atto_uri": atto,
        "numero_camera": numero,
        "legislatura": 19,
        "perimetro": "fase d'Aula alla Camera; Senato escluso",
        "fonte": "dati.camera.it — Camera dei deputati, CC-BY",
        "testata": testata[0] if testata else {},
        "interventi": interventi,
    }


def riassumi(d: dict) -> None:
    inter = d["interventi"]
    print("=" * 74)
    print(f"ATTO C. {d['numero_camera']} — XIX legislatura")
    print(f"{d['testata'].get('titolo', '(senza titolo)')[:300]}")
    print("=" * 74)

    if not inter:
        print("\nNessun intervento d'Aula nel LOD per questo atto.")
        print("Puo' significare: non ancora arrivato in Aula, oppure")
        print("dibattito non ancora pubblicato nei dati. NON significa")
        print("'nessuno ha parlato'.")
        return

    per_id = {i["interv"]: i for i in inter}
    date = sorted({i["data"] for i in inter if i.get("data")})
    print(f"\ninterventi d'Aula : {len(per_id)}")
    print(f"sedute            : {len(date)}  ({date[0]} → {date[-1]})")
    print(f"deputati distinti : {len({i['dep'] for i in per_id.values() if i.get('dep')})}")

    senza_gruppo = sum(1 for i in per_id.values() if not i.get("sigla"))
    senza_dep = sum(1 for i in per_id.values() if not i.get("dep"))
    print(f"senza deputato    : {senza_dep}  (governo, presidenza)")
    print(f"senza gruppo      : {senza_gruppo}")

    print("\n--- DISTRIBUZIONE PER GRUPPO (unita' di pubblicazione) ---")
    per_gruppo = Counter()
    dep_per_gruppo = defaultdict(set)
    for i in per_id.values():
        sigla = i.get("sigla", "(non attribuito)").split("(")[0].strip()[:52]
        per_gruppo[sigla] += 1
        if i.get("dep"):
            dep_per_gruppo[sigla].add(i["dep"])
    tot = sum(per_gruppo.values())
    for sigla, n in per_gruppo.most_common():
        quota = 100 * n / tot
        barra = "█" * max(1, round(quota / 2))
        print(f"{sigla:<54} {n:>5}  {quota:>5.1f}%  {len(dep_per_gruppo[sigla]):>3}dep {barra}")

    print("\n--- SEDUTE ---")
    per_data = Counter(i.get("data", "?") for i in per_id.values())
    for data, n in sorted(per_data.items()):
        print(f"  {data}: {n} interventi")

    print("\n--- CAMPIONE (primi 5, grezzi) ---")
    for i in list(per_id.values())[:5]:
        print(f"\n  {i.get('nome', '(nessun deputato)')}")
        print(f"    gruppo alla data : {i.get('sigla', '—')}")
        print(f"    seduta           : {i.get('data', '—')}")
        print(f"    testo            : {i.get('rel', '—')}")


def main() -> int:
    numero = sys.argv[1] if len(sys.argv) > 1 else "705"
    print(f"estrazione atto C. {numero} ...\n")
    d = estrai(numero)

    RAW.mkdir(parents=True, exist_ok=True)
    out = RAW / f"ac19_{numero}_aula.json"
    out.write_text(json.dumps(d, indent=2, ensure_ascii=False))

    riassumi(d)
    print(f"\ngrezzo salvato in: {out.relative_to(Path.cwd()) if out.is_relative_to(Path.cwd()) else out}")
    print("Fonte: dati.camera.it — Camera dei deputati, licenza CC-BY.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
