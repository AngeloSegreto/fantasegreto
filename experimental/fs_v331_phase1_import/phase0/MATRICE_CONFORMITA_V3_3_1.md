# FASE 0 — MATRICE DI CONFORMITÀ DEL REPOSITORY

**Norma:** FS FANTASEGRETO Master Prompt V3.3.1 (18/10/2026).
**Repository principale:** [AngeloSegreto/fantasegreto](https://github.com/AngeloSegreto/fantasegreto).
**Ref verificata:** `main` / `fa9562decb683a3d64ca248cb66ff20099ddcb54`.
**Repository PWA accessorio:** [AngeloSegreto/fs-control-room](https://github.com/AngeloSegreto/fs-control-room), ref `fe8a302200592e2e6964e28a67256d4c1ebe1470`.
**Metodo:** GitHub connected read-only listing ricorsivo e lettura codice/test; test locali eseguiti sul pacchetto V3.1, non sul checkout GitHub (rete GitHub non disponibile in container).
**STATUS:** audit di prima passata, non firmato dall’auditor indipendente e non certificazione di produzione.

| ID Requisito | Fonte Normativa | Codice Esistente | Test Presenti | Evidenza / Hash | Stato | Lacuna Rilevata | Criterio di Chiusura | Dipendenza di Promozione |
|---|---|---|---|---|---|---|---|---|
| G00 | Source Truth | app.js (registry/news loader); data/FOS_V2_WEB_EVIDENCE_SNAPSHOT_22SEP2026.json | Regressione FOS/registry, non test provenienza completa | app.js a550f30; data/FOS_V2_WEB... (Git blob) | PARZIALMENTE IMPLEMENTATO | Provenienza non garantita per ogni input decisionale | Snapshot grezzo+URL+timestamp per ogni feature e test negativo | P0: G00 |
| G01 | Calendar Integrity | analysis/G7_HYBRID_ROBUST_13OCT2026.md; SEASON_FORMATION_SIMULATION_25SEP2026.json | Nessun test G01 calendar join identificato | analysis/G7... 30f50cc; SEASON... cc4abbb | PARZIALMENTE IMPLEMENTATO | Fixture annotata, non join biunivoco player->club->gara verificato | Fixtures ufficiali e property test su tutte le squadre | P0: G01 |
| G02 | Player Identity | registry.json; app.js; tools/reconcile_listone_13oct.py | tools/validate_13oct_offline.py (test generale) | registry.json 6b7873a; app.js a550f30 | PARZIALMENTE IMPLEMENTATO | Registro d’asta senza prova mapping interfonte per tutte le entità dell’engine partita | Crosswalk ID univoco e test collisione multi-sorgente | P0: G02 |
| G03 | Role & Formation | premium-monte-carlo-v1.js: valida XI 11 ma non tutti i moduli | premium-monte-carlo-v1.test.js verifica lunghezze/bench | premium MC 7688bd0; test 619a5c2 | PARZIALMENTE IMPLEMENTATO | Manca resolver esatto moduli Classic e vincoli di ruolo su tutte candidate | Enumeratore legale completo con fixture negative | P0: G03 |
| G04 | Availability | MEDICAL_V3_22SEP2026.json; analysis/G7... | Nessun test automatico blackout indisponibili prelock rilevato | MEDICAL_V3... file root; analysis 30f50cc | PARZIALMENTE IMPLEMENTATO | Non presente esclusione vincolante per ogni indisponibile ufficiale e override | Validator availability e override append-only testato | P0: G04 |
| G05 | Match Correlation | premium-monte-carlo-v1.js: per-player normal indipendente | Test contratto bloccato, non coerenza eventi | premium MC 7688bd0 | NON IMPLEMENTATO | Nessun simulatore congiunto di risultati, gol, assist, parate | Scenari congiunti con invarianti di partita | P1 subordinato P0: G05 |
| G06 | Probability Domain | premium-monte-carlo-v1.js (win/draw/loss frequencies) | premium test blocco input, nessun test dominio esaustivo | premium MC 7688bd0 | PARZIALMENTE IMPLEMENTATO | Non c’è suite valori estremi + somma esatta/tolleranza dichiarata | Property test P(V)+P(N)+P(S)=1 e bounds | P0: G06 |
| G07 | Substitution Consistency | experimental/scoring-gate-v1.js; premium-monte-carlo-v1.js | scoring-gate-v1.test.js (ordine ruolo, max5, SV) | scoring b00c1b4; test 6a01761 | PARZIALMENTE IMPLEMENTATO | Non replicate tutte le fixture ufficiali e casi limite | Golden di sostituzione per ogni giornata e test regressione | P0: G07 |
| G08 | Goal Threshold Lock | experimental/scoring-gate-v1.js (soglie hardcoded); package locale V3.1 | Test locale package Goal Lock 29/29 PASS (18/10/26) | scoring b00c1b4; evidence screenshot sha256 f2d4860 | PARZIALMENTE IMPLEMENTATO | Nel repo regole hardcoded e calcolo float/epsilon; non è config-based Decimal | Source config verificata, Decimal esatto, 65.9/98 boundaries, parity | P0: G08,G20 |
| G09 | Defensive Modifier | experimental/scoring-gate-v1.js (formula hardcoded) | scoring-gate-v1.test.js (range ipotizzati) | scoring b00c1b4; test 6a01761 | PARZIALMENTE IMPLEMENTATO | Fasce/eligibility non certificate da piattaforma; vietato dichiarare GOLD | Acquisire regola ufficiale + golden nel calcolo scenari | P0: blocco GOLD |
| G10 | Captain Rules | experimental/scoring-gate-v1.js (formula hardcoded) | scoring-gate-v1.test.js (fasce ipotizzate) | scoring b00c1b4 | PARZIALMENTE IMPLEMENTATO | Bonus capitano/vice non certificato, potenziale divergenza piattaforma | Acquisire regola ufficiale e replay golden | P0: blocco GOLD |
| G11 | Keeper Comparison | Pacchetto locale V3 goalkeeper fixture; nessuna integrazione repository | test_gk_v3.py nel package locale, da non attribuire al repo | Zip V3 allegato; commit repo non integrato | PARZIALMENTE IMPLEMENTATO | Non calcolato in formazione completa, regole/modificatore non certificate | Confronto Gollini/Meret su scenari condivisi e XI valida | P1 dopo G05/G09 |
| G12 | No Future Leakage | analysis/G7... contiene note tempo; nessun gate runtime completo | Nessun test automatico timestamp<=lock identificato | analysis/G7... 30f50cc | PARZIALMENTE IMPLEMENTATO | Prelock snapshots e ingress validator non garantiti | Fixture future-data negative + freeze immutabile | P0: G12 |
| G13 | Precisione & Budget | premium-monte-carlo-v1.js (n fisso massimo, seed) | premium test verifica input, non precisione/budget | premium MC 7688bd0 | PARZIALMENTE IMPLEMENTATO | Assenti paired CI, delta, T_principale e fallback verificato | Misura errore MC e timing/fallback sulla macchina riferimento | P0: G13 |
| G14 | Calibration | Nessun artefatto calibrazione esiti o curve nel repo tree esaminato | Nessun Brier OOS calibrato identificato | tree main fa9562decb68 | NON IMPLEMENTATO | Soglie e report statistici pre-registrati mancanti | Brier+curve vs B0/B1, train/test separated | P0 per GOLD: G14 |
| G15 | Temporal Backtest | analysis/G7... è analisi statica, non rolling-origin | Nessun rolling-origin automatico identificato | tree main fa9562decb68 | NON IMPLEMENTATO | Nessuna prova miglioramento fuori campione | Backtest per giornata con asof snapshots certificati | P0 per GOLD: G15 |
| G16 | Golden Regression | REGRESSION_GATE_REPORT.json riguarda asta; scoring test sintetico | experimental/scoring-gate-v1.test.js fixture sintetiche | REGRESSION_GATE_REPORT 856c98f; scoring test 6a01761 | PARZIALMENTE IMPLEMENTATO | Nessuna riproduzione completa totali ufficiali di tutte giornate fantasy | Fixture G1..G7 con fonte indipendente e auditor separato | P0: G16 |
| G17 | Excel/PWA Parity | ENGINE_CONTRACT_V4_0_23_1_PARITY.json riguarda asta | Test parity auction; nessuna parity match-win attestata | ENGINE_CONTRACT a5f4e21 | PARZIALMENTE IMPLEMENTATO | No engine match-win esposto in Excel e PWA con output identici | Golden parity scoring end-to-end su entrambi | P0: G17 |
| G18 | Mobile UI | index.html PWA auction; nessuna decision-first partita | audit PWA esistenti riferiti all’asta | index.html d3bf169; app a550f30 | PARZIALMENTE IMPLEMENTATO | Interfaccia partita V3.3.1 assente | UI decision-first su iPhone, test viewport reale | P0: G18 |
| G19 | Release Integrity | CHECKSUMS.txt; SHA256_MANIFEST.json; sw.js; version.json | RC audit e manifests relativi all’asta | version 27a18e3; checksum root esistente | PARZIALMENTE IMPLEMENTATO | Mancano release/rollback test del match engine shadow | Bundle SHA + dry-run rollback + prova disaccoppiamento | P0: G19 |
| G20 | Configurazione Lega | FS_PREMIUM_MATCH_EVIDENCE_V1.json include league_rules incompleti | premium-monte-carlo-v1.test.js controlli fail-closed | match-evidence blob contract; premium test 619a5c2 | PARZIALMENTE IMPLEMENTATO | league_config.yaml certificato, schema, metadati, stati e hash assenti | File schema-compliant + source e hash per regola | P0: G20 |
| G21 | Riproducibilità | premium-monte-carlo-v1.js ha seed RNG (non PCG64) | Nessun replay completo output congelati testato | premium MC 7688bd0 | PARZIALMENTE IMPLEMENTATO | Seed unico di sequenza dipende dall’ordine; nessun archive input/output completo | PCG64 per ID scenario, archive e replay byte-identico | P0: G21 |
| G22 | Registro Decisioni | Asta usa state-manager.js ma non override formazioni | Nessun test append-only prelock identificato | state-manager.js 105c89c | NON IMPLEMENTATO | Nessun registro prelock suggerita vs inserita | Log append-only e test override/no-after-lock | P0: G22 |

## Conteggio

NON IMPLEMENTATO: **4** · PARZIALMENTE IMPLEMENTATO: **19**

## Evidenze puntuali

- [`index.html` boot](https://github.com/AngeloSegreto/fantasegreto/blob/fa9562decb683a3d64ca248cb66ff20099ddcb54/index.html) carica `app.js`, `state-manager.js`, `engine.js` per l’asta. Non carica `premium-monte-carlo-v1.js` nel boot verificato.
- [`engine.js`](https://github.com/AngeloSegreto/fantasegreto/blob/fa9562decb683a3d64ca248cb66ff20099ddcb54/engine.js) espone `FS_AUCTION_ENGINE`, non l’engine match-win V3.3.1.
- [`premium-monte-carlo-v1.js`](https://github.com/AngeloSegreto/fantasegreto/blob/fa9562decb683a3d64ca248cb66ff20099ddcb54/premium-monte-carlo-v1.js) contiene RNG non PCG64, `goal_thresholds.reduce(...)` e ritorna `BLOCKED_SCORING_RULES_UNIMPLEMENTED` per modificatore/capitano attivi.
- [`experimental/scoring-gate-v1.js`](https://github.com/AngeloSegreto/fantasegreto/blob/fa9562decb683a3d64ca248cb66ff20099ddcb54/experimental/scoring-gate-v1.js) usa costanti hardcoded, `Number` e epsilon per le soglie e valori ipotetici per modificatore/capitano.
- [`FS_CERTIFICATION_STATUS_08OCT2026.json`](https://github.com/AngeloSegreto/fantasegreto/blob/fa9562decb683a3d64ca248cb66ff20099ddcb54/FS_CERTIFICATION_STATUS_08OCT2026.json) certifica *SAFE MODE ONLY NO GOLD* nel suo perimetro alla data indicata.
- Le **29 prove locali PASS** appartengono all’allegato Goal Lock V3.1, NON al repository vivo o al motore d’asta.

## Blocchi immediati per GOLD LOCK

- G09 e G10: mancano regole ufficiali verificate con evidenza sufficiente.
- G14 e G15: non è dimostrata calibrazione e superiorità fuori campione.
- G16: non ci sono golden completi di scoring fantacalcio rispetto a risultati ufficiali.
- G20–G22: config canonica, replay integrale e log decisioni sono incompleti/assenti.

**Decisione di audit:** `SHADOW_ONLY / NOT TECH PASS / NOT STAT VALIDATED / NOT GOLD LOCK`. I file dell’incumbent NON sono stati modificati.

## Limiti della verifica

La presenza/assenza è dedotta dall’albero ricorsivo e dai file chiave letti. I test del repository remoto NON sono stati eseguiti; ogni voce VERIFICATO resta quindi preclusa, anche quando il codice mostra funzioni plausibili. Le attestazioni storico-statistiche richiedono auditor e snapshot ufficiali.
