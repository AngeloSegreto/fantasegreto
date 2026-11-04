# FS FantaSegreto | Generatore congiunto nativo V1.0 (SHADOW)

**Stato:** software implementato e verificato su dati sintetici. **Non** calibrato su risultati reali. GOLD_LOCK=false, STAT_VALIDATED=false.

## Funzione

native_joint_generator.py produce un unico stato per ciascuna delle dieci partite di Serie A a ogni estrazione. Lo stesso stato comprende:

- gol casa/trasferta correlati da un fattore comune di ritmo;
- eventi-gol con marcatore e assistente della stessa squadra oppure OTHER per i giocatori non osservati;
- stato VOTED/SV/DID_NOT_PLAY coerente: un giocatore SV non puo ricevere eventi individuali;
- voto puro, fantavoto, ammonizioni ed espulsioni sintetiche con audit del calcolo;
- gol subiti e clean sheet del portiere derivati dagli stessi gol della partita;
- fixture_states e player_outcomes per tutti i giocatori dei due fantateam, compatibili con prelock_scenario_compare.py.

**Tutte le formazioni alternative** (3-5-2, 4-4-2, 4-3-3, capitano, vice e panchina ordinata) devono essere valutate riutilizzando gli stessi scenario_id e gli stessi player_outcomes.

## Input vincolanti

1. --roster: JSON con roster di calciatori, ID ufficiali, squadra e ruolo.
2. --opponent: secondo roster nel medesimo formato, con ID ufficiali disgiunti. L'undici avversario e il capitano sono richiesti dal comparatore, non dal generatore.
3. --calendar: JSON con matchday e games di dieci incontri (home, away, kickoff), venti squadre distinte.
4. --priors: JSON con schema FS_NATIVE_JOINT_PRIORS_V1, evidence_kind SYNTHETIC_UNIT_TEST, players e fixtures.
5. --source-cutoff-at, --generated-at, --lock-at: timestamp ISO8601 con offset. Il motore rifiuta input con data delle fonti successiva alla generazione o lock dopo il primo kickoff.

Per calciatore i parametri sono availability (AVAILABLE, DOUBTFUL, OUT, UNKNOWN), vote_probability, pure_vote_mean, pure_vote_sd, goal_weight, assist_weight, yellow_probability, red_probability.

Per fixture la chiave e home|away|kickoff, i parametri sono home_xg, away_xg, shared_tempo_sd, other_goal_weight, other_assist_weight, assist_chance. Sono **input obbligatori**, non statistiche inventate dal programma.

## Test e demo offline

    python -m unittest discover -s experimental/fs_v331 -p 'test_native_joint*.py' -v
    python experimental/fs_v331/native_joint_demo.py --output-dir ./native_joint_demo --n 200 --seed 3301

La demo utilizza un calendario sintetico futuro nel 2030, parametri di esempio, nessun accesso di rete e nessun servizio a pagamento.

Comando CLI indipendente:

    python experimental/fs_v331/native_joint_generator.py \
      --roster own.json --opponent rival.json --calendar calendar.json \
      --priors priors.json --source-cutoff-at '2030-11-07T12:00:00+01:00' \
      --generated-at '2030-11-07T12:01:00+01:00' \
      --lock-at '2030-11-07T14:30:00+01:00' \
      --n 200 --seed 3301 --output joint_scenarios.json

## Integrazione V3.3.1

- native_joint_generator.py crea il bundle che prelock_scenario_compare.py riceve in input.
- Il comparatore ora valida matchday del calendario contro matchday del bundle, senza vincolarsi rigidamente a G8.
- league_scoring_v331.py rimane invariato: Traditional cinque sostituzioni di pari ruolo, fattore capitano su voto puro, modificatore difesa e soglie 66/4.
- test_native_joint_comparator_bridge.py verifica end-to-end il flusso con tutti i tre moduli, usando esclusivamente dati sintetici.

## Stato verifiche

| Controllo | Stato |
|---|---|
| Generatore nativo con evento per fixture | Implementato |
| Marcatori/assist della squadra corretta | Test sintetico superato |
| Portiere e fantavoto coerenti con gli eventi | Test sintetico superato |
| Integrazione scorer V3.3.1 | Test sintetico, CI da verificare |
| Parametri previsionali calibrati su storico autenticato | **NON VERIFICATO** |
| Rigori, autogol, secondo giallo e processo infortuni | **NON IMPLEMENTATI** |
| Replay osservato e holdout G14/G15 | **BLOCCATO** |
| Attestazione esterna del timestamp della fonte | **NON VERIFICATA** |
| Promozione in produzione/GOLD | **BLOCCATA** |

Il generatore rifiuta PRELOCK_JOINT_MODEL_OUTPUT perche una dichiarazione di calibrazione non deve essere falsificata. L'esecuzione demo e sempre SYNTHETIC_UNIT_TEST. Gli SHA256 dell'input individuano cambiamenti nei file, ma non autenticano l'origine delle fonti.

### Calcolo dimostrativo

Fantavoto = voto puro + 3*gol + assist - 0.5*giallo - rosso - gol_subiti_portiere + clean_sheet_portiere. Si tratta di un **sottoinsieme** del contratto punteggi della lega. I gol di calciatori esterni alle due rose sono rappresentati dal bucket OTHER.

L'output **non** va confuso con una previsione calibrata, e non e una prova G05/G14/G15 completata.
