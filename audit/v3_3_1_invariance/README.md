# Chiusura dei due difetti di ordine riprodotti in Fase 0

La regressione originaria resta in `audit/v3_3_1_phase0/probes.json`, riferita
alla versione allora ispezionata. Questo audit verifica la correzione sul
candidato successivo a 8a481b2fb26cf4120dd6aaf1796d2366c5762eda.

## Correzioni effettive

- Il compilatore ordina copie dei record di giocatori e fixture per ID prima
  delle estrazioni. Non modifica gli array ricevuti dal chiamante.
- Il resolver ordina gli ID titolari prima delle somme e delle sostituzioni;
  conserva esattamente l'ordine operativo della panchina.
- L'ultimo spareggio usa SHA-256 della decisione completa: titolari ordinati,
  panchina in ordine, capitano e vice. La codifica dei singoli campi è esplicita
  JSON UTF-8 per evitare ambiguità con delimitatori contenuti negli ID.
- Il report espone `recommended_decision_id`; gli indici continuano a puntare
  all'array originale del chiamante e possono cambiare quando questo cambia.

## Evidenza misurata

`regression.json` conserva i due confronti richiesti: 2.000 scenari con seed
20261018 su record normali e invertiti, più spareggio esatto su due candidate
in ordine opposto. Entrambi i controlli passano.

**85/85 test Node passano**, inclusi dieci nuovi test su record, eventi,
candidate, titolari, panchina, capitano/vice, fixture, duplicati e delimitatori.
Il log completo è `node-tests.log`.

Questo è un risultato di determinismo nel perimetro testato. Il PRNG JavaScript
resta quello V3.2 a 32 bit: non è PCG64 e non usa ancora flussi separati per
entità/scenario. L'aggiunta di un nuovo giocatore può cambiare la sequenza;
la proprietà verificata qui riguarda le permutazioni degli stessi record.
I metadati grezzi, gli hash del payload originario e il riferimento della
differenza appaiata alla prima candidata possono legittimamente differire.
La serializzazione dell'identità Node è esplicita ma la parità con la baseline
Python importata deve ancora essere verificata; non si dichiara G17 chiuso.

Le run precedenti restano legate ai rispettivi hash di codice. Non è stata
rieseguita o aggiornata la run da 200.000 scenari della revisione precedente:
il suo risultato non è attribuito a questa nuova revisione.

## GOLD

**TECH PASS V3.3.1 = NO; STAT VALIDATED = NO; GOLD LOCK = NO.**

Queste due correzioni non risolvono tutti i gate. Restano PCG64 e contratto
completo di riproducibilità, obiettivi e confronti statistici completi,
schema/eccezioni, pipeline e ripiego, golden ufficiali, G14/G15 reali,
parità Excel/PWA e prova iPhone. Nessun dato reale o attestazione PASS è
stato creato per forzare il rilascio. Nessun merge o deploy è eseguito.

## Riproduzione

```bash
node audit/v3_3_1_invariance/verify.js
```

Il comando aggiorna solo il nuovo report e log. I manifest sono integrità
dei byte, non firme digitali o certificazioni statistiche.
