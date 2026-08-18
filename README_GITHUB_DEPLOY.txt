FANTASEGRETO V4.1.8.2 — ENGINE PARITY + STATE HARDENING
FS NEWS Intelligence V2 cutoff: 18/08/2026 19:45 Europe/Rome

TARGET
GitHub Pages: https://angelosegreto.github.io/fs-control-room/
Test anti-cache: https://angelosegreto.github.io/fs-control-room/?v=4182

DEPLOY
Caricare/SOSTITUIRE TUTTI i file contenuti nel pacchetto GITHUB_ROOT_DEPLOY direttamente nella root del repository.
Non rinominare index.html, sw.js, registry.json, player-details.json o FS_NEWS_INTELLIGENCE_V2_DELTA_20260818_1945.json.
Mantenere anche .nojekyll e version.json.

COSA CAMBIA
- State Manager unico e namespaced: fantasegreto:* / FS_STATE_V2.
- Migrazione una tantum dalle chiavi legacy con validazione semantica; le vecchie chiavi restano preservate come recovery evidence.
- Backup V3 atomico: state + history + future + LKG, SHA-256 e registry fingerprint.
- Exact MAX usa la lineage V4.0.23.1 con MOD difesa, clean-sheet, opponent pressure, cost of pass e pivot.
- Il vecchio Shadow V4.0.10 viene conservato come shadow_raw diagnostico, ma NON può più esplodere: uplift operativo <= min(8 crediti, 8% del MAX MOD+CS).
- Decisione/instruction LIVE vengono generate dall'Exact MAX runtime, non dal vecchio testo statico del registry/detail.
- Service Worker elimina solo cache appartenenti a FantaSegreto / vecchio fs-control-room, non cache generiche dell'origine.

FS NEWS 18/08 19:45
- Vicario: CANONICAL ADD Juventus · P · QI 16 · FVM 55. Base registry 492 resta congelato; runtime effettivo = 493.
- Di Gregorio: Juventus · QI 9 · FVM 10 · backup risk HIGH · hard safety cap derivato.
- Lucumì: canonical team NON riscritto in questo delta; resta Bologna. Juventus = tactical context. Overlay +0,45 FS e +4% MAX conservativo.
- Kelly L.: Juventus · QI 5 · FVM 10 · ballottaggio medio · -0,4 FS e -7% MAX conservativo.
- Canonical registry writes = 1. Calibration writes = 0.

IMPORTANTE SUI VALORI DERIVATI
QI/FVM sopra citati sono dati sorgente del delta fornito e verificato.
FS Score / Ideal / MAX di Vicario e il repricing di Di Gregorio sono MODEL-DERIVED tramite bridge trasparente per ruolo/FVM: non vengono presentati come dati Fantacalcio.

EVIDENZE V4.1.8.2
- base registry 492, effective registry 493
- 0 ID HTML duplicati
- JavaScript syntax PASS
- State/Engine smoke PASS
- Legacy migration smoke PASS
- Backup checksum/tamper smoke PASS
- 5 aste complete deterministiche = 1.250 transazioni, 6.525 assertion, 0 failure
- Shadow guard verificato su tutti i giocatori valutabili

NON GOLD
La release è RC. Restano bloccanti:
1) Physical iPhone/Safari acceptance;
2) Current-engine certified temporal real-auction replay;
3) Full Golden Stress recertification della build corrente (il vecchio 3.000/750.000 resta evidence della lineage, non closure della nuova build 493 + Shadow Guard).

NOTE
I 237 vecchi testi detail con range statici invertiti e 3 instruction vuote restano nel payload legacy, ma V4.1.8.2 non li usa operativamente: la sheet mostra l'istruzione generata dall'Exact MAX runtime. La bonifica fisica del payload è pianificata in V4.1.8.4 DATA & DECISION INTEGRITY.
