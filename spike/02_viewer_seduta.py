"""
SPIKE 02 — Viewer di un resoconto stenografico.

Serve a UNA cosa: capire com'e' strutturata una discussione in Aula, guardandola.
Non estrae, non misura, non giudica. Legge il file gia' in data/raw/ e produce
una pagina HTML navigabile.

Struttura del resoconto (osservata, vedi docs/decisioni.md):
    p.titolo             punto all'ordine del giorno
    p.sottotitolo        FASE procedurale (linee generali, repliche, fiducia...)
    p.presidenza         chi presiede
    p.avviso             sospensioni e riprese
    p.intervento         apre un turno di parola (porta il nome dell'oratore)
    p.interventoVirtuale continuazione dello stesso turno

Uso:
    python3 spike/02_viewer_seduta.py data/raw/sed0028_stenografico.raw
"""

import html
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Ordine FISSO dei gruppi: il colore segue il gruppo, non la sua frequenza,
# cosi' due sedute diverse restano confrontabili a colpo d'occhio.
GRUPPI = [
    ("FDI", "Fratelli d'Italia"),
    ("PD-IDP", "Partito Democratico"),
    ("M5S", "Movimento 5 Stelle"),
    ("LEGA", "Lega"),
    ("FI-PPE", "Forza Italia"),
    ("AVS", "Alleanza Verdi e Sinistra"),
    ("AZ-PER-RE", "Azione - Popolari Europeisti"),
    ("MISTO", "Misto"),
]
# Le sigle cambiano DENTRO la legislatura: nel dicembre 2022 il terzo polo
# era "A-IV-RE" (Azione-Italia Viva), poi diventato "AZ-PER-RE". Stesso slot
# di colore, altrimenti lo stesso gruppo cambia colore da una seduta all'altra.
ALIAS = {"A-IV-RE": "AZ-PER-RE", "IV-C-RE": "AZ-PER-RE",
         "NM(N-C-U-I)M-CP": "MISTO", "PD-IDP ": "PD-IDP"}
COLORI = ["--s1", "--s2", "--s3", "--s4", "--s5", "--s6", "--s7", "--s8"]
SLOT = {sigla: COLORI[i] for i, (sigla, _) in enumerate(GRUPPI)}
NOMI = dict(GRUPPI)


def testo(frammento: str) -> str:
    frammento = re.sub(r"<[^>]+>", " ", frammento)
    frammento = html.unescape(frammento)
    return re.sub(r"\s+", " ", frammento).strip()


def analizza(sorgente: str) -> tuple[list, dict]:
    """Scorre i <p> in ordine documentale e ricostruisce sezioni e turni."""
    sezioni: list[dict] = []
    corrente = {"tipo": "avvio", "titolo": "Apertura della seduta", "turni": []}
    presidente = ""

    pattern = re.compile(
        r'<p class="(titolo|sottotitolo|presidenza|avviso|intervento|interventoVirtuale)"'
        r'(?:\s+id="([^"]*)")?[^>]*>(.*?)</p>',
        re.S,
    )

    for m in pattern.finditer(sorgente):
        classe, ident, corpo = m.group(1), m.group(2) or "", m.group(3)
        piano = testo(corpo)
        if not piano:
            continue

        if classe in ("titolo", "sottotitolo"):
            if corrente["turni"] or corrente["tipo"] != "avvio":
                sezioni.append(corrente)
            corrente = {"tipo": classe, "titolo": piano, "turni": [],
                        "presidente": presidente}
            continue

        if classe == "presidenza":
            presidente = piano
            corrente.setdefault("presidente", presidente)
            continue

        if classe == "avviso":
            corrente["turni"].append({"tipo": "avviso", "testo": piano})
            continue

        if classe == "interventoVirtuale":
            for t in reversed(corrente["turni"]):
                if t["tipo"] == "turno":
                    t["paragrafi"].append(piano)
                    break
            else:
                corrente["turni"].append(
                    {"tipo": "turno", "id": ident, "oratore": "",
                     "persona": "", "gruppo": "", "ruolo": "",
                     "paragrafi": [piano]})
            continue

        # classe == "intervento": apre un turno.
        # Attenzione: il resoconto ha DUE nomi per lo stesso oratore.
        #   - l'etichetta dentro <a>...</a> e' come lo chiama l'Aula:
        #     "PRESIDENTE" quando presiede, altrimenti nome e cognome;
        #   - il title="Vai alla scheda personale: X" da' sempre l'anagrafico.
        # Chi presiede si riconosce dall'etichetta, non dall'anagrafico:
        # la stessa persona e' PRESIDENTE in una seduta e deputato in un'altra.
        oratore = etichetta = persona = gruppo = ruolo = ""
        a = re.search(
            r'<a[^>]*title="Vai alla scheda personale:\s*([^"]+)"[^>]*>(.*?)</a>',
            corpo, re.S)
        if a:
            oratore = html.unescape(a.group(1)).strip()
            etichetta = testo(a.group(2))
        p = re.search(r"idPersona=(\d+)", corpo)
        if p:
            persona = p.group(1)
        g = re.search(r"\(\s*<span[^>]*>([^<]{1,40})</span>\s*\)", corpo)
        if g:
            gruppo = html.unescape(g.group(1)).strip()
            gruppo = ALIAS.get(gruppo, gruppo)
        r = re.search(r"<em>([^<]{1,60})</em>", corpo)
        if r:
            ruolo = html.unescape(r.group(1)).strip()

        # Il testo pronunciato comincia dopo l'intestazione
        # "NOME (GRUPPO), Ruolo." — si taglia al primo punto che la chiude.
        piano = testo(corpo)
        if etichetta:
            taglio = re.match(
                re.escape(etichetta) + r"\s*(\([^)]*\))?\s*(,[^.]{0,60})?\s*\.\s*",
                piano)
            if taglio:
                piano = piano[taglio.end():]
            elif piano.startswith(etichetta):
                piano = piano[len(etichetta):].lstrip(" ,.")

        corrente["turni"].append({
            "tipo": "turno", "id": ident, "oratore": oratore or etichetta,
            "etichetta": etichetta, "persona": persona, "gruppo": gruppo,
            "ruolo": ruolo, "paragrafi": [piano],
        })

    sezioni.append(corrente)

    titolo_seduta = ""
    t = re.search(r"<title>(.*?)</title>", sorgente, re.S)
    if t:
        titolo_seduta = testo(t.group(1))

    for s in sezioni:
        for t in s["turni"]:
            if t["tipo"] == "turno":
                t["testo"] = " ".join(p for p in t["paragrafi"] if p).strip()
                t["n"] = len(t["testo"])
                t["presidenza"] = t.get("etichetta", "").upper().startswith("PRESIDENT")

    return sezioni, {"titolo": titolo_seduta}


def barra(turni: list) -> str:
    """Barra segmentata per gruppo: mostra CHI occupa la parola in una fase."""
    per_gruppo = Counter()
    for t in turni:
        if t["tipo"] != "turno" or not t["n"]:
            continue
        if t["presidenza"]:
            per_gruppo["PRESIDENZA"] += t["n"]
        else:
            per_gruppo[t["gruppo"] or "ALTRI"] += t["n"]
    tot = sum(per_gruppo.values())
    if not tot:
        return ""
    pezzi = []
    ordinati = sorted(per_gruppo.items(),
                      key=lambda kv: (kv[0] == "PRESIDENZA", kv[0] == "ALTRI",
                                      list(SLOT).index(kv[0]) if kv[0] in SLOT else 99))
    for sigla, n in ordinati:
        var = SLOT.get(sigla, "--neutro")
        quota = 100 * n / tot
        pezzi.append(
            f'<span class="seg" style="flex:{n};background:var({var})" '
            f'title="{html.escape(sigla)}: {n} caratteri ({quota:.0f}%)"></span>')
    return f'<div class="barra">{"".join(pezzi)}</div>'


def genera(sezioni: list, meta: dict, sorgente_file: str) -> str:
    tot_turni = sum(1 for s in sezioni for t in s["turni"] if t["tipo"] == "turno")
    tot_char = sum(t["n"] for s in sezioni for t in s["turni"] if t["tipo"] == "turno")
    gruppi_presenti = Counter()
    oratori = defaultdict(int)
    for s in sezioni:
        for t in s["turni"]:
            if t["tipo"] == "turno" and not t["presidenza"]:
                gruppi_presenti[t["gruppo"] or "ALTRI"] += t["n"]
                if t["oratore"]:
                    oratori[t["oratore"]] += t["n"]

    indice = []
    corpo = []
    for i, s in enumerate(sezioni):
        turni = [t for t in s["turni"] if t["tipo"] == "turno"]
        nchar = sum(t["n"] for t in turni)
        liv = "sub" if s["tipo"] == "sottotitolo" else "top"
        indice.append(
            f'<a class="voce {liv}" href="#sez{i}">'
            f'<span class="vt">{html.escape(s["titolo"][:80])}</span>'
            f'<span class="vn">{len(turni)}</span></a>')

        righe = []
        for t in s["turni"]:
            if t["tipo"] == "avviso":
                righe.append(f'<p class="avviso">{html.escape(t["testo"])}</p>')
                continue
            if not t["testo"]:
                continue
            cls = "turno pres" if t["presidenza"] else "turno"
            var = SLOT.get(t["gruppo"], "--neutro")
            sigla = t["gruppo"] or ("PRESIDENZA" if t["presidenza"] else "—")
            ruolo = f'<span class="ruolo">{html.escape(t["ruolo"])}</span>' if t["ruolo"] else ""
            righe.append(f"""
<article class="{cls}" data-gruppo="{html.escape(sigla)}" data-pres="{int(t['presidenza'])}" id="{html.escape(t['id'])}">
  <header>
    <span class="pallino" style="background:var({var})"></span>
    <span class="nome">{html.escape(t["oratore"] or "(non attribuito)")}</span>
    <span class="sigla">{html.escape(sigla)}</span>{ruolo}
    <span class="lung">{t["n"]:,} car.</span>
  </header>
  <div class="testo">{html.escape(t["testo"])}</div>
</article>""")

        corpo.append(f"""
<section id="sez{i}" class="sez {liv}">
  <h2>{html.escape(s["titolo"])}</h2>
  <div class="meta-sez">{len(turni)} turni · {nchar:,} caratteri</div>
  {barra(s["turni"])}
  {"".join(righe)}
</section>""")

    legenda = "".join(
        f'<span class="lg"><i style="background:var({SLOT.get(sig, "--neutro")})"></i>'
        f'{html.escape(NOMI.get(sig, sig))}</span>'
        for sig, _ in gruppi_presenti.most_common())

    top = "".join(
        f'<li><span>{html.escape(n)}</span><b>{c:,}</b></li>'
        for n, c in sorted(oratori.items(), key=lambda kv: -kv[1])[:12])

    return TEMPLATE.format(
        titolo=html.escape(meta.get("titolo", "Resoconto")),
        file=html.escape(sorgente_file),
        tot_turni=tot_turni, tot_char=f"{tot_char:,}",
        tot_sez=len(sezioni), tot_gruppi=len(gruppi_presenti),
        indice="".join(indice), corpo="".join(corpo),
        legenda=legenda, top=top)


TEMPLATE = """<!doctype html>
<html lang="it"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{titolo}</title>
<style>
:root {{
  color-scheme: light;
  --surface: #fcfcfb; --card: #ffffff; --bordo: #e4e3de;
  --ink: #0b0b0b; --ink2: #52514e; --ink3: #82817b;
  --s1:#2a78d6; --s2:#eb6834; --s3:#1baf7a; --s4:#eda100;
  --s5:#e87ba4; --s6:#008300; --s7:#4a3aa7; --s8:#9a6a2f;
  --neutro:#b8b7b0;
}}
@media (prefers-color-scheme: dark) {{
  :root:where(:not([data-theme="light"])) {{
    color-scheme: dark;
    --surface:#1a1a19; --card:#242423; --bordo:#3a3a38;
    --ink:#ffffff; --ink2:#c3c2b7; --ink3:#8d8c85;
    --s1:#3987e5; --s2:#d95926; --s3:#199e70; --s4:#c98500;
    --s5:#d55181; --s6:#008300; --s7:#9085e9; --s8:#a9793d;
    --neutro:#6b6a65;
  }}
}}
* {{ box-sizing:border-box }}
body {{ margin:0; background:var(--surface); color:var(--ink);
  font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; }}
.wrap {{ display:grid; grid-template-columns:300px 1fr; gap:0; min-height:100vh }}
aside {{ position:sticky; top:0; height:100vh; overflow-y:auto; padding:20px 16px;
  border-right:1px solid var(--bordo); background:var(--card) }}
main {{ padding:28px 34px; max-width:900px }}
h1 {{ font-size:20px; margin:0 0 4px; line-height:1.3 }}
.sub {{ color:var(--ink3); font-size:13px; margin-bottom:18px }}
.stat {{ display:flex; gap:18px; flex-wrap:wrap; margin:16px 0 22px;
  padding:14px 16px; background:var(--card); border:1px solid var(--bordo); border-radius:10px }}
.stat div b {{ display:block; font-size:22px; line-height:1.2 }}
.stat div span {{ font-size:12px; color:var(--ink3) }}
.voce {{ display:flex; justify-content:space-between; gap:8px; padding:6px 8px;
  border-radius:6px; text-decoration:none; color:var(--ink2); font-size:13px }}
.voce:hover {{ background:var(--surface) }}
.voce.sub {{ padding-left:20px; color:var(--ink3); font-size:12.5px }}
.voce .vn {{ color:var(--ink3); font-variant-numeric:tabular-nums; flex:none }}
.sez {{ margin:0 0 38px; scroll-margin-top:14px }}
.sez h2 {{ font-size:17px; margin:0 0 3px; padding-top:14px; border-top:1px solid var(--bordo) }}
.sez.sub h2 {{ font-size:15px; color:var(--ink2); border-top:none; padding-top:6px }}
.meta-sez {{ font-size:12px; color:var(--ink3); margin-bottom:10px }}
.barra {{ display:flex; gap:2px; height:10px; margin:0 0 18px; border-radius:5px; overflow:hidden }}
.seg {{ min-width:2px }}
.turno {{ background:var(--card); border:1px solid var(--bordo); border-radius:10px;
  padding:12px 14px; margin:0 0 10px }}
.turno.pres {{ background:transparent; border-style:dashed; opacity:.72 }}
.turno header {{ display:flex; align-items:center; gap:8px; flex-wrap:wrap; margin-bottom:7px }}
.pallino {{ width:9px; height:9px; border-radius:50%; flex:none }}
.nome {{ font-weight:600; font-size:14px }}
.sigla {{ font-size:11px; color:var(--ink2); border:1px solid var(--bordo);
  padding:1px 6px; border-radius:20px }}
.ruolo {{ font-size:11px; color:var(--ink3); font-style:italic }}
.lung {{ margin-left:auto; font-size:11px; color:var(--ink3); font-variant-numeric:tabular-nums }}
.testo {{ font-size:14.5px; color:var(--ink2); white-space:pre-wrap }}
.turno.pres .testo {{ font-size:13.5px }}
.avviso {{ font-size:13px; color:var(--ink3); font-style:italic; text-align:center;
  margin:14px 0; padding:6px }}
.filtri {{ display:flex; gap:14px; align-items:center; flex-wrap:wrap; margin:0 0 20px;
  padding:12px 14px; background:var(--card); border:1px solid var(--bordo); border-radius:10px }}
.filtri label {{ font-size:13px; color:var(--ink2); display:flex; align-items:center; gap:6px }}
.filtri input[type=search] {{ flex:1; min-width:160px; padding:6px 10px; font-size:13px;
  border:1px solid var(--bordo); border-radius:7px; background:var(--surface); color:var(--ink) }}
.legenda {{ display:flex; gap:12px; flex-wrap:wrap; font-size:12px; color:var(--ink2); margin:10px 0 0 }}
.lg {{ display:flex; align-items:center; gap:5px }}
.lg i {{ width:10px; height:10px; border-radius:2px; display:inline-block }}
.top {{ list-style:none; padding:0; margin:14px 0 0; font-size:12.5px }}
.top li {{ display:flex; justify-content:space-between; gap:10px; padding:3px 0;
  border-bottom:1px solid var(--bordo); color:var(--ink2) }}
.top b {{ font-variant-numeric:tabular-nums; color:var(--ink) }}
.nascosto {{ display:none !important }}
mark {{ background:var(--s4); color:#000 }}
@media (max-width:820px) {{ .wrap {{ grid-template-columns:1fr }}
  aside {{ position:static; height:auto }} main {{ padding:18px }} }}
</style></head><body>
<div class="wrap">
<aside>
  <h1>Struttura della seduta</h1>
  <div class="sub">{tot_sez} sezioni</div>
  {indice}
  <div class="sub" style="margin-top:22px">Chi ha parlato di più (caratteri)</div>
  <ul class="top">{top}</ul>
</aside>
<main>
  <h1>{titolo}</h1>
  <div class="sub">{file}</div>
  <div class="stat">
    <div><b>{tot_turni}</b><span>turni di parola</span></div>
    <div><b>{tot_char}</b><span>caratteri pronunciati</span></div>
    <div><b>{tot_sez}</b><span>sezioni</span></div>
    <div><b>{tot_gruppi}</b><span>gruppi in campo</span></div>
  </div>
  <div class="filtri">
    <label><input type="checkbox" id="fpres"> nascondi la presidenza</label>
    <label><input type="checkbox" id="fbrevi"> solo turni &gt; 800 caratteri</label>
    <input type="search" id="cerca" placeholder="cerca nel testo…">
  </div>
  <div class="legenda">{legenda}<span class="lg"><i style="background:var(--neutro)"></i>presidenza / non attribuito</span></div>
  {corpo}
</main>
</div>
<script>
const turni = [...document.querySelectorAll('.turno')];
const fpres = document.getElementById('fpres');
const fbrevi = document.getElementById('fbrevi');
const cerca = document.getElementById('cerca');
function applica() {{
  const q = cerca.value.trim().toLowerCase();
  turni.forEach(t => {{
    const testo = t.querySelector('.testo').textContent;
    let ok = true;
    if (fpres.checked && t.dataset.pres === '1') ok = false;
    if (fbrevi.checked && testo.length <= 800) ok = false;
    if (q && !testo.toLowerCase().includes(q)) ok = false;
    t.classList.toggle('nascosto', !ok);
  }});
  document.querySelectorAll('.sez').forEach(s => {{
    const vivi = s.querySelectorAll('.turno:not(.nascosto)').length;
    s.classList.toggle('nascosto', vivi === 0 && (q || fpres.checked || fbrevi.checked));
  }});
}}
[fpres, fbrevi].forEach(el => el.addEventListener('change', applica));
cerca.addEventListener('input', applica);
</script>
</body></html>"""


def main() -> int:
    sorgente = Path(sys.argv[1] if len(sys.argv) > 1
                    else "data/raw/sed0028_stenografico.raw")
    testo_sorgente = sorgente.read_text("utf-8", "replace")
    sezioni, meta = analizza(testo_sorgente)
    out = sorgente.with_suffix(".html")
    out.write_text(genera(sezioni, meta, sorgente.name), encoding="utf-8")

    tot = sum(1 for s in sezioni for t in s["turni"] if t["tipo"] == "turno")
    print(f"sezioni: {len(sezioni)}   turni: {tot}")
    print(f"viewer:  {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
