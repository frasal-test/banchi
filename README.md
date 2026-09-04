# Banchi

Analisi della struttura argomentativa del dibattito parlamentare italiano
(Camera dei deputati, XIX legislatura). Data journalism, non fact-checking.

L'unità di analisi è **il provvedimento**, mai il singolo deputato.

## La domanda

Dato un provvedimento, quali argomenti hanno messo sul tavolo i vari
schieramenti, con quali metodi retorici, e si sono davvero risposti a
vicenda o hanno fatto monologhi paralleli?

## Cosa non è

- **Non è un fact-checker.** Non giudica la veridicità di quello che viene
  detto in Aula — misura struttura e metodo del discorso, non il suo
  contenuto di verità.
- **Non produce classifiche, pagelle o punteggi di singoli deputati.**
- **L'output pubblicabile è sempre una distribuzione per gruppo
  parlamentare.** Il livello individuale resta interrogabile nel dato, mai
  nel titolo.

## Perimetro

Solo la fase d'Aula alla Camera dei deputati, XIX legislatura. Il Senato ha
open data separati e resta fuori portata — va dichiarato esplicitamente in
ogni output pubblicato.

## Fonti

Solo endpoint ufficiali della Camera, nessuno scraping HTML, nessun ASR:

- **Struttura e iter** — SPARQL endpoint `dati.camera.it` (ontologia OCD,
  licenza CC-BY)
- **Testo degli interventi** — resoconto stenografico ufficiale su
  `documenti.camera.it`

Dettaglio di endpoint, pattern URI, licenze e quirk osservati nel dato in
[docs/fonti.md](docs/fonti.md).

## Stato

- **`src/banchi/sources/`** — dato un atto Camera, restituisce lo sviluppo
  cronologico completo dei suoi interventi d'Aula attraverso tutte le
  sedute del suo iter, testo incluso.
- **`web/`** — un primo mockup pubblico: indice dei provvedimenti e, per
  ciascuno, distribuzione degli interventi per gruppo parlamentare e
  sviluppo cronologico integrale. Dati statici generati dalla pipeline
  (`scripts/genera_dati_web.py`), deployato su Vercel — non un backend live.

Cronologia completa delle scelte, con la motivazione, in
[docs/decisioni.md](docs/decisioni.md).

## Struttura del repo

```
src/banchi/     codice di produzione: sources/ (accesso alle fonti),
                model/ (modello dati), db/ (persistenza, non ancora in uso)
scripts/        collegamento pipeline -> output statico per web/
web/            frontend statico (dati JSON, nessun build step)
spike/          codice usa e getta per verificare ipotesi sui dati —
                mai promosso a src/
docs/           fonti.md (endpoint/licenze/quirk), decisioni.md (log delle
                scelte strutturali, con motivazione)
data/raw/       cache dei resoconti scaricati (in .gitignore)
```

## Sviluppare qui

Python, solo stdlib — nessuna dipendenza inutile.

```bash
python3 scripts/genera_dati_web.py            # rigenera i dati statici di web/
python3 -m http.server 5173 --directory web   # anteprima locale del frontend
```

Istruzioni complete per chi lavora su questo repo — vincoli non
negoziabili, convenzioni, stato dettagliato pezzo per pezzo — in
[CLAUDE.md](CLAUDE.md).

## Licenza

Codice sotto licenza MIT (vedi [LICENSE](LICENSE)). I dati Camera veicolati
sono CC-BY: ogni output pubblicato deve citare *"Fonte: dati.camera.it —
Camera dei deputati, licenza CC-BY"*.
