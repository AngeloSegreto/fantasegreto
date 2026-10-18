# Regole acquisite dagli screenshot del 18 ottobre 2026

I sei file forniti dall'utente sono presenti e leggibili; l'errore iniziale
di percorso non persiste. Le immagini sono archiviate senza modifiche.
`transcription.json` conserva i parametri visibili, provenienza e SHA-256;
`league_config.yaml` è la configurazione corrente, in sintassi JSON valida YAML 1.2.
La configurazione dentro il pacchetto importato resta una ricevuta storica immutata.

## Dati verificati visivamente

- Soglie: primo gol 66, fasce fisse di quattro punti; 94 vale otto gol.
- Sostituzioni: cinque, tipo Traditional, riserva d'ufficio disattivata.
- Modificatore attivo, almeno quattro difensori nella formazione effettiva
  dopo le sostituzioni; portiere incluso con i tre migliori difensori;
  voti puri; bonus alla propria squadra.
- Media difesa: sotto 6,25 bonus zero; da 6,25 bonus 0,5; da 6,5 bonus 1;
  da 6,75 bonus 1,5; da 7 bonus 2.
- Sei politici validi come 6; SV ammoniti come 6 soltanto se validati
  dall'apposita opzione. L'attivazione di tale opzione non è mostrata.
- Capitano attivo: voto <=4,5 dà -1,5; 5 dà -1; 5,5/6/6,5 danno 0;
  7 dà +1; >=7,5 dà +1,5. Il vice interviene se il capitano non va a voto.
  Nessun raddoppio di bonus o malus; designazione partita per partita.
- Bonus/malus visibili: gol subito -1; rigore segnato +3; sbagliato -2;
  parato +3; giallo -0,5; rosso -1; assist standard +1, soft +0,5,
  gold +1,5; autogol -2; gol pareggio/vittoria 0; imbattuto +1; POTM 0.

## Implementazione verificata e limiti

`experimental/match-win-v3_2/league-rules.js` legge i parametri della configurazione
ricevuta come argomento. Calcola media difesa e confronti con aritmetica razionale
BigInt da stringhe decimali, senza arrotondamento binario. Gestisce le fasce
capitano mostrate e il passaggio al vice. Non assume regole per voti capitano
non elencati, entrambi SV o portiere SV: questi casi richiedono una regola esplicita.
Non abilita automaticamente l'opzione SV ammonito. I casi noti sono coperti da
32 test, inclusi confini, esclusioni e hash dei sei screenshot.

Il modulo è un componente del candidato in shadow, non è ancora collegato a
`core.score` o alla simulazione continua V3.2. Non sostituisce la produzione e
non chiude la validazione completa G09/G10: restano integrazione, eccezioni e
golden replay. La fonte dei parametri principali G09/G10 non è più mancante.

La parte alta della pagina bonus/malus non è visibile: il normale bonus gol
non viene certificato da questa immagine. Il tipo Traditional è trascritto
senza dedurre clausole non mostrate. Il nome della lega deriva dalla conversazione,
non è leggibile nei ritagli. La data di ricezione non è una prova pre-lock
per giornate già trascorse. Le vecchie matrici e i vecchi report restano snapshot
storici; questo documento ne aggiorna la disponibilità delle fonti.

**GOLD LOCK resta NO:** G14/G15 e gli altri gate operativi non sono chiusi da
queste immagini. Test tecnici del componente != accuratezza predittiva.

## Riproduzione

```bash
node --test experimental/match-win-v3_2/league-rules.test.js
```

Per rigenerare l'archivio dai sei originali: eseguire
`python tools/import_league_screenshots.py --source-directory /percorso/originali`.
