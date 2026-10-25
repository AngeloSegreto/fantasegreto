# FantaSegreto V3.3.1 — Fase 0: matrice di conformità

La matrice è compilata sul commit remoto `2122699104f8923eb65d9f4c7491d4bcf48306f2`, branch `feature/fs-match-win-v3-2`, PR #6 in bozza. `main` resta a `fa9562decb683a3d64ca248cb66ff20099ddcb54`. Il checkout locale ispezionato ha un commit diverso ma lo stesso albero Git `949ca62d8a62fddb2999dd00844d6a6139dbfc34`; questa uguaglianza è verificata in `inspection.json` e nel readback remoto.

**Esito della consegna:** 37 requisiti, nove colonne. Un requisito VERIFICATO nel perimetro dello snapshot ufficiale corrente, 31 PARZIALMENTE IMPLEMENTATO, cinque NON IMPLEMENTATO. Tutti gli ID G00–G22 sono presenti. Gli alias ai precedenti G0–G19 sono espliciti; nessun report precedente viene riscritto.

La Fase 0 è completata come censimento. Non sono conseguiti TECH PASS della V3.3.1, STAT VALIDATED o GOLD LOCK. Il PASS della validazione del CSV riguarda forma e tracciabilità dell'artefatto, non la conformità del motore. I test verdi V3.2 mantengono il proprio perimetro e non chiudono i nuovi requisiti.

## File principali

- [Matrice leggibile](MATRICE_CONFORMITA_V3_3_1.md).
- [Matrice CSV UTF-8](MATRICE_CONFORMITA_V3_3_1.csv), con le stesse nove colonne.
- `inspection.json`: ambiente, controlli rieseguiti, integrità dei nove asset protetti e manifest delle run V3.2.
- `probes.json`: sonde nuove con i risultati sfavorevoli conservati.
- `matrix-summary.json` e `matrix-validation.json`: conteggi, copertura e controlli dell'artefatto.
- `source-receipt.json`: fonte normativa ricevuta e hash delle trascrizioni archiviate.
- `manifest.json`: hash dei file della consegna; è integrità SHA-256, non firma digitale né ratifica dell'auditor indipendente.

## Controlli effettivamente rieseguiti

Cinque gruppi, tutti conclusi con exit code zero:

1. 23 test Node del candidato V3.2.
2. Contratto del simulatore legacy.
3. 28 controlli dello scoring legacy.
4. Validatore runtime ufficiale: 539 identità.
5. Validatore di parità dello snapshot ufficiale.

I log e i rispettivi hash sono riportati per ogni riga applicabile. Nessun download di browser, servizio cloud a consumo o API a pagamento è stato attivato in questa Fase 0. Il test fisico Safari/iPhone non è stato eseguito; il precedente blocco del browser rimane evidenza storica, non un nuovo test di layout.

Le nuove sonde hanno rilevato:

- **Ordine dei giocatori:** con gli stessi dati, seed 20261018 e 2.000 scenari, invertire i record cambia la prima probabilità da 0,3555 a 0,336. È un difetto rispetto all'invarianza deterministica richiesta; non dimostra da solo un bias della distribuzione.
- **Ordine delle candidate a pari punteggio:** la prima etichetta selezionata passa da A a B invertendo l'array. Lo spareggio attuale dipende dall'indice.
- **Regola mancante:** capitano nullo blocca correttamente la simulazione; zero scenari e `gold:false`.
- **Soglie:** i punti di controllo da 65,9 a 102 danno i gol attesi, ma il codice usa ancora costanti 66/4 e Number binario. G08 è quindi parziale rispetto alla V3.3.1, anche con i test V3.2 superati.

## Fonte normativa e omissioni tracciate

La V3.3.1 è stata ricevuta nel messaggio dell'utente, non come file nativo allegato. `specification-received.txt` trascrive il segmento intitolato Master Prompt V3.3.1; `ratification-clarifications.md` conserva un riepilogo esplicitamente identificato delle clausole del preambolo. I loro hash non sono presentati come hash del messaggio originale o come firma del CTO.

Il segmento canonico annuncia ma omette tabella del confronto, campi dell'identità, formula delle soglie e intestazioni della matrice. Il preambolo consente di ricostruire parte dei requisiti e lo schema a nove colonne. Le omissioni restano nel rilievo DOC-SPECIFICA; il testo ricevuto non viene corretto silenziosamente. I percorsi e l'hash illustrativi del preambolo non sono stati usati come evidenze.

La fonte V3.3 precedente è sostituita dall'ultimo testo. I temi P1 menzionati soltanto nella base sostituita sono censiti come contesto da confermare, non promossi a nuovi requisiti vincolanti. Nessuna nuova funzione concettuale è stata aggiunta.

La configurazione ufficiale della lega è ancora assente. L'attuale segnale `rules.verified:true` non prova da solo che la fonte sia certificata. Modificatore, capitano, eccezioni SV, assegnazione punti e moduli ammessi richiedono le evidenze della piattaforma. Questi dati mancanti non vengono inventati.

## Chiusure operative già autorizzate per la Fase 1

1. Configurazione con schema, provenienza e stato per regola; scoring esatto e soglie fuori dal codice.
2. Due profili e confronto statistico ratificato, identità completa, normalizzazione e casualità coerente con gli eventi condivisi.
3. Budget principale/ripiego/pubblicazione e percorso manuale quando manca un ripiego verificato.
4. Registro delle decisioni e replay del contenuto decisionale separato dai metadati operativi.

I test negativi devono chiudere i difetti rilevati. Golden ufficiali completi, validazione predittiva, parità Excel/PWA e prova iPhone rimangono gate aperti: la consegna della matrice non li risolve.

## Ripetizione dell'ispezione

Dalla root del repository, su una copia del commit ispezionato e di questa directory di audit:

```bash
python3 audit/v3_3_1_phase0/inspect.py
node audit/v3_3_1_phase0/probes.js
python3 audit/v3_3_1_phase0/build_matrix.py
```

Gli script scrivono soltanto i report di questa ispezione; non modificano l'engine o le run pre-match congelate. Tempi e metadati dell'ispezione possono differire e il manifest va rigenerato per una nuova consegna. La matrice include valutazioni manuali ancorate al commit: su codice diverso devono essere riesaminate, non certificate automaticamente dal generatore.
