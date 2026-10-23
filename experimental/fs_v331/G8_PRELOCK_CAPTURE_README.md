# FS FANTASEGRETO V3.3.1 — G8 PRE-LOCK CAPTURE (SHADOW ONLY)

La specifica V3.3.1 resta congelata. Questo è un sottoinsieme operativo P0. Non prevede risultati, non modifica l'engine di asta, non abilita GOLD e non archivia automaticamente le app di terzi.

## Calendario
Fonte pubblica: https://www.legaseriea.it/serie-a/news/quando-si-gioca-anticipi-e-posticipi-fino-alla-12a-giornata

- Serie A 2026/27, 8ª giornata: 23–25 ottobre.
- **Prima partita:** Torino–Monza, venerdì 23/10/2026 ore 20:45 CEST.
- I 10 incontri sono in `fixtures/md08_serie_a_2026_27.json`. Il passaggio dell'ora legale il 25/10 è rappresentato con i relativi offset UTC, non con orari senza timezone.
- **G00/G01 ancora DA VERIFICARE**: il JSON riporta la fonte, ma l'HTML/PDF originale e il mapping di tutti gli ID squadra/giocatore non sono ancora conservati in un archivio indipendente.
- La data effettiva di lock della piattaforma deve essere acquisita; non è certificato che coincida con il calcio d'inizio. L'intake impone `lock_at <= first_kickoff`.

## Operazione reale necessaria (prima del lock)

Servono **file realmente acquisiti prima del lock**, non ricostruzioni: screenshot delle regole e della rosa completa, listone ufficiale con ID, ultima informazione medico/tattica disponibile, configurazione di lega e **output del vero motore** con probabilità V/N/S per candidate, B0 e B1. Le previsioni devono essere già state prodotte dal motore e firmate con codice/commit. Nel solo ramo SHADOW si registrano come sperimentali/non calibrate.

```bash
python experimental/fs_v331/prelock_intake.py \
  --calendar experimental/fs_v331/fixtures/md08_serie_a_2026_27.json \
  --inputs /percorso/reale/md08_inputs.json \
  --config experimental/fs_v331/league_config.yaml \
  --decision /percorso/reale/md08_real_engine_output.json \
  --sources /percorso/reale/md08_sources.json \
  --output /percorso/archive/md08_prelock_immutable \
  --engine-file experimental/fs_v331/p0_core.py
```

`md08_inputs.json` deve contenere: `matchday`, `lock_at` ISO con timezone, `roster` completo P3/D8/C8/A6 con ID e ruoli, `starting_xi` 11 ID, `bench` ordinata, `captain`, `vice`, `module`. L'identità dev'essere coerente con `p0_core.decision_hash`.

L'output del motore deve contenere: `prediction_status:SHADOW_PRELOCK`, `snapshot_source:REAL_ENGINE_OUTPUT`, `generated_at` precedente al lock, `engine_version`, `engine_commit_sha`, `decision_hash`, `model_probabilities` con candidate/B0/B1 e distribuzioni V/N/S che sommano a 1.

`md08_sources.json` è una lista di fonti osservate, ciascuna con `id`, `uri`, `path` del file originale salvato, `kind:OBSERVED`, `observed_at` ISO timezone, `sha256` opzionale per il controllo iniziale. Sono richieste almeno due fonti. È responsabilità della fase di raccolta autenticarne l'origine e l'ora. Un campo `REAL_ENGINE_OUTPUT` auto-dichiarato, da solo, **non certifica** il replay o la calibrazione.

L'acquisizione non avviene se mancano rosa e fonti complete, se il calendario è errato, se il vero lock è passato o se il modello tenta di spacciare risultati sintetici per reali.

## Test

```bash
python -m unittest discover -s experimental/fs_v331 -p 'test_*.py' -v
```

I test usano oggetti artificiali: verificano la logica del software, **non** generano nuove previsioni reali. La corrispondenza delle fonti e dell'algoritmo con l'output resta gate esterno.

## Release

- TECH PASS completo: **NO**.
- STAT VALIDATED su dati fuori campione: **NO**.
- GOLD LOCK: **NO**.
- Merge su main, deploy, sovrascrittura dell'incumbent: **vietati** fino a GOLD LOCK.
