# Importazione autorizzata — 18 ottobre 2026

Pacchetto utente: FS_FANTASEGRETO_V3_3_1_PHASE0_PHASE1_SHADOW(1).zip.
SHA-256 ZIP: b0bf0f455615cdaa55e07cc257f0092948bb203ecf61653c2727ca808615b48d.
I 15 file del pacchetto sono importati senza modifiche; il manifest allegato verifica i 14 payload escluso se stesso. Questo documento e TEST_RERUN_IMPORT_18OTT2026.log sono aggiunte della verifica di importazione.

## Perimetro e provenienza

La matrice allegata riguarda main fa9562decb683a3d64ca248cb66ff20099ddcb54: 23 gate, 19 parziali e 4 mancanti. Non sostituisce la matrice del branch candidato in audit/v3_3_1_phase0 (37 requisiti, perimetro diverso). I log originali e le affermazioni di certificazione sono conservati come documenti ricevuti, non come nuovi verdetti di questo importatore.

Il branch fs-v331-shadow-phase1 esiste a 57e94efc90c5ca05af0fa648333c5914888f0bf4 e contiene un nucleo sperimentale separato. Questa importazione non lo modifica, non lo fonde e non collega moduli al runtime della dashboard.

## Verifica rieseguita

Python 3.12.14; NumPy 2.3.5; PyYAML 6.0.3; jsonschema 4.26.0.
La prima esecuzione nella cartella baseline era bloccata dall'assenza di jsonschema. Installata la dipendenza gratuita in una cartella temporanea isolata, la suite completa ha passato 21 test. Il log aggiunto documenta la nuova esecuzione; i 29 test del precedente Goal Lock sono solo un log ricevuto e non sono stati rieseguiti qui.

Comando dalla cartella phase1_baseline, con dipendenze disponibili:

```bash
python -m unittest discover -s tests -v
```

## Limiti aperti

- SHADOW ONLY: nessuna integrazione nel simulatore V3.2 o nell'engine di produzione; non risolve automaticamente i difetti d'invarianza già rilevati nell'altro candidato.
- Schema preliminare e verifica evidence non automaticamente imposta da load_config: G20 resta aperto.
- Intervallo normale appaiato: non prova copertura valida in piccoli campioni o casi di varianza osservata nulla; nessuna validazione predittiva.
- Registro a singolo scrittore: concorrenza, validazione completa degli override, controllo del tempo affidabile ed autenticità esterna restano da verificare.
- La precisione Decimal dipende anche dal contesto numerico per input estremi; i test coprono il dominio dichiarato, non tutti i numeri rappresentabili.
- Modificatore/capitano ufficiali, replay completo, calibrazione, backtest, budget/ripiego e parity/mobile non chiusi.

TECH PASS V3.3.1 = NO; STAT VALIDATED = NO; GOLD LOCK = NO.
Nessun merge, deploy, modifica main o costo a consumo.
