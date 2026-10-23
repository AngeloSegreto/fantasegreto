# FS FANTASEGRETO V3.3.1 — G8 Paired Scenario Comparator
**STATO: SHADOW/PROVVISORIO, NON UTILIZZARE PER INVIARE LA FORMAZIONE.**

## Cos'è stato implementato
`prelock_scenario_compare.py` confronta intere decisioni (11 titolari, panchina **nell'ordine esatto**, capitano e vice) per **4-3-3, 4-4-2 e 3-5-2**. L'elenco completo dei 25 giocatori è quello della lega, riconciliato con il registry del 13 ottobre. Il calendario G8 registra il vero avversario di Serie A per ciascun atleta e il primo calcio d'inizio il 23 ottobre alle 20:45 CEST.

Ogni record di scenario contiene **un solo stato per ciascuna delle 10 partite**, con esito e gol di casa/trasferta. Ogni giocatore fa riferimento alla partita effettiva tramite `fixture_ref`. TUTTE le candidate utilizzano lo stesso valore di `scenario_id`, gli stessi eventi dei giocatori e lo stesso risultato dell'avversario di fantacalcio. Non si rigenerano numeri casuali per un modulo differente. Il filtro strutturale vieta giocatori senza fixture e campionamenti indipendenti privi di `fixture_ref`.

Il punteggio di ciascuna candidata passa per l'engine comune della lega: Traditional fino a cinque cambi di pari ruolo, fattore capitano/vice su voto puro, bonus del modificatore difesa e soglie 66/4. Il confronto distingue `PUNTI_ATTESI = 3P(V)+P(N)` e `MAX_VITTORIA = P(V)`. Gli intervalli Monte Carlo sono calcolati dalla **differenza appaiata per scenario**, con alpha/delta pre-registrati e bootstrap deterministico. Solo un risultato **EQUIVALENTE ENTRO DELTA** attiva lo spareggio secondario; un confronto INCONCLUDENTE non sacrifica il criterio primario stimato.

`G11`: per confrontare **Meret/Gollini** basta candidare decisioni che differiscono per portiere e usare gli stessi scenari di Napoli–Roma. **Svilar** può essere valutato soltanto con uno stato di disponibilità prima del lock, senza presumerne il rientro.

## Prerequisiti reali ancora mancanti

1. **Avversario della nostra squadra nell'8ª giornata di National League**, con rosa, titolari, panchina ordinata e capitano/vice documentati prima del lock. Non si può riutilizzare AC DENTI della 7ª giornata.
2. **Generatore congiunto di scenari**, documentato e pre-registrato, che produca per tutti i giocatori dei due fantateam voto puro, fantavoto, stato di voto e `fixture_ref` nello stesso scenario. Ogni partita vera deve essere campionata **una sola volta**. Non è sufficiente elencare i nomi dei dieci incontri.
3. **Distribuzioni previsionali reali** con fonti e orari, statistiche, calendario, forza dell'avversario di Serie A, disponibilità, rigoristi, XI previsti, correlazione tra bonus e gol subiti. Nessuno di questi parametri viene inventato dal comparatore. Il file accetta scenari già prodotti dal generatore; **non genera né calibra** probabilità di gol o voto.
4. **Moduli ammessi e Classic** nel `league_config.yaml` sono tuttora PROVVISORI. Il real-mode respinge la promozione di tali dati a fonte certificata, anche quando uno scenario è presente.
5. Evidenze temporali e SHA256 di input e modello; prova indipendente della ricezione prima del vero lock della lega, non solo una data autocertificata dal programma.

## Comando

```bash
python experimental/fs_v331/prelock_scenario_compare.py \
  --roster experimental/fs_v331/data/mall_dealer_roster_20261019.json \
  --calendar experimental/fs_v331/fixtures/md08_serie_a_2026_27.json \
  --config experimental/fs_v331/league_config.yaml \
  --candidates /percorso/decisioni_v331_prelock.json \
  --protocol /percorso/protocollo_preregistrato.json \
  --opponent /percorso/avversario_reale_g8.json \
  --scenarios /percorso/scenari_congiunti_g8.json \
  --output /percorso/risultato_shadow_g8.json
```

Senza avversario/scenari, il comando stampa `BLOCKED_OPPONENT_G8_FANTASY_LINEUP_MISSING` o `BLOCKED_NO_PRELOCK_JOINT_SCENARIOS` con exit code 3. Con input reali ma configurazione non certificata, blocca con `ALLOWED_FORMATIONS_STILL_PROVISIONAL`. Non crea o carica previsioni automaticamente.

Le unit-test usano un avversario **fittizio** e 24 scenari **sintetici** per verificare scoring e confronto statistico, etichettati `SYNTHETIC_UNIT_TEST`. In tali test il modulo numericamente più conveniente NON è una raccomandazione per la vera G8.

## Limiti e Gate
- **G05 NON VERIFICATO**: `fixture_ref` prova la *coerenza delle identità delle partite*, ma non che il generatore sia coerente con tutti i marcatori, gli assist e le reti subite. Serve una verifica a livello eventi.
- **G14/G15 NON VERIFICATI**: un intervallo Monte Carlo misura errore del campionamento, non la calibrazione predittiva di partite future.
- **G03/G04 NON CHIUSI**: moduli certificati e indisponibilità reali devono essere confermati dalle fonti.
- **G21 NON CHIUSO**: confronto deterministico di scenari forniti non equivale al replay dell'intero modello generatore.
- `usable_for_lineup_submission=false`, `TECH_PASS=false`, `STAT_VALIDATED=false`, `GOLD_LOCK=false`.

**Principio antifuga:** la G7 può essere usata come diagnostica postmatch e test storico; i fantavoti già conosciuti della G7 non devono entrare come scenari osservati del 23 ottobre senza un modello temporalmente preregistrato.
