# FantaSegreto | Registro KILL CRITIC — Thorstvedt vs Pobega
Data decisione: 2026-10-08 (pre 6ª giornata). Data registrazione: 2026-10-12.
Stato: FAIL METODOLOGICO / SAFE MODE / NO GOLD.
Ambito: Mall & Dealer; audit formazione 4-4-2 e algoritmi Premium PRO 1/2/3.

## Decisione originale
XI: Svilar; Zortea, Dimarco, Solet, Wesley; Moreira, Modrić, Ekkelenkamp, Thorstvedt; Kolo Muani, Maldini.
Pobega in panchina.

## Evidenze e limiti
Lo script Python fornito per lo snapshot dell'8 ottobre include Thorstvedt (C, FM 5.8, probabilità di voto 0.85, 5 partite), ma NON include Pobega nel dizionario U. Quindi le formazioni candidate non potevano selezionarlo. Questa è una constatazione direttamente verificabile sul codice, indipendente dal risultato successivo.
Nell'audit conversazionale sono state riferite fonti precedenti alla gara: Thorstvedt 221 minuti in cinque presenze e due titolarità al 2 ottobre; Pobega in ballottaggio 60/40 con Moro il 7 ottobre. Questi dati richiedono conservazione dei documenti originali, URL, timestamp e verifica prima di diventare evidenza certificata.
Risultato riportato dopo la gara: Pobega ha ottenuto più fantapunti di Thorstvedt. I fantavoti ufficiali esatti non sono ancora riconciliati. Non usare il risultato ex post come prova che la scelta alternativa fosse ottimale ex ante.

## Verdetto
FAIL metodologico accertato: universo dei candidati incompleto.
Possibile errore secondario: sottostima del rischio di minutaggio/titolarità di Thorstvedt.
NON ACCERTATO: un ottimizzatore corretto avrebbe necessariamente schierato Pobega.

## Invarianti per Premium PRO
1. ROSTER_COMPLETENESS_GATE: tutti i tesserati eleggibili, titolari e riserve, devono entrare nel pool di valutazione; se mancano, BLOCKED.
2. TEMPORAL_INTEGRITY: congelare data/ora e fonti disponibili alla decisione; vietato usare risultati successivi per la previsione.
3. MINUTES_VOTE_SPLIT: stimare separatamente probabilità di partire titolare, minuti >=15 e voto ufficiale, rispettando le eccezioni del provider.
4. SAME_ROLE_BENCH: fino a cinque sostituzioni automatiche, nello stesso ruolo, seguendo l'ordine della panchina.
5. DIRECT_COMPARISON: confronto omogeneo tra tutti i candidati per ruolo, con fonti e incertezze esplicite.
6. COUNTERFACTUAL_AUDIT: calcolare scarto ex post e decisione controfattuale usando solo dati ex ante.
7. LEAGUE_RULES: applicare soglie gol, modificatore difesa sui voti puri e fattore capitano, senza proxy incompatibili.
8. NO_DOUBLE_COUNT: non sommare bonus gol già inclusi nella fantamedia.
9. NO_FABRICATED_PROBABILITIES: probabilità di vittoria solo dopo calibrazione, validazione e controlli sui dati.
10. GOLD_LOCK: nessuna modifica a BUY/STOP/MAX o al motore GOLD senza audit e test.

## Follow-up
Acquisire fantavoti ufficiali MD6 Pobega/Thorstvedt; recuperare e archiviare le fonti prepartita con timestamp; eseguire replay congelato all'8 ottobre e test di completezza roster; testare PRO 1/2/3 contro AC DENTI.
