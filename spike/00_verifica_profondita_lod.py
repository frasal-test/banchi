"""
SPIKE 00 — Verifica della profondita' del LOD della Camera per la XIX legislatura.

DOMANDA: partendo dall'atto Camera 3053 (XIX legislatura), il grafo LOD scende
davvero fino al singolo intervento del deputato in Aula?

La documentazione OCD descrive la catena
    atto -> assegnazione -> dibattito -> discussione -> intervento
ma si riferisce alla XVI legislatura. Che sia popolata allo stesso livello di
dettaglio per la XIX e' un'IPOTESI, non un fatto.

Questo script stampa il risultato GREZZO. Non interpreta, non normalizza, non
costruisce astrazioni. Codice usa e getta: non va promosso a src/.

Uso:
    python3 spike/00_verifica_profondita_lod.py
"""

import json
import ssl
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ENDPOINT = "https://dati.camera.it/sparql"
ATTO = "http://dati.camera.it/ocd/attocamera.rdf/ac19_3053"
TIMEOUT = 120


def contesto_ssl() -> ssl.SSLContext:
    """
    Su questa macchina la catena TLS verso dati.camera.it contiene un certificato
    presente nel keychain di sistema ma non nel bundle 'certifi' che Python usa
    di default: senza questo, ogni query fallisce con CERTIFICATE_VERIFY_FAILED
    mentre curl funziona. Si estraggono i root del sistema con /usr/bin/security.
    Niente dipendenze aggiuntive; su non-macOS si usa il default.
    """
    if sys.platform != "darwin":
        return ssl.create_default_context()
    pem = Path(tempfile.gettempdir()) / "banchi_system_roots.pem"
    if not pem.exists():
        out = subprocess.run(
            [
                "security", "find-certificate", "-a", "-p",
                "/Library/Keychains/System.keychain",
                "/System/Library/Keychains/SystemRootCertificates.keychain",
            ],
            capture_output=True, text=True, check=True,
        ).stdout
        pem.write_text(out)
    return ssl.create_default_context(cafile=str(pem))


CTX = contesto_ssl()

PREFIXES = """
PREFIX ocd:  <http://dati.camera.it/ocd/>
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dc:   <http://purl.org/dc/elements/1.1/>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
"""


def sparql(query: str) -> dict:
    """Esegue una query SPARQL. Solleva l'eccezione cosi' com'e' in caso di errore."""
    data = urllib.parse.urlencode({"query": PREFIXES + query}).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=data,
        headers={
            "Accept": "application/sparql-results+json",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "banchi-spike/0 (verifica profondita LOD; data journalism)",
        },
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT, context=CTX) as resp:
        return json.loads(resp.read().decode("utf-8"))


def esegui(titolo: str, ipotesi: str, query: str) -> None:
    """Esegue e stampa GREZZO. Nessuna interpretazione."""
    print("\n" + "=" * 78)
    print(f"[{titolo}]")
    print(f"ipotesi sotto test: {ipotesi}")
    print("-" * 78)
    print(query.strip())
    print("-" * 78)
    try:
        res = sparql(query)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:2000]
        print(f"HTTPError {e.code}\n{body}")
        return
    except Exception as e:  # noqa: BLE001 - spike: vogliamo vedere qualunque errore
        print(f"{type(e).__name__}: {e}")
        return

    righe = res.get("results", {}).get("bindings", [])
    print(f"RIGHE: {len(righe)}")
    if not righe:
        print("(nessun risultato)")
        return
    print(json.dumps(righe, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Le query. Ordine: prima si accerta che l'atto esista, poi si tenta la catena
# completa, poi — se la catena non regge — si guarda com'e' fatto il grafo.
# ---------------------------------------------------------------------------

QUERIES = [
    (
        "Q0 - l'atto esiste? triple uscenti",
        "l'URI ac19_3053 e' presente nel grafo",
        f"""
SELECT ?p ?o WHERE {{ <{ATTO}> ?p ?o }} LIMIT 200
""",
    ),
    (
        "Q1 - triple entranti sull'atto",
        "qualcosa nel grafo punta all'atto",
        f"""
SELECT ?s ?p WHERE {{ ?s ?p <{ATTO}> }} LIMIT 200
""",
    ),
    (
        "Q2 - catena come descritta dalla documentazione XVI legislatura",
        "atto -> assegnazione -> dibattito -> discussione -> intervento",
        f"""
SELECT ?assegnazione ?dibattito ?discussione ?intervento ?deputato WHERE {{
  ?assegnazione ocd:rif_attoCamera <{ATTO}> .
  ?dibattito    ocd:rif_assegnazione ?assegnazione .
  ?discussione  ocd:rif_dibattito ?dibattito .
  ?intervento   ocd:rif_discussione ?discussione .
  OPTIONAL {{ ?intervento ocd:rif_deputato ?deputato }}
}} LIMIT 100
""",
    ),
    (
        "Q3 - direzione degli archi verso un ocd:dibattito",
        "chi punta ai dibattiti e con quale predicato",
        """
SELECT ?tipo_soggetto ?p (COUNT(*) AS ?n) WHERE {
  ?s ?p ?o . ?o rdf:type ocd:dibattito . ?s rdf:type ?tipo_soggetto .
} GROUP BY ?tipo_soggetto ?p ORDER BY DESC(?n) LIMIT 20
""",
    ),
    (
        "Q4 - predicati uscenti da un ocd:dibattito qualsiasi",
        "il dibattito e' un nodo descritto o solo un URI referenziato",
        """
SELECT ?p (COUNT(*) AS ?n) WHERE {
  ?d rdf:type ocd:dibattito . ?d ?p ?o .
} GROUP BY ?p ORDER BY DESC(?n) LIMIT 25
""",
    ),
    (
        "Q5 - predicati uscenti da una ocd:discussione qualsiasi",
        "la discussione porta a interventi, seduta, data",
        """
SELECT ?p (COUNT(*) AS ?n) WHERE {
  ?d rdf:type ocd:discussione . ?d ?p ?o .
} GROUP BY ?p ORDER BY DESC(?n) LIMIT 25
""",
    ),
    (
        "Q6 - predicati uscenti da un ocd:intervento qualsiasi",
        "l'intervento porta al deputato e al testo/riferimento del resoconto",
        """
SELECT ?p (COUNT(*) AS ?n) WHERE {
  ?i rdf:type ocd:intervento . ?i ?p ?o .
} GROUP BY ?p ORDER BY DESC(?n) LIMIT 25
""",
    ),
    (
        "Q7 - CATENA REALE, come da ontologia OCD (classi.rdf)",
        "atto <- dibattito -> discussione -> intervento -> deputato, su TUTTA la XIX",
        """
SELECT (COUNT(DISTINCT ?dib) AS ?n_dibattiti) (COUNT(DISTINCT ?disc) AS ?n_discussioni)
       (COUNT(DISTINCT ?i) AS ?n_interventi) (COUNT(DISTINCT ?atto) AS ?n_atti) WHERE {
  ?dib rdf:type ocd:dibattito .
  ?dib ocd:rif_leg <http://dati.camera.it/ocd/legislatura.rdf/repubblica_19> .
  ?dib ocd:rif_attoCamera ?atto .
  ?dib ocd:rif_discussione ?disc .
  ?disc ocd:rif_intervento ?i .
}
""",
    ),
    (
        "Q8 - CATENA REALE applicata all'atto 3053",
        "l'atto 3053 ha interventi d'Aula nel LOD",
        f"""
SELECT ?dib ?disc ?i ?dep WHERE {{
  {{ ?dib ocd:rif_attoCamera <{ATTO}> }} UNION {{ <{ATTO}> ocd:rif_dibattito ?dib }}
  OPTIONAL {{ ?dib ocd:rif_discussione ?disc .
             OPTIONAL {{ ?disc ocd:rif_intervento ?i .
                        OPTIONAL {{ ?i ocd:rif_deputato ?dep }} }} }}
}} LIMIT 100
""",
    ),
    (
        "Q9 - atti XIX con piu' interventi d'Aula (catena reale)",
        "esistono atti XIX per cui la catena e' densamente popolata",
        """
SELECT ?atto ?titolo (COUNT(DISTINCT ?i) AS ?n_interventi) WHERE {
  ?dib rdf:type ocd:dibattito .
  ?dib ocd:rif_leg <http://dati.camera.it/ocd/legislatura.rdf/repubblica_19> .
  ?dib ocd:rif_attoCamera ?atto .
  ?dib ocd:rif_discussione ?disc .
  ?disc ocd:rif_intervento ?i .
  OPTIONAL { ?atto rdfs:label ?titolo }
} GROUP BY ?atto ?titolo ORDER BY DESC(?n_interventi) LIMIT 15
""",
    ),
    (
        "Q10 - campione di interventi di un atto XIX denso (ac19_1660)",
        "un intervento porta con se' deputato, titolo e riferimento al resoconto",
        """
SELECT ?disc ?data ?i ?dep ?titolo ?relazione WHERE {
  ?dib ocd:rif_attoCamera <http://dati.camera.it/ocd/attocamera.rdf/ac19_1660> .
  ?dib ocd:rif_discussione ?disc .
  ?disc ocd:rif_intervento ?i .
  OPTIONAL { ?disc dc:date ?data }
  OPTIONAL { ?i ocd:rif_deputato ?dep }
  OPTIONAL { ?i dc:title ?titolo }
  OPTIONAL { ?i dc:relation ?relazione }
} LIMIT 15
""",
    ),
    (
        "Q11 - latenza: intervento XIX piu' recente presente nel LOD",
        "quanto ritarda il LOD rispetto alla seduta",
        """
SELECT ?data (COUNT(DISTINCT ?i) AS ?n) WHERE {
  ?dib rdf:type ocd:dibattito .
  ?dib ocd:rif_leg <http://dati.camera.it/ocd/legislatura.rdf/repubblica_19> .
  ?dib ocd:rif_discussione ?disc .
  ?disc ocd:rif_intervento ?i .
  ?disc dc:date ?data .
} GROUP BY ?data ORDER BY DESC(?data) LIMIT 15
""",
    ),
    (
        "Q12 - stato d'iter dell'atto 3053 (perche' la catena e' vuota?)",
        "l'atto e' ancora in commissione e non e' mai arrivato in Aula",
        f"""
SELECT ?p ?o WHERE {{
  <{ATTO}> ocd:rif_assegnazione ?a . ?a ?p ?o .
}} LIMIT 50
""",
    ),
    (
        "Q13 - ATTENZIONE: rif_assemblea non distingue Aula da commissione",
        "l'unico discriminante e' la sezione dentro dc:relation dell'intervento",
        """
SELECT ?sezione (COUNT(DISTINCT ?i) AS ?n_interventi) (COUNT(DISTINCT ?disc) AS ?n_disc) WHERE {
  ?dib rdf:type ocd:dibattito .
  ?dib ocd:rif_leg <http://dati.camera.it/ocd/legislatura.rdf/repubblica_19> .
  ?dib ocd:rif_discussione ?disc .
  ?disc ocd:rif_intervento ?i .
  ?i dc:relation ?rel .
  BIND(IF(CONTAINS(STR(?rel), "sezione=assemblea"), "AULA (stenografico)",
       IF(CONTAINS(STR(?rel), "sezione=bollettini"), "COMMISSIONE (bollettino)",
          "altro")) AS ?sezione)
} GROUP BY ?sezione ORDER BY DESC(?n_interventi)
""",
    ),
    (
        "Q14 - perimetro reale del progetto: solo Aula E agganciato a un atto",
        "quanti atti XIX e quanti interventi restano dentro il perimetro dichiarato",
        """
SELECT (COUNT(DISTINCT ?atto) AS ?n_atti) (COUNT(DISTINCT ?i) AS ?n_interventi) WHERE {
  ?dib rdf:type ocd:dibattito .
  ?dib ocd:rif_leg <http://dati.camera.it/ocd/legislatura.rdf/repubblica_19> .
  ?dib ocd:rif_attoCamera ?atto .
  ?dib ocd:rif_discussione ?disc .
  ?disc ocd:rif_intervento ?i .
  ?i dc:relation ?rel .
  FILTER(CONTAINS(STR(?rel), "sezione=assemblea"))
}
""",
    ),
    (
        "Q15 - il ponte LOD -> testo: ancora dell'intervento nel resoconto",
        "dc:relation contiene l'id di ancoraggio del singolo intervento",
        """
SELECT ?i ?dep ?rel WHERE {
  ?dib ocd:rif_attoCamera <http://dati.camera.it/ocd/attocamera.rdf/ac19_705> .
  ?dib ocd:rif_discussione ?disc .
  ?disc ocd:rif_intervento ?i .
  ?i dc:relation ?rel .
  OPTIONAL { ?i ocd:rif_deputato ?dep }
  FILTER(CONTAINS(STR(?rel), "sezione=assemblea"))
} LIMIT 5
""",
    ),
]


def main() -> int:
    print("SPIKE 00 - profondita' LOD Camera, XIX legislatura")
    print(f"endpoint: {ENDPOINT}")
    print(f"atto:     {ATTO}")
    for titolo, ipotesi, query in QUERIES:
        esegui(titolo, ipotesi, query)
    print("\n" + "=" * 78)
    print("FINE. Nessuna interpretazione: leggere il grezzo qui sopra.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
