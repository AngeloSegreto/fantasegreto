# FantaSegreto V3.3.1 · Fase 1 P0, shadow only

La specifica V3.3.1 è immutabile; questo codice è un candidato locale di sviluppo. Non è il simulatore Monte Carlo completo e non va usato per formulare una formazione certificata.

Contenuti implementati e testati localmente:

- `league_config.yaml`: bozza versionata, goal thresholds da screenshot certificato, regole non certificate marcate `MANCANTE`/`PROVVISORIA`.
- `league_config.schema.json`: schema preliminare; NON copre ancora tutti i requisiti semantici di G20.
- `fs_p0_core.py`: goal mapping con Decimal senza tetto, verifica SHA-256 dello screenshot, hash deterministico della decisione completa (panchina ordinata), PCG64 per atleta/scenario, blocco della promozione in assenza di regole.
- `fs_decision_protocol.py`: confronto Monte Carlo appaiato per profilo primario con margine δ e intervallo di confidenza; registro pre-lock append-only con catena di hash, verifiche temporali e verifica manomissioni.
- `tests`: test di confini, monotonia, permutazioni, regole mancanti, conclusività, spareggio e registro.

## Test

Dalla cartella `phase1_baseline`:

```bash
python -m unittest discover -s tests -v
```

Risultato rilevato il 18 ottobre 2026: **21/21 PASS** (cfr. `../phase0/TEST_EXECUTION_LOCAL.log`). Separatamente, pacchetto Goal Lock V3.1 esistente: **29/29 PASS** (cfr. `../phase0/TEST_GOAL_LOCK_V3_1.log`).

## Gate ancora aperti

G00–G22 NON complessivamente validati; in particolare mancano: full scoring con modificatore/capitano ufficiali, golden replay piattaforma, benchmark tempo/fallback, archiviazione integrale per replay decisionale, gestione scritture concorrenti del registro, fonti pre-lock firmate, calibrazione G14 e rolling origin G15, parità XLSX/PWA e dispositivo iPhone.

Un intervallo Monte Carlo stretto riguarda l'incertezza numerica, non la bontà del modello. `STAT VALIDATED = false`; `GOLD LOCK = false`. L'incumbent di produzione resta intatto.
