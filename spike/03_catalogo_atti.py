"""
SPIKE 03 — Catalogo degli atti della XIX con dibattito d'Aula nel LOD.

Serve a scegliere su cosa lavorare: elenca i provvedimenti che HANNO una fase
d'Aula documentata, con quanti turni, quante sedute, in che periodo.

Perimetro (vedi docs/decisioni.md):
  - solo Camera, fase d'Aula (sezione=assemblea dentro dc:relation)
  - solo atti agganciati a un dibattito via ocd:rif_attoCamera
Restano fuori mozioni, question time e discussioni senza atto collegato.

Uso:
    python3 spike/03_catalogo_atti.py
"""

import csv
import html
import json
import re
import ssl
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

ENDPOINT = "https://dati.camera.it/sparql"
LEG = "http://dati.camera.it/ocd/legislatura.rdf/repubblica_19"
RAW = Path(__file__).resolve().parent.parent / "data" / "raw"

PREFIXES = """
PREFIX ocd:  <http://dati.camera.it/ocd/>
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dc:   <http://purl.org/dc/elements/1.1/>
"""


def contesto_ssl() -> ssl.SSLContext:
    if sys.platform != "darwin":
        return ssl.create_default_context()
    pem = Path(tempfile.gettempdir()) / "banchi_system_roots.pem"
    if not pem.exists():
        pem.write_text(subprocess.run(
            ["security", "find-certificate", "-a", "-p",
             "/Library/Keychains/System.keychain",
             "/System/Library/Keychains/SystemRootCertificates.keychain"],
            capture_output=True, text=True, check=True).stdout)
    return ssl.create_default_context(cafile=str(pem))


CTX = contesto_ssl()


def sparql(query: str) -> list[dict]:
    data = urllib.parse.urlencode({"query": PREFIXES + query}).encode()
    req = urllib.request.Request(
        ENDPOINT, data=data,
        headers={"Accept": "application/sparql-results+json",
                 "User-Agent": "banchi-spike/0 (data journalism)"})
    with urllib.request.urlopen(req, timeout=600, context=CTX) as r:
        res = json.loads(r.read().decode())
    return [{k: v["value"] for k, v in b.items()}
            for b in res["results"]["bindings"]]


def pulisci(t: str) -> str:
    t = html.unescape(html.unescape(t or ""))
    t = re.sub(r"<[^>]+>", "", t)
    t = t.replace('\\"', '"').replace("\\'", "'")
    t = re.sub(r"\s+", " ", t).strip()
    # i label del LOD chiudono spesso con il numero d'atto: "…(3053)"
    t = re.sub(r"\s*\(\d+(-\w+)?\)\s*$", "", t)
    return t.strip(' "')


def data_it(g: str) -> str:
    return f"{g[6:8]}/{g[4:6]}/{g[0:4]}" if g and len(g) == 8 else g


def catalogo() -> list[dict]:
    volumi = sparql(f"""
SELECT ?atto (COUNT(DISTINCT ?i) AS ?n_int) (COUNT(DISTINCT ?disc) AS ?n_disc)
       (MIN(?data) AS ?dal) (MAX(?data) AS ?al) WHERE {{
  ?dib rdf:type ocd:dibattito .
  ?dib ocd:rif_leg <{LEG}> .
  ?dib ocd:rif_attoCamera ?atto .
  ?dib ocd:rif_discussione ?disc .
  ?disc ocd:rif_intervento ?i .
  ?disc dc:date ?data .
  ?i dc:relation ?rel .
  FILTER(CONTAINS(STR(?rel), "sezione=assemblea"))
}} GROUP BY ?atto ORDER BY DESC(?n_int)
""")

    schede = sparql(f"""
SELECT ?atto ?titolo ?natura ?iniziativa WHERE {{
  ?atto rdf:type ocd:atto .
  ?atto ocd:rif_leg <{LEG}> .
  OPTIONAL {{ ?atto rdfs:label ?titolo }}
  OPTIONAL {{ ?atto ocd:rif_natura ?natura }}
  OPTIONAL {{ ?atto ocd:iniziativa ?iniziativa }}
}}
""")
    per_uri = {s["atto"]: s for s in schede}

    out = []
    for v in volumi:
        s = per_uri.get(v["atto"], {})
        numero = v["atto"].rsplit("_", 1)[-1]
        titolo = pulisci(s.get("titolo", ""))
        # il label comincia con l'eventuale numero Senato: "S. 274. - ..."
        alias = ""
        m = re.match(r"^\s*(S\.\s*\d+[^.]*)\.", titolo)
        if m:
            alias = m.group(1).strip()
            titolo = titolo[m.end():].strip(" -")
        natura = s.get("natura", "").rsplit("/", 1)[-1].replace("_", " ")
        out.append({
            "numero_camera": numero,
            "alias_senato": alias,
            "titolo": titolo.strip('"'),
            "natura": natura,
            "iniziativa": s.get("iniziativa", ""),
            "interventi_aula": int(v["n_int"]),
            "discussioni": int(v["n_disc"]),
            "dal": v["dal"], "al": v["al"],
            "uri": v["atto"],
        })
    return out


def pagina(atti: list[dict]) -> str:
    righe = []
    for a in atti:
        titolo = a["titolo"] or "(senza titolo)"
        alias = f'<span class="alias">{html.escape(a["alias_senato"])}</span>' if a["alias_senato"] else ""
        righe.append(f"""<tr data-cerca="{html.escape((titolo + ' ' + a['numero_camera'] + ' ' + a['alias_senato']).lower())}">
  <td class="num">C. {html.escape(a["numero_camera"])}{alias}</td>
  <td class="tit">{html.escape(titolo[:190])}</td>
  <td class="n">{a["interventi_aula"]:,}</td>
  <td class="n">{a["discussioni"]}</td>
  <td class="d">{data_it(a["dal"])}<br><span class="al">{data_it(a["al"])}</span></td>
</tr>""")

    tot = sum(a["interventi_aula"] for a in atti)
    return f"""<!doctype html><html lang="it"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Atti XIX con dibattito d'Aula</title><style>
:root {{ color-scheme:light; --surface:#fcfcfb; --card:#fff; --bordo:#e4e3de;
  --ink:#0b0b0b; --ink2:#52514e; --ink3:#82817b; --acc:#2a78d6; }}
@media (prefers-color-scheme:dark) {{ :root:where(:not([data-theme=light])) {{
  color-scheme:dark; --surface:#1a1a19; --card:#242423; --bordo:#3a3a38;
  --ink:#fff; --ink2:#c3c2b7; --ink3:#8d8c85; --acc:#3987e5; }} }}
*{{box-sizing:border-box}}
body {{ margin:0; padding:28px; background:var(--surface); color:var(--ink);
  font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif }}
h1 {{ font-size:21px; margin:0 0 4px }}
.sub {{ color:var(--ink3); font-size:13px; margin-bottom:18px }}
.stat {{ display:flex; gap:20px; flex-wrap:wrap; margin:0 0 20px; padding:14px 16px;
  background:var(--card); border:1px solid var(--bordo); border-radius:10px }}
.stat b {{ display:block; font-size:21px }} .stat span {{ font-size:12px; color:var(--ink3) }}
input {{ width:100%; max-width:460px; padding:9px 12px; font-size:14px; margin-bottom:16px;
  border:1px solid var(--bordo); border-radius:8px; background:var(--card); color:var(--ink) }}
.tw {{ overflow-x:auto; border:1px solid var(--bordo); border-radius:10px; background:var(--card) }}
table {{ border-collapse:collapse; width:100%; min-width:760px }}
th {{ text-align:left; font-size:12px; color:var(--ink3); font-weight:600;
  padding:11px 12px; border-bottom:1px solid var(--bordo); position:sticky; top:0;
  background:var(--card); cursor:pointer; user-select:none }}
th:hover {{ color:var(--acc) }}
td {{ padding:9px 12px; border-bottom:1px solid var(--bordo); vertical-align:top }}
tr:last-child td {{ border-bottom:none }}
.num {{ font-weight:600; white-space:nowrap; font-size:13.5px }}
.alias {{ display:block; font-weight:400; font-size:11px; color:var(--ink3) }}
.tit {{ color:var(--ink2); font-size:13.5px; max-width:640px }}
.n {{ text-align:right; font-variant-numeric:tabular-nums; white-space:nowrap }}
.d {{ font-size:12px; color:var(--ink2); white-space:nowrap }}
.al {{ color:var(--ink3) }}
.via {{ display:none }}
footer {{ margin-top:18px; font-size:12px; color:var(--ink3) }}
</style></head><body>
<h1>Atti della XIX legislatura con dibattito d'Aula</h1>
<div class="sub">Camera dei deputati · solo fase d'Aula · il Senato è fuori perimetro</div>
<div class="stat">
  <div><b>{len(atti)}</b><span>provvedimenti</span></div>
  <div><b>{tot:,}</b><span>turni d'Aula</span></div>
  <div><b>{tot // max(1, len(atti)):,}</b><span>turni per atto (media)</span></div>
</div>
<input id="q" type="search" placeholder="cerca per numero o titolo…">
<div class="tw"><table><thead><tr>
<th data-c="0">Atto</th><th data-c="1">Titolo</th>
<th data-c="2" class="n">Turni</th><th data-c="3" class="n">Discussioni</th>
<th data-c="4">Periodo</th></tr></thead>
<tbody id="tb">{"".join(righe)}</tbody></table></div>
<footer>Fonte: dati.camera.it — Camera dei deputati, licenza CC-BY.</footer>
<script>
const tb=document.getElementById('tb'), q=document.getElementById('q');
q.addEventListener('input',()=>{{const v=q.value.trim().toLowerCase();
  [...tb.rows].forEach(r=>r.classList.toggle('via', v && !r.dataset.cerca.includes(v)));}});
let asc={{}};
document.querySelectorAll('th').forEach(th=>th.addEventListener('click',()=>{{
  const c=+th.dataset.c; asc[c]=!asc[c];
  const num=(c===2||c===3);
  [...tb.rows].sort((a,b)=>{{
    let x=a.cells[c].innerText.trim(), y=b.cells[c].innerText.trim();
    if(num){{x=+x.replace(/[^\\d]/g,'');y=+y.replace(/[^\\d]/g,'');return asc[c]?x-y:y-x;}}
    return asc[c]?x.localeCompare(y):y.localeCompare(x);
  }}).forEach(r=>tb.appendChild(r));
}}));
</script></body></html>"""


def main() -> int:
    print("interrogazione dell'endpoint…")
    atti = catalogo()
    RAW.mkdir(parents=True, exist_ok=True)

    (RAW / "catalogo_atti_xix.json").write_text(
        json.dumps(atti, indent=2, ensure_ascii=False), encoding="utf-8")
    with (RAW / "catalogo_atti_xix.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(atti[0].keys()))
        w.writeheader()
        w.writerows(atti)
    (RAW / "catalogo_atti_xix.html").write_text(pagina(atti), encoding="utf-8")

    tot = sum(a["interventi_aula"] for a in atti)
    print(f"\n{len(atti)} atti con fase d'Aula · {tot:,} turni totali\n")
    print(f"{'ATTO':<12} {'TURNI':>6} {'DISC':>5}  {'PERIODO':<23} TITOLO")
    print("-" * 108)
    for a in atti[:25]:
        per = f"{data_it(a['dal'])}–{data_it(a['al'])}"
        print(f"C. {a['numero_camera']:<9} {a['interventi_aula']:>6} "
              f"{a['discussioni']:>5}  {per:<23} {a['titolo'][:52]}")
    print(f"\nsalvati in data/raw/: catalogo_atti_xix.{{json,csv,html}}")
    print("Fonte: dati.camera.it — Camera dei deputati, licenza CC-BY.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
