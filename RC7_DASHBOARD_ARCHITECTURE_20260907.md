# FantaSegreto V3.9.6 RC7 — FULL DASHBOARD ARCHITECTURE

## Obiettivo
Unificare la dashboard RC6 BUY DEPTH + 2 PIVOT con l'intera struttura operativa FantaSegreto già presente nel repository, senza duplicare l'engine e senza retrocedere i dati correnti.

## Moduli da preservare dal Control Room legacy
- Asta live con transazioni VINTO/PERSO atomiche
- Budget residuo, slot 3P/8D/8C/6A, lega residua 10x500
- Remaining Pool
- Manager avversari e opponent pressure
- Rosa personale
- Piano 25
- Backup / restore / undo / redo
- Audit / regression / release metadata
- PWA / localStorage state hardening

## Moduli RC7 correnti
- Registry 07SEP: 531 giocatori
- Market500
- FOS V2
- Risk
- MAX LIVE
- BUY / WATCH / PASS
- BUY DEPTH
- 2 PIVOT ENGINE
- Medical overlay 07SEP
- Ricerca e filtri ruolo/decisione

## Miglioramenti mutuati da repository pubblici 2026, adattati a FantaSegreto
### Da Miramira-hub/fantahq
- Budget strategy per reparto + piano B
- Auction ledger con ricerca per giocatore o manager
- Svincolo con rimborso configurabile
- Formazione/availability relativa alla giornata
- Validazione nomi nel builder
- VORP / prezzo atteso separato dal tetto d'asta
- Nuovi arrivi non penalizzati per gare che non potevano giocare
- Medical status distinto da fragilità storica

## Regole architetturali
1. Un solo engine autorevole.
2. Source != Derived != Decision.
3. Medical aggiorna Availability/Risk/MAX, non Market500.
4. FOS V2 canonico non viene modificato dal BUY DEPTH.
5. Pivot devono essere stesso ruolo e preferibilmente stessa fascia o più economici.
6. Le transazioni live devono aggiornare budget, slot, scarcity, opponent pressure, pivot e MAX LIVE.
7. Tutti i dati devono sopravvivere a refresh e reinstallazione PWA tramite stato versionato.
8. Nessun GOLD con gate bloccanti.

## Roadmap UI RC7
Tab principali:
1. Asta
2. Listone
3. BUY Board
4. Rosa
5. Manager
6. Piano 25
7. Medical
8. Performance
9. Movimenti
10. Audit

## Gate
- REGISTRY_531_PASS
- MEDICAL_07SEP_PASS
- BUY_DEPTH_PASS
- PIVOT_2_PER_PLAYER_PASS
- LEGACY_ENGINE_PARITY_PENDING
- MATCHDAY3_FINAL_PENDING
- PERFORMANCE_REFRESH_PENDING
- STATE_MIGRATION_PENDING
- PWA_CACHE_MIGRATION_PENDING
- REGRESSION_PENDING
- RELEASE_SEAL_BLOCKED
