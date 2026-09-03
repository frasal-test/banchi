# Fonti

Tutte le fonti sono ufficiali Camera dei deputati. Nessuna fonte terza,
nessuno scraping.

---

## 1. dati.camera.it — Linked Open Data (struttura e iter)

| | |
|---|---|
| Endpoint SPARQL | `https://dati.camera.it/sparql` |
| Metodo | `POST` (o `GET`) con parametro `query`; header `Accept: application/sparql-results+json` |
| Licenza | CC-BY — attribuzione obbligatoria in ogni output pubblicato |
| Ontologia | OCD (Ontologia Camera dei deputati), namespace `http://dati.camera.it/ocd/` |

### Pattern URI

- Atto Camera: `http://dati.camera.it/ocd/attocamera.rdf/ac{legislatura}_{numero}`
  - esempio XIX legislatura, atto 3053: `http://dati.camera.it/ocd/attocamera.rdf/ac19_3053`
- Legislatura: `http://dati.camera.it/ocd/legislatura.rdf/repubblica_19`

### Documentazione ufficiale

- Pagina di documentazione: <https://dati.camera.it/ocd-rappresentazione-semantica-e-documentazione>
- Ontologia formale (classi e proprietà, dominio/range): <https://dati.camera.it/ocd/classi.rdf>
- Dataset scaricabili: <https://dati.camera.it/it/download>

La pagina di documentazione dichiara una copertura che si ferma alla XVII
legislatura per dibattiti e voti. **La dichiarazione è conservativa**: il
SPARQL endpoint è aggiornato quotidianamente e i dati XIX sono presenti
(verificato, vedi sotto). Non fidarsi della copertura dichiarata: si misura.

### Catena atto → intervento: VERIFICATA (2026-08-05)

La catena esiste per la XIX legislatura, ma **non passa da `assegnazione`**
come lascia intendere la documentazione riferita alla XVI. Struttura reale,
confermata sia empiricamente sia da `classi.rdf`:

```
atto  <──ocd:rif_attoCamera──  dibattito
                                   │ ocd:rif_discussione   (domain: dibattito)
                                   ▼
                              discussione
                                   │ ocd:rif_intervento    (domain: discussione)
                                   ▼
                               intervento
                                   │ ocd:rif_deputato
                                   ▼
                                deputato
```

Punti di attenzione, tutti verificati:

- **La direzione degli archi è dal dibattito verso il basso.** `dibattito` e
  `discussione` hanno gli archi uscenti; `intervento` è una foglia (7 soli
  predicati, nessun link di ritorno alla discussione).
- `ocd:rif_dibattito` ha dominio `assegnazione`/`richiestaParere`, ma nella
  pratica anche l'`atto` lo usa. Esiste quindi un secondo arco atto→dibattito.
- **`ocd:rif_assemblea` NON distingue l'Aula dalla commissione**: vale `a19`
  per tutti gli interventi della legislatura, commissioni incluse. L'unico
  discriminante affidabile è la sezione dentro `dc:relation` dell'intervento
  (`sezione=assemblea` = Aula, `sezione=bollettini` = commissione).
- **`dc:relation` dell'intervento è il ponte LOD → testo**: contiene l'URL del
  resoconto stenografico con l'**ancora del singolo intervento**, es.
  `...&idSeduta=0029&nomefile=stenografico&ancora=sed0029.stenografico.tit00110.sub00010.int01770`.
  Non serve ricostruire l'allineamento intervento↔testo: lo fornisce la Camera.
- `ocd:rif_leg` (non `rif_legislatura`) è il predicato della legislatura.
- **Le triple sono duplicate.** Ogni entità porta il proprio `rdf:type` due
  volte e i nodi collegati si moltiplicano. Usare sempre `SELECT DISTINCT` e
  `COUNT(DISTINCT ?x)`: senza, i conteggi escono raddoppiati e plausibili.
- **Le entità con durata sono già storicizzate**: il nodo `ocd:aderisce` che
  lega deputato e gruppo porta `ocd:startDate`, `ocd:endDate` e
  `ocd:motivoTermine`. Vale anche per incarichi, uffici di presidenza e
  composizione delle commissioni. Il gruppo va sempre attribuito **alla data
  dell'intervento**, mai "l'attuale".

### Cardinalità osservate (XIX legislatura, rilevate il 2026-08-05)

| Insieme | Valore |
|---|---|
| Triple totali nell'endpoint | 377.736.198 |
| Interventi (tutte le legislature) | 1.150.881 |
| Interventi XIX raggiungibili dalla catena | 126.645 |
| — di cui **Aula** (`sezione=assemblea`) | 64.089 (8.496 discussioni) |
| — di cui commissione (`sezione=bollettini`) | 62.551 (16.697 discussioni) |
| Interventi XIX agganciati a un atto Camera | 75.997 |
| **Perimetro del progetto: Aula + agganciati a un atto** | **39.000 interventi su 405 atti** |
| Ultima seduta con interventi nel LOD | 17 giugno 2026 |

Il resto degli interventi d'Aula non è agganciato a un atto Camera: sono
mozioni, question time, discussioni generali senza `rif_attoCamera`.

---

## 2. documenti.camera.it — Resoconti stenografici (testo degli interventi)

| | |
|---|---|
| Web service | `https://documenti.camera.it/apps/resoconto/elabora.asmx` |
| Formati | XML / XHTML |

### Vincolo di processo

Si analizza **solo il resoconto stenografico DEFINITIVO**. Se per una seduta
esiste solo il provvisorio, il provvedimento resta in coda e non si processa.
Il provvisorio può cambiare; il definitivo no.

### Cache

I resoconti di sedute chiuse **non cambiano mai**: si scaricano una volta
sola e si tengono in `data/raw/`. Nessun ri-download.

---

## 3. Dossier dei servizi studi (PDF)

PDF linkati dalla scheda dell'atto. Descrizione tecnica e neutrale del merito
del provvedimento, prodotta da funzionari parlamentari.

Uso previsto: **ancora indipendente** per valutare la pertinenza degli
argomenti emersi nel dibattito rispetto al contenuto reale del provvedimento.

**Non ancora in uso.** Annotato qui per non perderlo di vista.

---

## Vincoli trasversali

- **Mai scraping HTML di camera.it.** Il `robots.txt` vieta l'accesso
  automatico alle pagine. Si usano solo gli endpoint sopra, che sono pensati
  per il consumo automatico.
- **Mai ri-hosting di video WebTV.** La licenza non lo consente. Solo embed
  ufficiale, se e quando servirà.
- **Nessun ASR, nessuna trascrizione audio.** Solo testo ufficiale.
- **Perimetro: fase d'Aula alla Camera.** Il Senato ha open data separati ed è
  fuori portata. Va dichiarato esplicitamente in ogni output pubblicato.

## Attribuzione richiesta

Per i dati LOD (CC-BY), ogni output pubblicato deve citare:
*Fonte: dati.camera.it — Camera dei deputati, licenza CC-BY.*
