# Banchi

Analisi della struttura argomentativa del dibattito parlamentare italiano
(Camera dei deputati, XIX legislatura). Data journalism.

L'unità di analisi è **il provvedimento**, mai il singolo deputato.

Domanda di ricerca: dato un provvedimento, quali argomenti hanno messo sul
tavolo i vari schieramenti, con quali metodi retorici, e si sono davvero
risposti a vicenda o hanno fatto monologhi paralleli?

---

## Vincoli identitari (non negoziabili)

- **NON è un fact-checker.** Non si emettono MAI giudizi di verità su
  affermazioni fattuali. Si misurano struttura e metodo del discorso, non la
  sua veridicità.
- **NON produce classifiche, pagelle o punteggi di singoli deputati.**
- **L'output pubblicabile è sempre una DISTRIBUZIONE PER GRUPPO.** Il livello
  individuale resta interrogabile nel dato, mai nel titolo.

Se una feature richiesta viola uno di questi tre punti, va segnalata come
violazione identitaria prima di essere implementata.

## Vincoli tecnici e legali (non negoziabili)

- **MAI scraping HTML di camera.it**: il robots.txt vieta l'accesso
  automatico. Si usano solo gli endpoint ufficiali pensati per le macchine.
- **MAI ri-hosting di video WebTV**: la licenza non lo consente. Solo embed
  ufficiale, se e quando servirà.
- **Nessuna trascrizione audio, nessun ASR.** Solo testo ufficiale.
- **Il resoconto stenografico prelevato dal sito ufficiale si considera
  definitivo.** Nessuno degli endpoint ufficiali (SPARQL, `getDocumento.ashx`,
  `formato_xml`) espone un flag definitivo/provvisorio — verificato il
  2026-09-03, vedi [docs/decisioni.md](docs/decisioni.md). Non si mette in
  coda nulla in attesa di un segnale che la fonte non fornisce. Se in futuro
  emerge un modo affidabile per distinguerli, si rivede questa regola.
- **Perimetro dichiarato: fase d'Aula alla Camera.** Il Senato ha open data
  separati ed è fuori portata; va dichiarato esplicitamente nell'output.
- **Cache su disco obbligatoria** in `data/raw/` per tutto ciò che si scarica.
  I resoconti di sedute chiuse non cambiano mai: si scaricano una volta sola.

## Fonti

Dettaglio completo di endpoint, pattern URI e licenze in [docs/fonti.md](docs/fonti.md).

1. Struttura e iter — SPARQL endpoint `https://dati.camera.it/sparql`,
   ontologia OCD, licenza CC-BY.
2. Testo degli interventi — resoconto stenografico via
   `https://documenti.camera.it/apps/commonServices/getDocumento.ashx`.
3. Dossier dei servizi studi (PDF dalla scheda dell'atto) — ancora indipendente
   e neutrale sul merito del provvedimento. **Non ancora in uso.**

## Identificativi

Lo stesso provvedimento ha chiavi diverse in sistemi diversi.
Esempio reale: decreto-legge 12 giugno 2026 n. 100 = S. 1939 al Senato
= C. 3053 alla Camera.

**La chiave primaria è quella Camera; le altre sono alias.** Il modello dati
deve prevederlo fin dall'inizio: mai assumere una chiave sola.

## Stack

Python. Nessuna dipendenza inutile — se sta in stdlib, si usa stdlib.

In prospettiva, **non ora**: Oracle ADB su database dedicato (separato da
altri progetti) e annotazione via Anthropic API.

Riassunti dei turni: LLM locale (Ollama), non API cloud. Cache su disco in
`data/raw/riassunti/`, niente DB. Vedi
[docs/decisioni.md](docs/decisioni.md), 2026-09-04.

## Convenzioni di repo

- `spike/` — codice usa e getta per verificare ipotesi sui dati. **Mai
  promosso a `src/`.** Uno spike si legge, si impara qualcosa, e il codice
  buono si riscrive.
- `src/banchi/` — codice di produzione: `sources/` (accesso alle fonti),
  `model/` (modello dati), `db/` (persistenza).
- `docs/decisioni.md` — log delle scelte **con la motivazione**. Ogni scelta
  strutturale che non è ovvia va registrata lì.
- `data/raw/` — cache, in `.gitignore`. Mai committata.
- `web/` — frontend statico (mockup generato con Claude Design, dati JSON
  statici, nessun build step). Deployato su Vercel come progetto separato
  `banchi` (root directory `./web`, collegato al repo GitHub per deploy
  automatico ad ogni push su `main`, nessun dominio custom).
- `scripts/` — script di collegamento pipeline → output statico (es.
  `genera_dati_web.py`). Non `src/banchi/`: non è codice di libreria, è da
  rieseguire a mano quando cambia l'input o il formato a valle.

## Stato del progetto

La fase di sola verifica è chiusa (2026-08-05: la catena LOD è popolata per
la XIX, vedi `spike/00_verifica_profondita_lod.py`). Da qui si costruisce
incrementalmente dentro `src/banchi/`, nell'ordine **ingestione → modello →
pubblicazione**: ogni pezzo dipende dal precedente per avere dati veri su cui
lavorare. Se un pezzo si rivela sbagliato si butta e si riparte — non si
torna allo stadio spike-only per questo.

Primo pezzo scritto (2026-09-03): `src/banchi/sources/{camera_lod,
resoconto_stenografico,atto}.py` — dato un atto Camera, restituisce lo
sviluppo cronologico completo dei suoi interventi d'Aula attraverso tutte le
sedute del suo iter, testo incluso. Verificato su C. 2397. Nessuna
persistenza oltre la cache dei resoconti grezzi: i metadati LOD si rifanno da
SPARQL a ogni chiamata, da rivedere quando serve una home page che legge più
atti insieme.

Primo mockup di `pubblicazione` (2026-09-03): `web/`, generato con Claude
Design e deployato su Vercel (vedi sopra).

`web/` collegato ai dati veri per tutto il catalogo (2026-09-03):
`scripts/genera_dati_web.py` chiama la pipeline (`src/banchi/sources/atto.py`)
per ogni atto di `web/data/catalogo_atti.json` e scrive
`web/data/atto_<numero>_sviluppo.json`; il frontend fa fetch generico per
numero atto, non più cablato su un solo caso, con stato di
caricamento/mancante per atto e conteggio "sviluppo disponibile per N atti
su M" in home. Restano comunque dati statici committati (nessun backend): da
rigenerare a mano rieseguendo lo script quando il catalogo o
`src/banchi/sources/` cambiano. Vedi [docs/decisioni.md](docs/decisioni.md),
2026-09-03.

Bug di parsing corretto (2026-09-04): il campo `ruolo` in
`resoconto_stenografico.py` prendeva il primo `<em>` di **tutto** il corpo
dell'intervento invece che solo l'intestazione subito dopo `</a>`,
scambiando enfasi tipografica nel discorso (forestierismi, "96-bis", note
di regia come "Applausi") per il ruolo dell'oratore. Ora ancorato
correttamente. Dati rigenerati per tutti gli atti. Vedi
[docs/decisioni.md](docs/decisioni.md), 2026-09-04.

Tre link ufficiali Camera aggiunti a ogni turno di merito in `web/`
(2026-09-04): scheda del deputato, scheda del gruppo, paragrafo esatto nel
resoconto stenografico. Richiesto un nuovo campo `gruppo_uri` in
`Intervento`/`camera_lod.py` (il resto derivava da dati già presenti) e la
rigenerazione dei 16 JSON di `web/data/`. Dettagli e i pattern URL verificati
in [docs/decisioni.md](docs/decisioni.md), 2026-09-04.

**Nota nota e accettata, non un bug:** alcuni interventi compaiono due volte
di fila nello sviluppo cronologico. Verificato che è il dato ufficiale
stesso a duplicarli (due nodi `discussione` distinti nel grafo LOD puntano
allo stesso turno) — si è deciso di lasciarli così invece di deduplicare
arbitrariamente. Vedi [docs/decisioni.md](docs/decisioni.md), 2026-09-04, e
[docs/fonti.md](docs/fonti.md).

Testi "autorizzati in calce" separati dal corpus discusso (2026-09-04):
alcuni turni in coda al resoconto (dopo `<p class="titolo_allegato">`) sono
testi depositati da un deputato e mai pronunciati in Aula, ma
strutturalmente identici a un turno vero — venivano confusi col dibattito
vivo. Nuovo campo `pubblicato_in_calce` in `Intervento`/
`resoconto_stenografico.py`, propagato fino a `web/`: esclusi dalle
statistiche per gruppo, ma mostrati nello sviluppo cronologico in un box
distinto e marcato. Rigenerati i 16 JSON. Anche i turni di presidenza in
`web/` sono ora espandibili per intero ("Leggi tutto") invece di troncati a
140 caratteri sempre — restano esclusi dalle statistiche, cambia solo la
leggibilità. Dettagli in [docs/decisioni.md](docs/decisioni.md), 2026-09-04.

Turni recuperati dal resoconto (2026-09-04): alcuni turni pronunciati in
Aula non hanno nessun nodo `ocd:intervento` nel grafo LOD — non un
collegamento mancante verso un atto, un buco vero nel dato ufficiale
(verificato su C. 705, seduta 0028: il turno di Ciriani che pone la
questione di fiducia). `sviluppo_atto()` li recupera ora quando cadono nello
stesso blocco tit/sub del resoconto di un turno già confermato dal LOD per
quell'atto, usando `deputato_uri` ricostruito dall'idPersona nel resoconto
stesso (nuovo, in `resoconto_stenografico.py`) e il gruppo risolto per data
via `camera_lod.mappa_adesioni()` (nuova, indipendente dal nodo
`intervento`). Marcati `dedotto=True`: nella pipeline di produzione, quindi
vale per tutti gli atti, presenti e futuri, non solo per il 705. In `web/`
hanno lo stesso trattamento visivo di un turno confermato, con la sola
differenza di un'etichetta piccola e muta ("non confermato dal LOD") — sono
dibattito vero, non vanno percepiti come turni da poter saltare. Portata
misurata non trascurabile: il totale interventi per atto è più che
raddoppiato in diversi casi dopo la rigenerazione dei 16 JSON (C. 705:
1030 → 2042). Dettagli in [docs/decisioni.md](docs/decisioni.md), 2026-09-04.

Riassunti dei turni (design chiuso, implementazione non ancora iniziata,
2026-09-04): per i turni di merito ≥250 parole, un riassunto integrale
(200-300 parole, non un teaser) generato da LLM locale (Ollama) sarà sempre
visibile in `web/`, con il testo ufficiale sempre raggiungibile sotto via
toggle ("Leggi il testo integrale"); sotto soglia nessun riassunto e nessuna
UI aggiuntiva. Persistenza a cache su disco (`data/raw/riassunti/`, chiave
id turno + hash del testo), niente DB — coerente con "Oracle ADB in
prospettiva, non ora" (vedi Stack sopra). In attesa del nome del modello
Ollama prima di scrivere `scripts/genera_riassunti.py`. Primo test previsto
su C. 1114 per intero (343 interventi), non un sottoinsieme. Vedi
[docs/decisioni.md](docs/decisioni.md), 2026-09-04.
