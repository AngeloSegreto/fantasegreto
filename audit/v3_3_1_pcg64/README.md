# PCG64 nel simulatore candidato

## Requisito implementato e verificato

Il percorso `simulator.evaluate` usa ora **PCG XSL RR 128/64**. La precedente
funzione a 32 bit è rimossa; anche `rng(seed)` usa PCG64 come helper a flusso
singolo. Nelle valutazioni complete ogni scenario deriva flussi distinti
per MATCH, TEAM e PLAYER, con chiave SHA-256 versionata comprendente master
seed, numero dello scenario e ID dell'entità. I risultati delle partite
restano comuni alle due squadre fantasy e a tutti i portieri interessati.

La semina è definita esplicitamente da hash -> stato uint128 e incremento
uint128 dispari. **Non è compatibilità con NumPy SeedSequence(seed)**:
il confronto indipendente imposta esattamente lo stesso stato/incremento.
La baseline Python importata usa un'altra inizializzazione; la parità completa
tra i due candidati resta da chiudere e non è dedotta dai test qui descritti.

## Evidenze misurate

- NumPy 2.3.5 ha generato le reference per 100 stati, inclusi casi limite:
  **800 output uint64 e 800 uniformi double coincidono esattamente** con Node.
- **95/95 test Node passano**, inclusi dieci nuovi test PCG64.
- I flussi sono riproducibili per seed/entità/scenario; riordinare le entità
  o consumare un altro flusso non cambia i draw del giocatore testato.
- Aggiungere un giocatore indisponibile con quote gol/assist nulle non sposta
  le prestazioni degli altri nello scenario verificato. Aggiungere invece
  un partecipante con peso positivo può legittimamente cambiare le attribuzioni.
- Nuova run congelata con questa revisione: **50.000 scenari di sviluppo +
  50.000 di conferma**, due candidate dichiarate, **35,816 secondi** locali.
  Non è una ricerca esaustiva né una misura su rose e previsioni reali.
- Il report espone `random_engine=PCG64_XSL_RR_128_64_ENTITY_SCENARIO_V1`.
  I manifest della nuova run conservano input, codice e output usati.

Reference metodologica primaria:
https://numpy.org/doc/stable/reference/random/bit_generators/pcg64.html
Il generatore `generate_numpy_vectors.py` permette di ripetere il confronto
con la libreria di riferimento installata. Queste sono prove tecniche del
generatore, non una validazione del modello predittivo.

## Stato di rilascio

**Il requisito PCG64 del candidato è verificato nel perimetro dichiarato.**
Non equivale al PASS globale G21 o al rilascio V3.3.1:
restano replay e ambiente completi, parità con gli altri percorsi,
profili e confronti statistici completi, schema/eccezioni di lega,
pipeline/ripiego, golden ufficiali, G14/G15 su dati reali, parity e iPhone.

**TECH PASS V3.3.1 = NO; STAT VALIDATED = NO; GOLD LOCK = NO.**
L'autorizzazione dell'utente consente lo sviluppo e la pubblicazione sul branch;
non è registrata come una misura di accuratezza o come PASS dei gate mancanti.
Main, produzione e vecchie run rimangono invariati. Le vecchie run e gli audit
sono riferiti alle revisioni precedenti: non vengono riscritti per mostrare
il nuovo PRNG come se fosse già presente nelle prove passate.

## Riproduzione

```bash
python audit/v3_3_1_pcg64/generate_numpy_vectors.py
node --test experimental/match-win-v3_2/test.js \
  experimental/match-win-v3_2/league-rules.test.js \
  experimental/match-win-v3_2/league-integration.test.js \
  experimental/match-win-v3_2/invariance.test.js \
  experimental/match-win-v3_2/pcg64.test.js
node experimental/match-win-v3_2/run.js \
  audit/v3_3_1_integration/synthetic-pmf-input.json \
  /percorso/nuova-run-pcg64 50000 20261018
```

La cartella della run deve essere nuova. Il risultato è SYNTHETIC_TEST_ONLY,
con PMF artificiali e ipotesi di disponibilità costruite per il test; non
costituisce una raccomandazione per la giornata della National League.
