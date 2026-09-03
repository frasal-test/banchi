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
2. Testo degli interventi — web service resoconti stenografici
   `https://documenti.camera.it/apps/resoconto/elabora.asmx`.
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

## Convenzioni di repo

- `spike/` — codice usa e getta per verificare ipotesi sui dati. **Mai
  promosso a `src/`.** Uno spike si legge, si impara qualcosa, e il codice
  buono si riscrive.
- `src/banchi/` — codice di produzione: `sources/` (accesso alle fonti),
  `model/` (modello dati), `db/` (persistenza).
- `docs/decisioni.md` — log delle scelte **con la motivazione**. Ogni scelta
  strutturale che non è ovvia va registrata lì.
- `data/raw/` — cache, in `.gitignore`. Mai committata.

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
