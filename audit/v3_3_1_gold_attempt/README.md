# Tentativo di chiusura GOLD — 18 ottobre 2026

**Esito misurato: GOLD_LOCK_BLOCKED. TECH PASS V3.3.1 = NO; STAT VALIDATED = NO.**

Il commit candidato esaminato è ae33e0df56dc2d048265db4983125707224b2bb7,
albero 80fcd072ea657f03731533cbfff38d110b1f3ad7. L'audit e i suoi test sono
aggiunte successive a quel candidato, non una certificazione retroattiva.

## Lavoro eseguito

- Rieseguiti sette gruppi: 10 nuovi test del controllo evidenze, 21 test Python
  della baseline, 23 test Node V3.2, contratto legacy, 28 controlli scoring e due
  validatori ufficiali. Tutti i gruppi hanno exit code zero.
- Verificati nove file protetti contro main fa9562decb683a3d64ca248cb66ff20099ddcb54:
  contenuto identico. Nessuna modifica di engine o dashboard in questa consegna.
- Aggiunto un controllo di ammissibilità del dossier: gate mancanti o duplicati,
  scope d'asta, albero Git diverso, assenza di revisore o evidenza manomessa
  bloccano l'idoneità alla revisione di rilascio. Per G14/G15 sono richiesti
  anche protocollo pre-registrato, dataset fuori campione e report misurato.
- Conservati log, dossier e report macchina. Il dossier non inventa attestazioni
  PASS a partire da test parziali della matrice precedente.

Il controllo valuta la completezza documentale e i riferimenti; non autentica
crittograficamente il revisore, non dimostra la verità del contenuto dei report
e non è un sistema di certificazione statistica. Persino un dossier completo
produce ELIGIBLE_FOR_RELEASE_REVIEW, non GOLD o promozione automatica.
È una CLI di audit: non è ancora collegata a un percorso operativo di deploy.

## Bloccanti esterni e lavoro ancora aperto

| Gate | Evidenza necessaria |
|---|---|
| G09 | Regola ufficiale del modificatore: eleggibilità, portiere, voti puri, soglie e bonus, inclusi casi di sostituzione. Il YAML ricevuto riporta MANCANTE. |
| G10 | Formula ufficiale capitano/vice, fasce e trattamento SV. Il YAML ricevuto riporta MANCANTE. |
| G14 | Protocollo e soglie pre-registrati, previsioni congelate e risultati osservati fuori campione, report di calibrazione contro baseline. |
| G15 | Rolling backtest con dati effettivamente disponibili alla decisione e miglioramento misurato con incertezza; non un replay con informazioni future. |
| G16 | Giornate complete ufficiali con XI, panchina, voti, bonus/malus, sostituzioni e totali di entrambe le squadre. I sette valori G7 da soli non bastano. |
| G13/G17/G18 | Pipeline completa con budget/ripiego verificato, parità di scoring Excel/PWA e accettazione su iPhone. |

Le soglie 66/4 sono supportate dallo screenshot ricevuto; ciò non certifica
modificatore e capitano. Il contratto storico di asta caricato dall'utente
impedisce già di chiamare GOLD una release con blocking FAIL/PENDING; non
certifica il modello partita. Nessun attestato completo G00–G22 è disponibile
nel dossier attuale; ciò non significa che ogni funzione sia assente.

Non è possibile costruire osservazioni future o previsioni passate congelate
oggi. Se manca uno storico utilizzabile, G14/G15 richiedono nuove giornate in
shadow. Aumentare le simulazioni sintetiche non chiude questi gate.

## Riproduzione

Con le dipendenze della baseline disponibili (NumPy, PyYAML, jsonschema):

```bash
python audit/v3_3_1_gold_attempt/run.py
```

Il runner restituisce zero quando i controlli software circoscritti passano;
questo non è il verdetto GOLD. Per il controllo bloccante del dossier:

```bash
python tools/audit_match_win_gold.py --root . \
  --dossier audit/v3_3_1_gold_attempt/dossier.json \
  --reviewed-tree 80fcd072ea657f03731533cbfff38d110b1f3ad7 \
  --output audit/v3_3_1_gold_attempt/GATE_CHECK.json
```

Quest'ultimo comando restituisce **2** con il dossier attuale. L'output
GOLD_READINESS.json contiene gli esiti e i motivi aperti per ciascun gate.
manifest.json identifica i file di questa verifica, non è una firma digitale.
