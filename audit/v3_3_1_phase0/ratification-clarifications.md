# Clausole integrative ricevute nello stesso messaggio

Questi estratti sono trascritti dal preambolo del messaggio dell'utente del 18 ottobre 2026, ore 22:14:41 Europe/Rome. Completano i punti annunciati ma omessi nel segmento intitolato "Master Prompt V3.3.1 (Canonico)". Non sono un file originale allegato né una nuova ratifica.

## Contratto statistico riportato nel preambolo

| Condizione | Verdetto Statistico | Azione Decisionale / Spareggio |
|---|---|---|
| L > +δ | A SUPERIORE | Raccomanda A (superiorità dimostrata oltre il margine). |
| U < -δ | B SUPERIORE | Raccomanda B (superiorità dimostrata oltre il margine). |
| [L, U] ⊆ [-δ, +δ] | EQUIVALENTI ENTRO δ | Le formazioni sono equivalenti nel criterio primario. Applica gli spareggi: criterio secondario, minore P(Sconfitta), continuità con input attuali, spareggio canonico. |
| Tutti gli altri casi | INCONCLUDENTE | Scegli la candidata con la stima puntuale maggiore del criterio primario; etichetta CONFRONTO INCONCLUDENTE. |

## Identità completa riportata nel preambolo

- Titolari: vettore degli ID univoci degli undici giocatori, ordinato canonicalmente.
- Panchina: vettore degli ID nell'ordine operativo esatto.
- Capitano: ID univoco.
- Vicecapitano: ID univoco.
- La run collega l'identità a giornata, versione della configurazione, profilo attivo e hash degli input normalizzati.

## Budget riportato nel preambolo

Il timeout del principale è fissato a T_disponibile meno T_ripiego_stimato e T_pubblicazione_garantito. Se manca un ripiego verificato e compatibile, stato RIPIEGO NON DISPONIBILE e intervento manuale.

## Schema a nove colonne riportato nel preambolo

ID Requisito; Fonte Normativa; Codice Esistente; Test Presenti; Evidenza / Hash; Stato; Lacuna Rilevata; Criterio di Chiusura; Dipendenza di Promozione.

## Note di ricezione

- Gli esempi `src/scoring.py`, `tests/test_g8.py` e `e3b0c442...` del preambolo sono illustrativi: non sono usati come prove del repository.
- Il preambolo usa in un esempio lo stato MANCANTE, escluso dal vocabolario finale. La matrice usa NON IMPLEMENTATO.
- L'ultimo testo integrale dichiara di sostituire le versioni precedenti. La V3.3 allegata resta contesto storico; non viene promossa a fonte prevalente per riempire omissioni.
- L'hash di queste trascrizioni identifica i byte archiviati da questo audit, non un inesistente file nativo V3.3.1 fornito dall'utente. Non costituisce firma digitale né prova di esistenza prima del lock.
