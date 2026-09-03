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
