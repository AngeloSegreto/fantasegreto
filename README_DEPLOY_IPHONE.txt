FS CONTROL ROOM V4.1.1.1 — iOS DEPLOYMENT HOTFIX

OBIETTIVO
Correggere il caso visto su iPhone: index.html aperto isolatamente non aveva accesso agli asset relativi.

ARCHITETTURA
- index.html: shell + CSS critico inline (piccolo, nessun monolite dati)
- app.js: UI runtime
- engine.js: Engine V4.0.23.1 LOCK
- registry.json: registry 492
- player-details.json: dettagli on-demand
- sw.js: PWA R8.1
- manifest.webmanifest
- styles.css: copia sorgente del design system; non necessaria al boot perché CSS già inline

IMPORTANTE
NON aprire index.html isolato dall'app File/anteprima per validare il runtime. In file:// la build mostra volutamente un avviso e NON avvia il motore.

DEPLOY GITHUB PAGES
1. Svuota/sostituisci nella root del repository i file runtime con quelli di questa cartella.
2. Mantieni TUTTI questi file nella stessa directory.
3. Commit + deploy GitHub Pages.
4. Apri: https://angelosegreto.github.io/fs-control-room/?v=4111
5. Chiudi eventuale vecchia tab/PWA prima del primo test.

GATE IPHONE
PASS solo se:
- tema scuro Apple/Linear/Vercel visibile subito
- BOOT overlay sparisce
- Remaining Pool mostra 492 trovati / 24 renderizzati
- ricerca trova un giocatore
- P/D/C/A filtrano
- tap giocatore apre una sola bottom sheet
- chiusura bottom sheet libera la vista
- nessun blocco/scatto durante scroll

Non dichiara GOLD LOCK: restano i blocker del Golden Contract.
