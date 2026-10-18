# FS FANTASEGRETO — ADAPTIVE MATCH-WIN INTELLIGENCE V3.2 RC1

**Candidato sperimentale, non GOLD, non promosso.** La scelta massimizza la probabilità di vincere in fantagol contro una formazione avversaria nello stesso scenario. Il confronto avviene fra formazioni complete, con sostituzioni, bonus di reparto e capitano ricalcolati. La produzione conserva il motore precedente.

Repository ispezionato: `AngeloSegreto/fantasegreto`, branch di partenza `main`, commit `fa9562decb683a3d64ca248cb66ff20099ddcb54`. Runtime rilevato: V4.2.5, registry ufficiale 539 giocatori al 13 ottobre, engine V4.0.23.1 LOCK + AUCTION_MARKET_V1. `index.html` carica `app.js`, quindi `engine.js` e il market layer. Il vecchio `premium-monte-carlo-v1.js` è standalone; il candidato V3.2 resta standalone nello stesso spirito e non viene caricato da `index.html` di produzione.

## Risultati misurati

- 23 test del candidato superati; 28 controlli dello scoring legacy e contratto legacy superati.
- Entrambi i validatori offline del runtime ufficiale superati: 539 identità coerenti.
- 100.000 scenari sintetici condivisi, 14 formazioni candidate: sette moduli per due portieri. Altri 100.000 scenari, seed indipendente, per controllare la scelta rispetto al migliore modulo alternativo. Circa 11,6 secondi sul runtime locale di questa esecuzione.
- Controllo di consistenza fra le due metà del campione superato per tutte le 14 candidate. Non dimostra calibrazione o correttezza del modello del mondo reale.
- Hash degli asset di produzione uguali al commit di partenza. Manifest degli input, del codice e dei report verificati.
- 23 nomi della rosa di riferimento G6/G7 risolti univocamente nel registry. Non sono una certificazione della rosa o della formazione attuale.
- Prova di readiness sui dati reali: **zero simulazioni**, probabilità assenti, elenco esplicito degli input mancanti.
- UI: script e struttura statica testati. Test Chromium non eseguito: eseguibile assente; tentativo di download fallito. Safari/iPhone fisico non verificato.
- Nessuna API a pagamento, GPU, inferenza cloud o abbonamento attivato.

## Esecuzione gratuita locale

Richiede Node.js 18+; nessuna dipendenza per motore, simulazioni o test. I validatori legacy usano Python standard library.

```bash
node --test experimental/match-win-v3_2/test.js
node experimental/match-win-v3_2/run.js --synthetic /tmp/fs-new-synthetic-run 100000 20261018
node experimental/match-win-v3_2/run.js experimental/match-win-v3_2/real-input-template.json /tmp/fs-new-readiness-run
node experimental/match-win-v3_2/audit.js
```

Usare una directory nuova per ogni run. Il runner rifiuta una destinazione esistente, registra dataset, codice, seed e report e non modifica le run precedenti. Sono file ordinari con hash e una convenzione di non sovrascrittura, non uno storage WORM. Il file `execution.base_commit` identifica il parent su cui il candidato è stato costruito; gli hash del codice identificano esattamente il candidato eseguito.

Per simulare un proprio input: usare `example.js` e `runs/synthetic/input.json` come schema, senza trasferire i parametri inventati del test ai giocatori reali. Il file può contenere `{input, candidates}`; senza un pannello viene valutata la sola formazione `home.lineup`. L'avversario rimane quello specificato in `away.lineup`.

## Componenti e contratti

| Componente | Implementazione |
|---|---|
| Identità, fixture, disponibilità, provenienza, freschezza | `core.js`: validazione, probabilità di start/sub/voto/SV, decadimento confidence fonte |
| Voti e fantapunti condizionati al calendario | `simulator.js`: distribuzioni individuali condizionate ai gol avversari e a shock di squadra |
| Eventi correlati | Un unico risultato per partita, gol assegnati a un solo marcatore, assist collegato alla stessa azione, gol subiti e clean sheet dei portieri coerenti |
| Regole National League | Soglia 66, fascia 4, nessun epsilon; sostituzioni stesso ruolo, massimo cinque, priorità della panchina nell'ordine di visualizzazione |
| Modificatore | Portiere e tre migliori voti puri, almeno quattro difensori effettivamente con voto, fasce da configurazione |
| Capitano | Voto puro, fasce configurate, vice su SV, nessuna eredità automatica della fascia al sostituto |
| Ottimizzazione | `optimizer.js`: confronto di XI, panchina, capitano/vice e portiere per P(vittoria), poi pareggio, completezza e punti |
| Disponibilità bayesiana | `diagnostics.js`: aggiornamento Beta con cutoff e osservazioni reali; posterior distinto da probabilità calibrata |
| Calibrazione e backtest | Brier multiclass, log loss, MAE, ECE della vittoria, Brier voto/bonus; fold rolling con soli risultati completati prima del lock |
| Panchina e oracle | Punti e bonus inutilizzati, recupero via sostituzioni, oracle limitato al pannello fornito, nessuna deduzione automatica di errore prevedibile |
| LIVE | What-if deterministico sullo stato osservato, con punti mancanti a pareggio/vittoria; probabilità LIVE non implementate |
| Audit e UI | Audit G0–G19, report con hash, pagina decision-first autonoma con import locale JSON |

Le fasce del modificatore e del capitano presenti in `example.js` sono **inventate per il test**. Il valore `rules.verified` e la sua provenienza sono obbligatori: non sostituiscono la verifica umana dell'evidenza esterna. Le regole effettive devono essere acquisite prima dell'utilizzo reale. Le funzioni legacy con fasce hardcoded non vengono importate dal candidato.

`projection.vote_mean` e `vote_sd` sono parametri del voto puro condizionato a voto valido. I coefficienti di contesto sono specifici del giocatore/ruolo. Goal/assist share sono quote condizionate alla partecipazione con voto e mantengono massa residua per i giocatori non rappresentati: l'assenza di un compagno non aumenta automaticamente la quota degli altri. Non sono probabilità di gol individuali marginali né si ricavano da FOS o FVM.

Il modello attuale usa Poisson separati per i due punteggi reali, un fattore normale condiviso di squadra per i voti e uno shock comune di disponibilità. Le correlazioni fantasy derivano dagli eventi di partita condivisi. Queste sono assunzioni euristiche del candidato; mancano la stima empirica delle dipendenze fra punteggi, la dinamica temporale delle espulsioni e i minuti individuali. Il portiere è un occupante esclusivo per tutta la partita; infortuni e cambi del portiere durante la gara richiedono un adapter temporale successivo. `EXCLUSIVE_FULL_MATCH` deve essere riconosciuto esplicitamente negli input.

## Perimetro della ricerca

`enumerate(input, {bench:'ALL', captains:'ALL'})` genera le combinazioni ammissibili nei sette moduli, tutte le permutazioni della panchina e tutte le coppie capitano/vice. Stima prima la dimensione: oltre 1.000 candidate rifiuta l'esecuzione, senza tagliare silenziosamente il pool ai giocatori con media più alta. Con `FIXED` viene dichiarato il vincolo di ricerca. Il profilo con capitani fissi esclude gli XI che non li contengono.

Il run incluso confronta un **pannello esplicito di 14 candidate**; non è la ricerca globale su tutte le combinazioni di una rosa reale di 25 giocatori. Il runtime esaustivo per grandi rose e la ricerca congiunta completa della panchina restano da ottimizzare prima della promozione. L'output dichiara sempre il perimetro; non certifica un ottimo globale quando non è stato esplorato.

La classifica viene scelta sul campione iniziale. Il holdout indipendente controlla quella scelta senza riordinare i risultati. Gli intervalli riportano solo l'errore di campionamento Monte Carlo, condizionato ai parametri: non includono l'incertezza dei parametri o l'errore predittivo reale. Il confronto fra moduli usa differenze appaiate sullo stesso insieme di scenari.

Il confronto A/B/C/D presenta massima media, massima completezza, distribuzioni comuni e massima P(vittoria). Non finge quattro predittori indipendenti: i primi due sono diagnostiche dello stesso modello. I pesi ensemble restano `null` fino a una stima su storico fuori campione.

## Dati reali e gate aperti

`real-input-template.json` mantiene nulli calendario, proiezioni, formazione e avversario attuali, regole non verificate. I dati G7 del Master Prompt sono conservati separatamente in `g7-observed.json`, etichettati come risultati riferiti dall'utente e non riconciliati con voti ufficiali. Non entrano nella previsione pre-G7, né dimostrano da soli che il 3-5-2 fosse la scelta preventiva migliore.

Per una previsione reale servono: giornata e lock; rose/XI/panchina aggiornati di entrambe le squadre; calendario e fonti prima del lock; proiezioni con provenienza; regole ufficiali di bonus/malus, modificatore, capitano e SV eccezionali. Svilar non riceve una data di rientro inventata; il template conserva la sua indisponibilità riferita dall'utente e richiede verifica del rientro.

Restano da completare: acquisizione automatica delle fonti e calendario, modello temporale LIVE con residuo condizionato, dinamica delle espulsioni e minuti, ricerca completa su rose grandi, confronto reale dei portieri, storico di calibrazione, backtest temporale reale, ensemble appreso, parità Excel/PWA e accettazione fisica iPhone. `release-audit.json` elenca G0–G19 separando PASS tecnico, verifica sintetica, perimetro parziale e PENDING.

## Anteprima e rilascio

Aprire `experimental/match-win-v3_2/index.html` tramite server locale, per esempio `python -m http.server 8000` dalla root. La pagina parte senza probabilità reali. Il pulsante esplicito apre il report sintetico; l'upload può aprire un altro report. Non usa servizi esterni e non registra service worker.

Il test browser fornito è opzionale e richiede Playwright con Chromium già disponibile:

```bash
node experimental/match-win-v3_2/audit-browser.js
```

Non installa dipendenze né attiva servizi a pagamento. Se l'eseguibile manca, scrive `BLOCKED_BROWSER_UNAVAILABLE` e termina con codice 2. Il test su dispositivo Safari resta comunque necessario.

Promozione bloccata. Prima del merge operativo servono i gate reali e un adapter esplicito alla dashboard. Tutti i cambiamenti di questa RC sono confinati alla nuova directory: rollback tramite rimozione del candidato o mancato merge, senza migrazioni di storage o stato d'asta.
