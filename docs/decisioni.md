# Log delle decisioni

Ogni scelta strutturale non ovvia va registrata qui **con la motivazione**.
Formato: data, decisione, perché, cosa la renderebbe sbagliata.

---

## 2026-08-05 — La chiave primaria è quella Camera

**Decisione.** Nel modello dati il provvedimento è identificato dal numero
atto Camera; le chiavi Senato e le denominazioni ufficiali (decreto-legge,
data, numero) sono alias.

**Perché.** Lo stesso provvedimento ha chiavi diverse in sistemi diversi:
decreto-legge 12 giugno 2026 n. 100 = S. 1939 al Senato = C. 3053 alla Camera.
Il perimetro dichiarato del progetto è la fase d'Aula alla Camera, quindi la
chiave Camera è l'unica sempre presente.

**Cosa la renderebbe sbagliata.** Un'estensione al Senato: lì la chiave Camera
può mancare del tutto e servirebbe un identificativo neutro sopra entrambe.
Per questo gli alias esistono fin dall'inizio invece di essere aggiunti dopo.

---

## 2026-08-05 — Prima di scrivere codice si verifica la profondità del LOD

**Decisione.** Nessun client, modello dati, parser o codice DB prima di aver
visto il dato grezzo della catena atto → intervento per la XIX legislatura.

**Perché.** La documentazione OCD che descrive la catena
atto → assegnazione → dibattito → discussione → intervento si riferisce alla
XVI legislatura. Se la catena è popolata anche per la XIX, la struttura del
dibattito si legge dal LOD. Se non lo è, va ricostruita dal testo del
resoconto stenografico — progetto diverso, con costi e rischi diversi.
Scrivere astrazioni prima di sapere quale dei due mondi è quello reale
significa buttarle.

**Stato.** CHIUSA il 2026-08-05. La catena **è popolata** per la XIX, ma con
una topologia diversa da quella documentata per la XVI: non passa da
`assegnazione`, e la direzione degli archi è `dibattito → discussione →
intervento`. Dettaglio e cardinalità in [docs/fonti.md](fonti.md).
Decisione sulla forma del progetto: in attesa.

---

## 2026-08-05 — L'atto 3053 non è un caso di test valido

**Osservazione.** L'atto scelto per lo spike (C. 3053, decreto-legge 12 giugno
2026 n. 100) ha zero interventi nel LOD. Non perché il LOD sia incompleto: il
provvedimento è stato assegnato alla I Commissione **il 30 luglio 2026**, sei
giorni prima della rilevazione, e non è ancora arrivato in Aula. Gli 8
dibattiti collegati esistono come URI ma sono nodi vuoti, senza archi uscenti.

**Conseguenza.** Un URI di dibattito presente non implica che il dibattito
sia avvenuto. Il modello dati deve distinguere "dibattito previsto/annunciato"
da "dibattito con discussioni popolate", altrimenti un provvedimento in corso
d'iter appare identico a uno concluso senza interventi.

---

## 2026-08-05 — Il filtro Aula non si fa con rif_assemblea

**Decisione.** Per isolare la fase d'Aula si filtra sulla stringa
`sezione=assemblea` dentro `dc:relation` dell'intervento, non su
`ocd:rif_assemblea`.

**Perché.** `ocd:rif_assemblea` vale `a19` per tutti gli interventi della
legislatura, **commissioni incluse**: identifica la Camera nella XIX, non la
sede dei lavori. Usarlo come filtro d'Aula farebbe entrare nel perimetro
62.551 interventi di commissione, cioè metà del totale, violando in silenzio
il perimetro dichiarato del progetto.

**Cosa la renderebbe sbagliata.** Un cambio di formato negli URL di
`documenti.camera.it`: il filtro è basato su una stringa dentro un URL, non su
una proprietà semantica. Va trattato come euristica fragile e verificato a
ogni ingestione, non dato per acquisito.

---

## 2026-08-05 — L'allineamento intervento↔testo non va ricostruito

**Osservazione.** `dc:relation` dell'intervento contiene l'URL del resoconto
stenografico **con l'ancora del singolo intervento**
(`ancora=sed0029.stenografico.tit00110.sub00010.int01770`).

**Conseguenza.** Il problema più caro che ci si poteva aspettare — allineare
il record LOD di un intervento al suo testo nel resoconto — è già risolto
dalla fonte. Non serve fuzzy matching su nome del deputato e ordine di
intervento.

---

## 2026-08-05 — Il rumore è la presidenza, non la brevità

**Struttura del resoconto.** Un turno di parola è spezzato su più paragrafi:
`<p class="intervento">` apre il turno e porta il nome del deputato in link,
`<p class="interventoVirtuale">` ne è la **continuazione**. Nella seduta 0028:
120 turni, 574 paragrafi. Chi misura solo i `<p class="intervento">` misura
l'incipit del discorso, non il discorso.

**Osservazione (seduta 0028, turni ricomposti).** Mediana complessiva 199
caratteri, ma la distribuzione è nettamente bimodale:

| | turni | mediana |
|---|---|---|
| Presidenza | 66 (55%) | brevissimi |
| Deputati e governo | 54 (45%) | **3.796 caratteri** |

Solo il 26% dei turni non di presidenza sta sotto i 400 caratteri.

**Conseguenza.** L'unità argomentativa non va cercata con una soglia di
lunghezza: **basta escludere la presidenza**, che è metà dei turni ed è
identificabile dal ruolo, non da un'euristica. Tolta quella, i turni dei
deputati sono discorsi veri, con mediana di quasi 4.000 caratteri: materiale
adeguato a un'analisi della struttura argomentativa.

**Cosa la renderebbe sbagliata.** La misura viene da una sola seduta, per di
più anomala (seduta fiume ostruzionistica). Il rapporto presidenza/deputati
va rimisurato su sedute ordinarie prima di darlo per stabile.

---

## 2026-08-05 — Il numero di interventi è un indicatore di tattica, non di merito

**Osservazione.** Estratto l'atto C. 705 (DL 162/2022, ergastolo ostativo e
rave): 1.030 interventi d'Aula in 3 sedute, di cui **954 in un solo giorno** —
il 28 dicembre 2022. I titoli delle discussioni nel LOD dicono esplicitamente
*"seduta fiume"* e *"sui costi dell'utilizzo di azioni di tipo
ostruzionistico"*. La distribuzione per gruppo che ne risulta è PD 32,5% e M5S
29,3% contro FdI 4,3% e Lega 0,8%.

**Conseguenza.** Quella distribuzione **non dice** che l'opposizione abbia
argomentato otto volte più della maggioranza: dice che ha usato lo strumento
ostruzionistico. Pubblicare il conteggio grezzo come "chi ha portato più
argomenti" sarebbe una lettura falsa del dato, per quanto il dato sia esatto.
La forma d'Aula (seduta fiume, contingentamento dei tempi, dichiarazioni di
voto) va trattata come variabile di controllo, non come rumore.

---

## 2026-08-05 — Il ponte LOD → testo è verificato end-to-end

**Osservazione.** Scaricata la seduta 0028 dall'URL contenuto in `dc:relation`
(`getDocumento.ashx`, consentito dal robots.txt di `documenti.camera.it`, che
vieta solo `getAudioVideo.asp` e un file statico). L'ancora del LOD
`sed0028.stenografico.tit00030.sub00010.int00120` corrisponde esattamente a
`<p class="intervento" id="sed0028.stenografico.tit00030.sub00010.int00120">`
nel documento, e il markup contiene già nome del deputato, link alla scheda
personale e **sigla del gruppo inline** (`(FI-PPE)`).

**Conseguenza.** L'aggancio intervento↔testo è esatto e non probabilistico.
Inoltre il resoconto porta con sé una seconda attribuzione di gruppo,
indipendente da quella LOD: utile come controllo incrociato sui deputati che
hanno cambiato gruppo.

**Punto aperto.** Non è ancora accertato come distinguere il resoconto
**definitivo** dal provvisorio via `getDocumento.ashx`. Il vincolo di progetto
impone il definitivo: va risolto prima di qualunque ingestione sistematica,
probabilmente tramite il web service `elabora.asmx`.

---

## 2026-08-05 — Due tipi di cambiamento, due trattamenti diversi

**Distinzione.** Nel dato della Camera cambiano due cose che è facile confondere:

1. **Cambia il mondo** — un deputato passa da un gruppo all'altro, un ministro
   cambia incarico, una commissione si ricompone.
2. **Cambia il dato** — la Camera corregge un'attribuzione, aggiunge un
   intervento mancante, ritocca un record. Nel mondo non è successo nulla.

**Decisione.** Non si costruisce nessuna tabella di storicizzazione per il
caso 1: **è già storicizzato alla fonte**. L'appartenenza a un gruppo non è un
valore singolo ma un intervallo, con `ocd:startDate`, `ocd:endDate` e
`ocd:motivoTermine` sul nodo `ocd:aderisce`. Lo stesso vale per ogni entità
con durata (incarichi, uffici di presidenza, composizione delle commissioni):
l'ontologia OCD è costruita così. Una singola estrazione contiene già tutta la
sequenza storica, e permette di attribuire il gruppo **alla data
dell'intervento** senza tenere alcuno storico proprio.

Misura al 2026-08-05: su 414 deputati della XIX, 362 non hanno mai cambiato
gruppo, 37 una volta, 13 due volte, 2 tre volte — 52 mobili in totale.

**Per il caso 2 invece si versiona**, e la ragione è giornalistica prima che
tecnica: un pezzo pubblicato deve poter dire *"analisi sul dato al
5 agosto 2026"*. Senza, un conto non è rifacibile e un articolo non è
difendibile da una contestazione. Non serve una tabella dedicata: basta datare
ogni sincronizzazione e conservare la risposta grezza dell'endpoint. Alla
scala in gioco (~334 MB di testo per l'intera legislatura, più qualche decina
di MB di grafo) lo spazio non è un vincolo.

**Cosa la renderebbe sbagliata.** Se si scoprisse che la Camera **riscrive**
gli intervalli storici invece di chiuderli e aprirne di nuovi — cioè se una
rettifica cancellasse il passato invece di aggiungersi. Non osservato, ma non
escluso: da verificare confrontando due estrazioni a distanza di mesi.

---

## 2026-08-05 — Su questo endpoint, `DISTINCT` sempre

**Regola.** Ogni query SPARQL verso `dati.camera.it` usa `SELECT DISTINCT`, e
ogni aggregazione usa `COUNT(DISTINCT ?x)`. Un `COUNT` senza `DISTINCT` è da
considerarsi sbagliato finché non si dimostra il contrario.

**Perché.** Le triple del grafo sono duplicate: ogni entità porta il proprio
`rdf:type` due volte, e i nodi collegati si moltiplicano di conseguenza. Senza
`DISTINCT`, una query sui cambi di gruppo restituisce ogni adesione due volte
e porta a concludere che **tutti** i 414 deputati hanno cambiato gruppo,
invece di 52. L'errore non dà errore: dà un numero plausibile e sbagliato.

**Come accorgersene.** Se un conteggio viene esattamente doppio, o se ogni
entità sembra avere un numero pari di relazioni, è quasi sempre questo.

---

## 2026-08-05 — TLS: si usa il truststore di sistema

**Decisione.** Gli script usano i root certificate del keychain macOS estratti
con `/usr/bin/security`, non il bundle `certifi` di default di Python.

**Perché.** Su questa macchina la catena TLS verso `dati.camera.it` contiene un
certificato presente nel keychain ma non in `certifi`: senza questo accorgimento
ogni query fallisce con `CERTIFICATE_VERIFY_FAILED` mentre `curl` funziona,
il che rende il sintomo facile da attribuire erroneamente all'endpoint.
Nessuna verifica TLS è stata disabilitata.

---

## 2026-09-03 — Definitivo/provvisorio: si dà per definitivo ciò che si preleva

**Decisione.** Il vincolo originale ("solo resoconto DEFINITIVO, altrimenti
il provvedimento resta in coda") viene sostituito: il resoconto prelevato dal
sito ufficiale si considera definitivo, senza attesa né coda. Se in futuro
emerge un modo affidabile per distinguerli, si rivede la regola.

**Perché.** Verificati tre endpoint ufficiali sulla seduta 677 (17 giugno
2026, la più recente nel grafo LOD): il contratto WSDL di `elabora.asmx`
(parametro `tipo` = stenografico/sommario/allegato_a/allegato_b/sommario_new,
nessun valore relativo allo stato editoriale), l'HTML di `getDocumento.ashx`,
e la variante `formato_xml` (`<seduta>`, `<resoconto tipo="stenografico">`,
nessun attributo di stato). Nessuno dei tre espone un flag
definitivo/provvisorio. Le uniche occorrenze testuali di "provvisorio" e
"definitivo" trovate sono dentro i discorsi dei deputati, non nei metadati.
Mettere in coda un provvedimento in attesa di un segnale che la fonte non dà
significa non processare mai nulla, o farlo sulla base di un'euristica
temporale indimostrata.

**Osservazione emersa dalla verifica, utile ma non decisiva.** Il grafo LOD
(`dati.camera.it`) ha di suo un ritardo di mesi rispetto alla data corrente:
alla verifica, la seduta più recente raggiungibile da SPARQL era di circa due
mesi e mezzo prima. Qualunque intervento raggiungibile da lì è quindi con
ogni probabilità già editorialmente stabile per il solo fatto del ritardo. Il
problema provvisorio/definitivo, se esiste, riguarda le sedute più recenti
non ancora nel grafo — fuori perimetro dell'ingestione LOD-driven attuale, non
dentro.

**Cosa la renderebbe sbagliata.** Se si scoprisse un caso concreto di
resoconto raggiungibile da SPARQL il cui testo cambia tra due fetch a
distanza di tempo: significherebbe che il ritardo del grafo non basta a
garantire stabilità, e servirebbe allora un controllo attivo (es. hash del
contenuto su fetch ripetuti) prima di pubblicare.

---

## 2026-09-03 — `web/` è un mockup statico, scollegato dalla pipeline

**Decisione.** Il primo frontend pubblicabile (`web/`) è stato costruito in
una chat separata con Claude Design: un canvas `.dc.html` più `support.js`
(React/ReactDOM/Babel da CDN, nessun build step) che legge dati statici da
`web/data/*.json`. Deployato su Vercel (progetto `banchi`, root `./web`,
collegato a GitHub — push su `main` fa deploy automatico). Dettagli operativi
(URL, team, limite del connector Vercel) in memoria di progetto, non qui:
qui conta solo la scelta strutturale.

**Perché.** Serviva validare la direzione del layout — due schermate, home
indice e pagina-argomento con taglio orizzontale — prima di spendere tempo a
collegarlo alla pipeline reale. I dati d'esempio (`catalogo_atti_esempio.json`,
`atto_2397_sviluppo.json`) sono stati generati DA `src/banchi/sources/atto.py`
su un atto vero (C. 2397), non inventati: la forma è quella reale anche se il
sito non interroga nulla dal vivo.

**Cosa la renderebbe sbagliata, o comunque da rifare.** `web/` non ha
persistenza né backend: quando la pipeline avrà un output servibile (vedi la
nota "Nessuna persistenza oltre la cache" più sopra), `web/` va ricollegato a
dati veri o riscritto — è dichiaratamente un mockup, non l'inizio del sito
definitivo.

---

## 2026-09-03 — `dc:title` sul gruppo non è la sigla

**Osservazione.** `?gruppo dc:title ?sigla` restituisce il nome pieno del
gruppo con l'intervallo di date incollato in coda, es. `"FORZA ITALIA - IL
POPOLO DELLA LIBERTA' - BERLUSCONI PRESIDENTE (FI-PDL) (19.03.2013"`
(stringa troncata così dalla fonte, non da un parsing nostro). spike/01
copriva il sintomo tagliando alla prima parentesi — che però butta via anche
la sigla vera, lasciando solo il nome esteso.

**Correzione.** La sigla pulita è su un predicato diverso:
`dcterms:alternative` (`http://purl.org/dc/terms/alternative`), verificato
ispezionando tutti i predicati di un nodo `ocd:gruppoParlamentare`: dà
`"MISTO"`, `"FI-PPE"` ecc. senza post-processing.

**Cosa la renderebbe sbagliata.** Se un gruppo avesse più di un valore per
`dcterms:alternative` (sigla cambiata a parità di gruppo): non osservato, ma
la query in `camera_lod.py` prende il primo che trova — da verificare se mai
si nota una sigla sbagliata per un gruppo che sappiamo aver cambiato nome.

---

## 2026-09-03 — Fine della sola fase di verifica: primo codice in `src/`

**Decisione.** Scritto il primo modulo di produzione:
`src/banchi/sources/{camera_lod,resoconto_stenografico,atto}.py` e
`src/banchi/model/intervento.py`. Realizzano il taglio orizzontale su un
atto — dalla richiesta dell'utente di una pagina per argomento che segua un
provvedimento attraverso tutte le sue sedute, non seduta per seduta.

**Verificato su un caso reale.** Atto C. 2397 (decreto-legge 54/2025): 22
interventi su 2 sedute (0479, 0490), tutti agganciati al testo del resoconto
(0 mancanti), ordine cronologico corretto attraverso le sedute, gruppo
attribuito alla data e sigla pulita.

**Perché ora e non prima.** La voce "Stato del progetto" in CLAUDE.md
vietava client/modello/DB finché la profondità del LOD non fosse verificata:
lo è, dal 5 agosto. Da qui in avanti si costruisce incrementalmente dentro
`src/banchi/`, nell'ordine ingestione → modello → pubblicazione (deciso in
conversazione, non ancora qui prima d'ora). Se un pezzo si rivela sbagliato
si butta e si riparte, senza tornare allo stadio spike-only.

**Nota.** Non c'è ancora persistenza oltre la cache dei resoconti grezzi in
`data/raw/` (nessun DB, nessun modello per Atto/Seduta/Gruppo): i metadati
LOD si rifanno da SPARQL a ogni chiamata. Da rivedere quando si costruisce la
home page, che ha bisogno di leggere più atti senza interrogare l'endpoint
ogni volta.

---

## 2026-08-05 — Solo stdlib per gli spike

**Decisione.** Lo spike di verifica usa `urllib` dalla stdlib, non `requests`.

**Perché.** "Nessuna dipendenza inutile". Uno spike che serve a fare due
POST HTTP non giustifica una dipendenza, e non deve costringere chi lo
rilegge a installare qualcosa per eseguirlo.

---

## 2026-09-03 — `web/` collegato ai dati veri per tutto il catalogo

**Decisione.** Aggiunto `scripts/genera_dati_web.py`: chiama
`sviluppo_atto()` (src/banchi/sources/atto.py) per ogni atto di
`web/data/catalogo_atti.json` e scrive `web/data/atto_<numero>_sviluppo.json`
nello stesso formato usato finora solo per C. 2397. Il frontend
(`web/index.html`) non ha più il numero 2397 cablato: `selectAtto` fa fetch
generico su `data/atto_${numero}_sviluppo.json` con uno stato di
caricamento/mancante per atto, così la pagina di un provvedimento senza
dati generati resta un fallback esplicito invece di un errore silenzioso.

**Verificato.** 16/16 atti del catalogo generati, 8497 interventi totali,
0 mancanti (100% di aggancio testo-metadati, stesso controllo già fatto per
C. 2397 il 2026-09-03 in precedenza). Verificato a occhio nel browser su
C. 705, C. 1114 e C. 2397: nessun errore in console.

**Perché ora.** CLAUDE.md segnalava esplicitamente `web/` come "ancora
scollegato dalla pipeline dati reale" e la nota da rivedere "quando la
pipeline avrà un output servibile" — lo è, da qui i tre moduli di
`src/banchi/sources/` scritti in precedenza oggi stesso.

**Nota.** `scripts/genera_dati_web.py` è uno script di collegamento
(pipeline -> file statici), non fa parte di `src/banchi/`: va rieseguito a
mano quando il catalogo cambia o quando `src/banchi/sources/` cambia
formato. Non è automatizzato (nessun cron, nessun hook di build) — scelta
deliberata finché `web/` resta un mockup statico su Vercel senza backend.

**Cosa la renderebbe sbagliata.** Se il catalogo cresce molto (centinaia di
atti), 16 file JSON da 0.7-2 MB l'uno committati in `web/data/` (~14 MB
totali oggi) diventa un problema di dimensione del repo prima che di
tempo di generazione — a quel punto serve un backend che serva i dati a
richiesta invece di file statici pre-generati.

---

## 2026-09-04 — Il campo "ruolo" del resoconto va ancorato subito dopo `</a>`

**Decisione.** In `resoconto_stenografico.py` (`turni_seduta()`) il ruolo
dell'oratore (Relatore, Sottosegretario, Ministro...) non si cerca più con
`re.search(r"<em>...</em>", corpo)` su tutto il corpo dell'intervento, ma
con un `re.match` ancorato subito dopo `</a>` (con l'eventuale gruppo
parlamentare in mezzo). Un `<em>` che inizia con `(` (note di regia come
"Applausi", "Commenti") non conta come ruolo.

**Perché.** Il resoconto usa `<em>` anche per l'enfasi tipografica dentro
il discorso stesso (forestierismi, tecnicismi, citazioni di articoli come
"96-bis", note di regia). Un `re.search` senza ancora prende il primo
`<em>` che trova ovunque nel corpo — quasi sempre non è un ruolo, perché la
maggioranza dei deputati non ne ha uno. Segnalato dall'utente: parole senza
senso ("rave", "Guinness", "bis", "media"...) tra il nome e il tag di
gruppo nella pagina di un atto.

**Verificato.** Confronto sui 16 atti generati: i valori distinti del campo
ruolo passano da 439 (391 rumore) a 49 (1 solo falso sospetto nel filtro di
verifica, in realtà un ruolo genuino — "Vicepresidente della V
Commissione"). Nessun impatto sul tasso di aggancio testo-metadati (8497
interventi, 0 mancanti, invariato).

**Cosa la renderebbe sbagliata.** Un caso osservato ma non coperto: più
relatori nominati insieme prima del tag di ruolo comune (es. "OTTAVIANI,
PELLA e TRANCASSINI, <em>Relatori.</em>") — l'ancora richiede adiacenza
stretta, quindi qui il ruolo resta vuoto invece di essere attribuito a
tutti e tre. Raro (un solo caso trovato nei dati scaricati finora); da
rivedere se ricorre più spesso man mano che si generano altri atti.

---

## 2026-09-04 — Interventi duplicati: si lasciano, sono nel dato ufficiale

**Osservazione.** In diversi atti, uno stesso intervento (stesso testo,
stesso oratore) compare due volte di fila nello sviluppo cronologico.
Segnalato dall'utente insieme al problema del ruolo (sopra).

**Verificato — non è un nostro bug.** Su C. 1114 (seduta 0114, intervento di
Dario Carotenuto): la query SPARQL in `camera_lod.py` (`interventi_atto()`,
già `SELECT DISTINCT`) restituisce correttamente due righe *genuinamente
distinte* — `?interv` = `in19_679053` legato a `?disc` =
`disIdDib162653_19`, e `?interv` = `in19_678864` legato a `?disc` =
`disIdDib162640_19` — che condividono però la stessa `dc:relation`, cioè la
stessa ancora nel resoconto stenografico. È dati.camera.it stesso a
registrare lo stesso turno di parola sotto due nodi `discussione` diversi
(probabile causa: la seduta discute più provvedimenti collegati e la Camera
modella la cosa come due "discussioni" separate che puntano allo stesso
turno reale). `DISTINCT` funziona correttamente qui: non c'è nulla da
deduplicare a livello di riga SPARQL, la duplicazione è nel grafo.

**Decisione.** Non si deduplica in `sviluppo_atto()`. A differenza del bug
sul ruolo (quello sì un errore nostro di parsing, corretto sopra), qui
scartare una delle due copie significherebbe scegliere arbitrariamente
quale "discussione" ufficiale ignorare, senza un criterio che la fonte
stessa fornisca.

**Portata misurata.** Da 5 (C. 1483) a 128 (C. 705) coppie duplicate
consecutive per atto sui 16 atti generati; assente solo su C. 2397 e C. 75.

**Cosa la renderebbe sbagliata.** Se in futuro serve un conteggio esatto
degli interventi (non solo la lettura cronologica), la duplicazione va
trattata esplicitamente — es. deduplica per ancora a valle, con una nota
che dichiara quale copia si è tenuta e perché.

---

## 2026-09-04 — Testi in calce marcati e tolti dal corpus, non scartati

**Osservazione (seduta 0028, C. 705).** In calce ad alcune sedute compaiono
testi introdotti da `<p class="titolo_allegato">` con dicitura tipo "TESTI
DEGLI INTERVENTI DI CUI È STATA AUTORIZZATA LA PUBBLICAZIONE IN CALCE AL
RESOCONTO STENOGRAFICO DELLA SEDUTA ODIERNA". Sono testi depositati da un
deputato e mai pronunciati in Aula, ma strutturalmente identici a un turno
vero: stesso `<p class="intervento">`, stesso link alla scheda personale,
stesso `<em>ruolo</em>`. Il parser non li distingueva in alcun modo dal
dibattito vivo — finivano nel corpus di analisi come se fossero stati
oggetto di replica in tempo reale, il che è falso per definizione (nessuno
può rispondere a un testo che non è stato detto).

**Decisione.** `turni_seduta()` traccia quando l'ultimo `titolo_allegato`
incontrato scorrendo il documento marca l'inizio della sezione "in calce" e
imposta `pubblicato_in_calce=True` su tutti i turni successivi (il flag non
torna mai a `False` entro la stessa seduta: la sezione è sempre in coda al
resoconto). Il campo arriva fino a `Intervento` e ai JSON di `web/`. Il
frontend li **esclude** dal calcolo "chi ha parlato, per gruppo" (assieme
alla presidenza) ma li **mostra** nello sviluppo cronologico, in un box
distinto con l'etichetta "Testo autorizzato in calce — non pronunciato in
Aula": visibili, non silenziati, ma marcati come out-of-band rispetto al
dibattito.

**Cosa la renderebbe sbagliata.** Il segnale usato è posizionale (tutto ciò
che segue l'ultimo `titolo_allegato` della seduta), non un attributo esplicito
sul singolo turno. Se una seduta avesse *altri* `titolo_allegato` non legati
a testi depositati (es. un secondo blocco di ordine del giorno dopo gli
allegati), il flag si sporcherebbe. Da verificare su altre sedute quando se
ne presenta l'occasione.

---

## 2026-09-04 — Presidenza leggibile per intero, non più tagliata a 140 caratteri

**Osservazione.** In `web/index.html` i turni di presidenza erano sempre
troncati a `textShort` (140 caratteri, nessuna espansione), indipendentemente
dalla lunghezza — conseguenza diretta della decisione del 2026-08-05 ("il
rumore è la presidenza, non la brevità"). Ma quella decisione riguardava
l'unità di misura dell'analisi argomentativa, non implicava che un intervento
presidenziale chiarificatore (es. spiega cosa sta succedendo in aula, un
punto di procedura non banale) dovesse restare illeggibile in UI.

**Decisione.** I turni di presidenza usano ora lo stesso meccanismo di
espansione ("Leggi tutto") già in uso per i turni di merito, invece del solo
`textShort`. Restano visivamente distinti (corsivo, icona, opacità ridotta)
e restano esclusi dalle statistiche per gruppo: cambia solo la leggibilità,
non il perimetro dell'analisi.

---

## 2026-09-04 — Turni recuperati dal resoconto

**Origine.** Il turno di Luca Ciriani che pone la questione di fiducia su
C. 705 (seduta 0028, `tit00050.sub00050.int00020`) non ha nessun nodo
`ocd:intervento` nel grafo LOD — verificato interrogando il SPARQL endpoint
senza filtro per atto: l'ancora non esiste in nessun `dc:relation` per
quella seduta. Non è un collegamento mancante verso il 705: è un turno che
Camera non ha mai messo nel grafo, pur avendolo pubblicato per intero nel
resoconto stenografico (fonte già autorizzata, non scraping — vedi
`resoconto_stenografico.py`).

**Portata misurata (prima di intervenire).** Confrontando l'inventario
completo dei turni di `turni_seduta()` con l'inventario completo dei nodi
`intervento` del LOD per la stessa seduta (qualunque atto), il fenomeno non
è raro: sulle 3 sedute di C. 705, seduta 0024 zero buchi, seduta 0028 (quella
di Ciriani) 12 turni non-presidenza orfani, seduta 0029 (seduta fiume
ostruzionistica, già nota per l'anomalia — vedi la voce del 2026-08-05) ben
217 turni non-presidenza orfani, alcuni di migliaia di caratteri. Un buco
puntuale e uno sistematico dentro lo stesso atto.

**Decisione.** `sviluppo_atto()` recupera un turno orfano solo se cade nello
stesso blocco tit/sub del resoconto di un turno già confermato dal LOD per
quell'atto (mai un'attribuzione a un atto che in quella seduta non ha nessun
turno confermato). Per farlo:
- `resoconto_stenografico.py` ora cattura anche `idPersona` dal link alla
  scheda personale (era già nell'HTML, veniva scartato) e ricostruisce
  `deputato_uri` — indipendente da qualsiasi nodo LOD, funziona anche per i
  turni orfani.
- `camera_lod.py` espone `mappa_adesioni()` / `gruppo_per_data()`
  separatamente da `interventi_atto()`: la tabella deputato → gruppo per
  data è per persona, non per turno, quindi si può interrogare anche senza
  un nodo `intervento`.
- Ogni turno recuperato così porta `dedotto=True` in `Intervento`: è
  un'inferenza nostra sulla struttura del documento (stesso blocco tit/sub),
  non un dato che Camera dichiara esplicitamente. Il meccanismo è nella
  pipeline di produzione, quindi si applica automaticamente a tutti gli
  atti — presenti e futuri — non solo al 705.

**In `web/`.** I turni recuperati restano indistinguibili nel trattamento
visivo dai turni confermati (stessa barra colorata, stesso spazio, stessa
espansione) — sono dibattito vero, non testi in calce da isolare. La sola
differenza è un'etichetta piccola e muta ("non confermato dal LOD", con
tooltip) accanto al tag di gruppo: visibile a chi vuole verificare, non un
segnale che inviti a saltare il turno. Contano nelle statistiche per gruppo
come qualunque altro turno di merito.

**Effetto sul catalogo.** Rigenerati i 16 JSON: il totale interventi per
atto è più che raddoppiato in diversi casi (C. 705: 1030 → 2042; include
presidenza recuperata, esclusa dalle statistiche come sempre). Il numero
"interventi" mostrato nell'indice (`catalogo_atti.json`) resta quello
dichiarato dal LOD e non è stato toccato: sono due misure diverse, non un
'errore da correggere' l'una rispetto all'altra.

**Cosa la renderebbe sbagliata.** Il segnale è posizionale (stesso blocco
tit/sub), non un attributo esplicito sul turno. Se un blocco tit/sub
contenesse in realtà due argomenti diversi (es. un cambio di atto a metà
sub-titolo senza un nuovo `tit`/`sub` a segnarlo), un turno estraneo
finirebbe attribuito per errore. Non riscontrato finora, ma da tenere
d'occhio se compaiono attribuzioni palesemente fuori tema.

---

## 2026-09-04 — Tre link ufficiali Camera nella pagina atto di `web/`

**Decisione.** Ogni turno di merito in `web/index.html` linka ora, quando
disponibile: (1) la scheda personale del deputato, (2) la scheda del gruppo,
(3) il paragrafo esatto nel resoconto stenografico. Tutti e tre costruiti da
URI già presenti (o resi presenti) nei dati, nessuno scraping nuovo.

**Deputato.** `deputato_uri` (LOD, es. `.../deputato.rdf/d307857_19`) contiene
già l'id numerico Camera. Verificato in browser che
`documenti.camera.it/apps/commonServices/getDocumento.ashx?sezione=deputati&tipoDoc=schedaDeputato&idLegislatura=19&idPersona={id}&webType=Normale`
(stesso dominio già usato per i resoconti) fa redirect esatto alla scheda
personale umana su camera.it. Nessuna modifica alla pipeline: il campo
c'era già.

**Gruppo.** `?gruppo` era già interrogato dalla SPARQL in `camera_lod.py` ma
scartato — solo `dcterms:alternative` (la sigla) veniva tenuto. Aggiunto
`gruppo_uri` a `Intervento`, propagato da `interventi_atto()` /
`sviluppo_atto()`, e tutti i 16 JSON di `web/data/` rigenerati con
`scripts/genera_dati_web.py`. Il link punta alla pagina LOD del gruppo su
dati.camera.it (stesso stile già in uso per "apri scheda atto"): niente id
interno Camera noto per un link diretto a una scheda gruppo umana.

**Resoconto (deep link al paragrafo).** `id_seduta` + `ancora` erano già nei
dati. Il link ovvio via `documenti.camera.it/getDocumento.ashx` **non
funziona per il deep-link**: verificato che il suo redirect perde il
frammento `#ancora`, atterrando sulla pagina della seduta senza scroll. Si
linka invece direttamente a `www.camera.it/leg19/410?idSeduta={id}&tipo=stenografico#{ancora}`
(la destinazione finale di quel redirect), che conserva il frammento e
scrolla al paragrafo giusto — verificato che l'id del frammento corrisponde
esattamente al turno atteso.

**Cosa la renderebbe sbagliata.** Il path `/leg19/410` per il resoconto e la
struttura dell'URL `schedaDeputato` sono pattern osservati, non documentati
formalmente da camera.it: un cambio di piattaforma sul sito lato "umano"
(non sugli endpoint di `documenti.camera.it` usati per lo scraping) li
romperebbe senza preavviso. Da ricontrollare se compaiono link rotti.

---

## 2026-09-04 — Riassunti e vector search: grana per intervento, non per gruppo

**Decisione.** Si introduce un DB (FastAPI + SQLite, con `sqlite-vec` per gli
embedding) per una nuova funzione di riassunto degli interventi. Il riassunto
si genera **one-shot al momento dell'acquisizione dell'atto** e resta legato
per sempre al singolo intervento (`ancora`), non al gruppo — a differenza
della prima bozza di schema discussa, che lo prevedeva a grana atto×gruppo.

**Perimetro di generazione.** Niente riassunto (né embedding) per i turni di
**presidenza**. I turni **`pubblicato_in_calce`** (testi autorizzati in
calce, mai pronunciati in Aula — vedi la voce del 2026-09-04 sopra) **sì**,
vengono riassunti: restano testo vero prodotto da un deputato, la loro
esclusione dalle statistiche per gruppo è una scelta separata che riguarda i
conteggi, non la disponibilità di un riassunto.

**Due politiche di vettorizzazione distinte.**
- **Riassunto**: testo breve, imbeddato per intero in un solo vettore
  (`vec_riassunti`, 1:1 con `ancora`). Chunkarlo sarebbe controproducente:
  frammenterebbe il punto di sintesi che deve restare recuperabile in un
  colpo solo.
- **Testo originale del turno**: chunkato prima di essere imbeddato
  (`intervento_chunk` + `vec_intervento_chunk`), perché i turni di merito
  sono lunghi e spesso multi-tema (mediana ~3.800 caratteri, vedi la voce
  del 2026-08-05 "Il rumore è la presidenza, non la brevità"). I confini dei
  chunk vanno presi dalla struttura già nota del resoconto (paragrafi
  `<p class="intervento">` / `<p class="interventoVirtuale">`), non da un
  text-splitter generico a caratteri fissi.

**Punto aperto, deliberatamente non deciso ora.** Il modello di embedding —
e se sarà lo stesso per riassunti e chunk o due modelli diversi con
dimensioni diverse — si valuta più avanti. Vincolo già fissato: **deve
girare in locale**, non un servizio di embedding esterno. Lo schema (vedi
sotto) lascia la dimensione del vettore parametrica per questo.

**Schema abbozzato** (non ancora implementato — nessun codice scritto con
questa decisione):

```sql
CREATE TABLE atti (
    numero_camera   TEXT PRIMARY KEY,
    numero_senato   TEXT,
    denominazione   TEXT,
    creato_il       TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE interventi (
    ancora              TEXT PRIMARY KEY,
    numero_camera       TEXT NOT NULL REFERENCES atti(numero_camera),
    id_seduta           TEXT NOT NULL,
    data                TEXT NOT NULL,
    deputato_uri        TEXT,
    deputato_nome       TEXT,
    gruppo_sigla        TEXT,
    gruppo_uri          TEXT,
    ruolo               TEXT,
    presidenza          INTEGER NOT NULL DEFAULT 0,
    pubblicato_in_calce INTEGER NOT NULL DEFAULT 0,
    dedotto             INTEGER NOT NULL DEFAULT 0,
    testo               TEXT NOT NULL
);

CREATE TABLE riassunti (
    ancora        TEXT PRIMARY KEY REFERENCES interventi(ancora),
    testo         TEXT NOT NULL,
    modello       TEXT NOT NULL,
    generato_il   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE VIRTUAL TABLE vec_riassunti USING vec0(
    ancora    TEXT PRIMARY KEY,
    embedding FLOAT[N]
);

CREATE TABLE intervento_chunk (
    id      INTEGER PRIMARY KEY,
    ancora  TEXT NOT NULL REFERENCES interventi(ancora),
    ordine  INTEGER NOT NULL,
    testo   TEXT NOT NULL,
    UNIQUE (ancora, ordine)
);

CREATE VIRTUAL TABLE vec_intervento_chunk USING vec0(
    chunk_id  INTEGER PRIMARY KEY,
    embedding FLOAT[N]
);
```

**Nota identitaria.** Persistere il riassunto a grana di singolo intervento
non viola il vincolo "output pubblicabile sempre per gruppo" (CLAUDE.md): il
vincolo riguarda cosa si pubblica, non cosa si conserva — "il livello
individuale resta interrogabile nel dato, mai nel titolo". Da rispettare
quando si costruirà la superficie pubblica: nessuna vista che aggreghi o
classifichi per deputato.

**Cosa la renderebbe sbagliata.** Se la generazione one-shot si rivela
troppo rigida — es. serve rigenerare un riassunto dopo una correzione della
Camera al resoconto — va rivista l'assenza di versionamento sui riassunti
(oggi una riga per `ancora`, sovrascrivibile ma senza storico). Non
osservato finora, perché nessun riassunto è stato ancora generato.
