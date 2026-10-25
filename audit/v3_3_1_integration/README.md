# Integrazione delle regole acquisite nel candidato

## Comportamento effettivo

`core.score` usa ora `rules.league_config` quando presente. Prima risolve
le sostituzioni con il resolver esistente, poi applica modificatore difesa,
capitano/vice e soglie gol della configurazione ricevuta. Voto puro e
fantapunteggio rimangono separati. Il percorso acquisito richiede stringhe
decimali per gli osservati; somma e confronti delle fasce usano razionali BigInt.
Il campo `exact` conserva i totali decimali; i campi numerici sono viste per
report e statistiche. I fantagol vengono calcolati sul totale esatto.

`simulator.evaluate` supporta lo stesso scoring tramite il modello esplicito
`EXPLICIT_DISCRETE_PMF`: ogni giocatore deve avere una PMF di voti con stringhe
decimali e probabilità valide. Non viene inventato un arrotondamento per la
precedente distribuzione normale continua. I coefficienti di shock continuo
devono essere zero in questo percorso; le correlazioni di gol e portieri
restano quelle degli scenari condivisi esistenti. Le PMF devono già incorporare
il contesto della previsione; non sono apprese automaticamente.

Se una simulazione incontra una regola ignota (per esempio entrambi capitano
e vice SV), l'intera valutazione viene bloccata e gli eventuali risultati
parziali sono scartati, senza selezionare soltanto i campioni riusciti.
Se fallisce la conferma indipendente, l'ottimizzatore non pubblica una scelta.
Gli input REAL senza configurazione acquisita non possono usare le fasce
del precedente esempio sintetico. Le date di ricezione delle regole devono
precedere `as_of`; le immagini non sono prove pre-lock per giornate passate.

Il modello sintetico precedente resta disponibile per regressione. La sua
assenza di `league_config` è esplicita e non viene presentata come regolamento
reale. Main e l'engine d'asta restano invariati.

## Evidenze eseguite

- **75/75 test Node**: 23 precedenti, 32 del componente e 20 di integrazione.
- Sette gruppi di verifica complessivi passati, inclusi 21 test Python,
  10 test del dossier GOLD, legacy e validatori ufficiali.
- Nove asset di produzione identici al commit main
  fa9562decb683a3d64ca248cb66ff20099ddcb54.
- Run congelata: **100.000 scenari di sviluppo + 100.000 di conferma**,
  due candidate dichiarate (4-4-2 e 3-5-2), seed 20261018 e seed indipendente.
  Tempo misurato **40,065 secondi** in questo ambiente. Non prova il budget
  di una ricerca esaustiva, di una rosa reale o di una pipeline di pubblicazione.
- Manifest di input/report e hash del codice della run verificati.

`prepare-synthetic.js` dichiara e costruisce PMF artificiali per i giocatori
di test; non contiene proiezioni dei giocatori reali. Disponibilità senza SV
e coefficienti di shock nulli sono ipotesi di questa fixture e non stime
della National League. Le fasce provengono dagli screenshot, ma gli altri
parametri dei giocatori e gli eventi modellati restano il sottoinsieme
sintetico esistente (non tutti i bonus/malus mostrati sono simulati).

## Gate aperti

**TECH PASS V3.3.1 = NO; STAT VALIDATED = NO; GOLD LOCK = NO.**

L'integrazione chiude il precedente distacco tra componente e percorso di
scoring per i casi supportati; non è il PASS integrale di G09/G10. Restano
le eccezioni non mostrate, schema semantico completo, fonte del normale bonus
gol, casi SV e sostituzioni complessi da confermare con replay ufficiali.
Le dipendenze PRNG/ordine del candidato, obiettivo strategico completo,
budget/ripiego, G14/G15 reali, golden ufficiali, parity e iPhone restano aperte.
Nessuna metrica fuori campione viene sostituita dai risultati sintetici.

Gli snapshot storici e le run precedenti restano nei loro commit e cartelle;
i loro hash di codice non devono essere confrontati con questa nuova versione
come se fosse la stessa revisione. La nuova run ha il proprio manifest.

## Riproduzione

```bash
node --test experimental/match-win-v3_2/test.js \
  experimental/match-win-v3_2/league-rules.test.js \
  experimental/match-win-v3_2/league-integration.test.js
python audit/v3_3_1_integration/verify.py
node experimental/match-win-v3_2/run.js \
  audit/v3_3_1_integration/synthetic-pmf-input.json \
  /percorso/nuova-cartella-run 100000 20261018
```

La directory di output deve essere nuova: il runner rifiuta di sovrascrivere
una run congelata. I comandi Python richiedono le dipendenze della baseline.
