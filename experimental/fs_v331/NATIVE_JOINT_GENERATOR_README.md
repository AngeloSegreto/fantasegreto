# FantaSegreto V3.3.1 — Native Joint Event Generator (SHADOW)

## Cosa fa davvero
`experimental/fs_v331/joint_event_generator.py` genera scenari congiunti *a livello evento* utilizzando esclusivamente Python standard library. Ciascuna delle 10 partite reali viene campionata una sola volta per scenario: i due risultati, il ritmo condiviso, l'attribuzione dei marcatori e degli assist, i voti, le ammonizioni, le espulsioni e i gol subiti dai portieri sono coerenti nell'ambito di quello scenario. Una singola estrazione del giocatore serve tutte le formazioni fantasy candidate; per confrontarle, riusare sempre lo stesso bundle.

- Il formato in uscita espone `joint_fixture_groups`, `scenarios[].fixture_states` e `scenarios[].player_outcomes`, compatibili **strutturalmente** con `prelock_scenario_compare.py` nel ramo V3.3.1.
- Per i giocatori esterni alle due rose si usa `scorer_player_id: null`, non si inventano nomi o identity.
- Scorer, assist e portieri si riferiscono alla medesima partita: non si estraggono i bonus separatamente dai gol della squadra.
- La scelta del portiere di ciascun club è esclusiva nel modello (massimo un portiere con voto). L'eventuale portiere di altre fantasquadre non è modellato perché non appartiene agli input.
- I giocatori in panchina fantasy sono presenti nelle estrazioni, non soltanto i titolari: la sostituzione è applicata dal **comparatore/scoring engine**, non da questo generatore.

## Esecuzione e input
Lo script accetta `--calendar` (JSON con 10 partite), `--own-roster` e `--opponent-roster` (ciascuno con `roster` di ID/club/ruolo), tre timestamp ISO-8601 con offset, `--count`, `--seed` e `--output`.

- Con `--synthetic-demo` crea **soltanto** parametri di prova identici per tutti i ruoli. Non sono previsioni né dati storici.
- Con `--parameters percorso.json` esige un record per ciascuna partita e ciascun giocatore, con `source_kind: EXPLORATORY_ASSUMED` o `SYNTHETIC_UNIT_TEST`. Il modello **non** crea probabilità mancanti.
- In entrambi i casi l'output è etichettato `SYNTHETIC_UNIT_TEST`, `GOLD_LOCK=false` e `STAT_VALIDATED=false`.
- Si ferma se mancano fixture o proiezioni, si duplicano gli ID, i portieri della stessa squadra superano probabilità totale 1 o i timestamp violano il lock.
- `--count` massimo 10.000 per impedire output JSON sproporzionati. Generare batch con seed diversi per simulazioni più estese, ma **non** cumulare automaticamente fino a quando non esiste un consolidatore rigoroso.

**Schema parametri partita**, indicizzato dalla chiave `casa|trasferta|kickoff`:
`home_goal_mean`, `away_goal_mean` (0..5), `shared_pace_shape` (>0), `assist_event_probability` (0..1), `other_scorer_weight`, `other_assist_weight` (>0).

**Schema proiezione per giocatore**, indicizzato da ID: `pure_mean`, `pure_sd`, `vote_probability`, `scorer_weight`, `assist_weight`, `yellow_probability`, `red_probability`. Per i portieri, `vote_probability` è la probabilità di essere l'unico portiere a voto del club; per il resto indica probabilità di ottenere un voto.

## Test
`cd experimental/fs_v331 && python -m unittest -v test_joint_event_generator`

11 test locali passati il 4 novembre 2026: riproducibilità, dieci partite, integrità marcatori/assist, fantavoto = voto + eventi, gol subiti del portiere, esclusività portieri, zero marcatori dei due roster, controlli temporalità e fail-closed.

## Limiti prima di GOLD
1. **Calibrazione vera mancante**: intensità gol, presenze, voti, scorer/assist devono essere stimate da dati storici pre-lock documentati, non dai default del demo. Servono split temporali, holdout e metriche out-of-sample per i gate G14/G15.
2. Copertura incompleta: cambi portiere in gara, rigori, autogol, salvataggi, espulsioni di portieri, bonus assist soft/gold e durata effettiva dei giocatori non modellati. La coerenza riguarda soltanto le variabili effettivamente implementate, **non** l'insieme degli eventi ufficiali.
3. G05 è **testato sinteticamente**, non attestato su eventi ufficiali. Il comparatore attuale `prelock_scenario_compare.py` è ancora limitato a *matchday 8*: i bundle della giornata 11 richiedono un aggiornamento controllato del comparatore e fixture verificate.
4. Non c'è ancora un autentico snapshot pre-lock delle proiezioni, della formazione completa dell'avversario, del suo ordine di panchina, dei suoi capitani e delle ore di lock.
5. Non scrive formazioni nell'app, non promuove branch e non modifica il GOLD.

## Artefatto dimostrativo
`FS_NATIVE_JOINT_250_SYNTHETIC_EVENTS_DEMO.json`: 250 scenari su 10 fixture **fittizie** nell'anno 2030, con 6 calciatori fittizi. È una smoke-test dimostrativa, non il risultato della Serie A 2026/27.
