#!/usr/bin/env python3
"""Render the nine-column Phase 0 inventory. Statuses are reviewed findings, not inferred certification."""
import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
C = 'experimental/match-win-v3_2/'
HEADERS = ['ID Requisito','Fonte Normativa','Codice Esistente','Test Presenti','Evidenza / Hash','Stato','Lacuna Rilevata','Criterio di Chiusura','Dipendenza di Promozione']
PART = 'PARZIALMENTE IMPLEMENTATO'
NO = 'NON IMPLEMENTATO'
YES = 'VERIFICATO'
CHECK = 'DA VERIFICARE'

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def evidence(*names):
    return '; '.join(str((OUT/n).relative_to(ROOT))+' SHA256='+digest(OUT/n) for n in names)

def main():
    inspection = json.loads((OUT/'inspection.json').read_text())
    probes = json.loads((OUT/'probes.json').read_text())
    rows = []
    def add(rid, source, code, tests, ev, status, gap, closure, dependency):
        rows.append(dict(zip(HEADERS,[rid,source,code,tests,ev,status,gap,closure,dependency])))
    suite = C+'test.js'
    unit = evidence('evidence/candidate-tests.log')
    scan = evidence('inspection.json')
    probe = evidence('probes.json')
    gates = [
      ('G00','core.js:validate; run.js',suite,unit,PART,'URL e observed_at validati; snapshot grezzi delle fonti reali non acquisiti.','Ogni campo usato risolve a snapshot e provenienza archiviati; test negativo su snapshot assente.','P0; blocca TECH PASS e promozione'),
      ('G01','core.js:validate',suite,unit,PART,'Controllo fixture/team sintetico presente; calendario ufficiale della giornata non integrato.','Mapping giocatore-squadra-partita corretto per giornata; rinvii e assenze gestiti con fonte.','P0; blocca run reale certificata'),
      ('G02','../../registry.json; ../../tools/validate_official_runtime.py; core.js:validate','tools/validate_official_runtime.py; tools/validate_13oct_offline.py; '+suite,evidence('evidence/official-runtime.log','evidence/official-parity.log','evidence/candidate-tests.log'),YES,'Nessuna collisione nei 539 record dello snapshot ufficiale 13OCT; verifica limitata a questo snapshot, non alla freschezza futura.','Rieseguire con ogni nuovo snapshot e mantenere mapping univoco e test negativi.','P0; verifica di identità, non calibrazione'),
      ('G03','core.js:formation/validateLineup; optimizer.js:enumerate',suite,unit,PART,'Sette moduli e ID verificati sui test; elenco dei moduli ufficialmente ammessi non certificato in configurazione.','Configurazione ufficiale e test di validità di XI, ruoli, capienza e panchina per ogni candidata.','P0; dipende da G20'),
      ('G04','core.js:availability/validate; diagnostics.js:betaVotePosterior',suite,unit,PART,'Indisponibile forza start/sub a zero ma puo ancora comparire nel XI; nessun registro override o feed ufficiale aggiornato.','Esclusione dalla raccomandazione, conservazione della scelta umana separata e prova delle indisponibilita.','P0; dipende da G22 e fonti'),
      ('G05','simulator.js:scenario',suite,unit,PART,'Risultati, marcatori, assist e portieri coerenti nel modello full-match; minuti e cambio portiere non risolti.','Casi strutturali su tempo in campo e regole effettive; perimetro semplificato esplicitamente limitato fino alla chiusura.','P1; blocca promozione se il perimetro reale include casi non supportati'),
      ('G06','core.js:prob/validate; simulator.js:evaluate',suite,unit,PART,'Dominio e somma verificati entro tolleranza nei test; contratto finale scrive uguaglianza esatta senza rappresentazione/tolleranza.','Contratto numerico dichiarato per conteggi, probabilita e somma; test negativi di massa e valori non finiti.','P0; blocca TECH PASS globale'),
      ('G07','core.js:score',suite,unit,PART,'Cinque cambi stesso ruolo e ordine panchina testati; fixture ufficiali complete ed eccezioni SV mancanti.','Riprodurre sostituzioni ufficiali su tutte le fixture certificate e configurazione delle eccezioni.','P0; dipende da G20 e dataset G16'),
      ('G08','core.js:goals; simulator.js:evaluate; diagnostics.js:liveWhatIf',suite,probe,PART,'Controlli 65.9-102 superati; soglie hardcoded 66/4, Number binario, nessuna aritmetica decimale esatta.','Soglie lette dalla configurazione; scoring decimale esatto; golden dei confini e mutazione della config senza patch al codice.','P0; blocca conformita V3.3.1 anche con test V3.2 verdi'),
      ('G09','core.js:score/validate',suite,unit,PART,'Fasce configurabili nel payload ma nessuna regola di lega certificata; scenari di sensibilita non orchestrati.','Regola certificata attiva/disattiva e confronto ufficiale; regola necessaria non certificata mantiene GOLD bloccato.','P0; dipende da G20, blocco prevalente V3.3.1'),
      ('G10','core.js:score/validate',suite,unit,PART,'Capitano/vice e fallback SV testati in esempio; fasce ed eccezioni National League non certificate.','Regola ufficiale, eccezioni SV e totali certificati; sensibilita separata e nessuna promozione con regola necessaria ignota.','P0; dipende da G20, blocco prevalente V3.3.1'),
      ('G11','simulator.js:evaluate; optimizer.js:optimize',suite,unit,PART,'Confronto keeper disponibile su input sintetici; Meret/Gollini/Svilar non confrontati su fixture e proiezioni attuali.','Confronto reale in XI completi, disponibilita verificata e impatto sul criterio attivo.','P1; nessun consiglio reale certificato disponibile'),
      ('G12','core.js:validate; diagnostics.js:rollingBacktest',suite,unit,PART,'Timestamp futuri rifiutati; nessuna prova completa che il contenuto della fonte fosse noto entro lock.','Snapshot pre-lock, tempi di pubblicazione/acquisizione e trasformazioni tracciate; test di contaminazione del contenuto.','P0; blocca backtest certificato'),
      ('G13','run.js; simulator.js:evaluate',suite,scan,PART,'Run precedente 100k+100k sintetica archiviata; N fisso, nessun supervisore di deadline o budget fallback.','Macchina ratificata, T_max e sottobudget, controllo timeout, precisione e memoria misurate sul flusso completo.','P0; dipende da P0-BUDGET e P0-FALLBACK'),
      ('G14','diagnostics.js:metrics',suite,unit,PART,'Brier 0-2/log loss/MAE/ECE disponibili; mancano storico OOS, curve complete, baseline e pre-registrazione ratificata.','Superare criteri pre-registrati con campione e incertezza; separare esito condizionato a XI noti e previsione pre-lock.','P1 predittivo; blocca STAT VALIDATED e GOLD'),
      ('G15','diagnostics.js:rollingBacktest',suite,unit,PART,'Harness rolling verificato con dati sintetici; nessun backtest reale certificato.','Fold temporali reali, fonte pre-lock, baseline comparabili, metodo appaiato e incertezza pre-registrati.','P1 predittivo; blocca STAT VALIDATED e GOLD'),
      ('G16','diagnostics.js:postmatchOracle; g7-observed.json',suite+'; experimental/scoring-gate-v1.test.js',evidence('evidence/candidate-tests.log','evidence/legacy-scoring.log'),PART,'23 test nuovi e 28 controlli legacy superati; G7 contiene solo sette valori utente, senza XI, panchina, sostituzioni e totali ufficiali completi.','Golden ufficiali indipendenti su dataset completo; specificare voto puro/fantavoto; auditor separato.','P0; blocca TECH PASS V3.3.1'),
      ('G17','Nessun adapter XLSX/PWA del nuovo scoring','Nessun test di parita XLSX/PWA',scan,NO,'Le suite attuali non eseguono un workbook contro il nuovo motore e la PWA.','Stessi input certificati e identita di scoring, modificatori, sostituzioni e fantagol nei tre percorsi.','P0 di rilascio; blocca promozione'),
      ('G18','index.html; audit-browser.js',suite+'; '+C+'audit-browser.js',unit,PART,'Sintassi HTML/JS testata; browser eseguibile non disponibile nell audit precedente e nessuna accettazione iPhone fisico.','Test browser eseguito e prova fisica della prima schermata con dati reali/provvisori/nulli corretti.','P0 di attivazione Control Room'),
      ('G19','run.js; audit.js',suite,scan,PART,'Nove asset protetti identici e manifest V3.2 validi; rollback operativo e release V3.3.1 non verificati.','Manifest completo, versione/config compatibili, rollback eseguito, nessun gate necessario pendente.','P0 di rilascio; non autorizza merge/deploy'),
      ('G20','core.js:validate; real-input-template.json',suite,unit,PART,'Validatore procedurale parziale; league_config.yaml e schema formale con stato/fonte per ogni regola assenti.','Schema e controlli semantici, valori ufficiali e tracciamento dei campi non certificati; test negativi.','P0; dipendenza di G03/G07/G08/G09/G10'),
      ('G21','run.js; simulator.js:rng/evaluate',suite,scan,PART,'Replay stesso seed verificato e input/report archiviati; normalizzazione, PRNG PCG64, snapshot grezzi e ambiente ricostruibile mancanti.','Replay contenuto decisionale identico in ambiente dichiarato, file originali archiviati, canonicalizzazione e test di permutazione.','P0; dipende da P0-IDENTITA e P0-PRNG'),
      ('G22','Nessun registro override match; state-manager.js gestisce lo stato asta','Nessun test registro override pre-lock',scan,NO,'Le transazioni asta non costituiscono un registro delle decisioni di formazione.','Raccomandazione e scelta umana separate, timestamp entro lock, modifiche append-only e test negativi.','P0; blocca attivazione del flusso decisionale'),
    ]
    for rid,code,tests,ev,state,gap,closure,dep in gates:
        # Paths in this column are rooted at repository, not at an imaginary src/ tree.
        if code.startswith('../../'):
            code = code.replace('../../','').replace('; core.js','; '+C+'core.js')
        elif not code.startswith('Nessun'):
            code = '; '.join(C+p for p in code.split('; '))
        add(rid,'V3.3.1 testo ricevuto §7; clausole specifiche §§2-6',code,tests,ev,state,gap,closure,dep)
    additions = [
      ('P0-PROFILO','§3','optimizer.js:rankResults/optimize',suite,unit,PART,'Solo MAX_VITTORIA poi draw; PUNTI_ATTESI e doppio output assenti.','Profili configurati e verificati su controesempio dove cambiano la raccomandazione.','P0; dipende da verifica punteggi della lega'),
      ('P0-CONFRONTO','§3 e preambolo contratto statistico','simulator.js:evaluate; optimizer.js:rankResults',suite,unit,PART,'Intervalli appaiati presenti ma nessun delta, verdetto a tre vie o spareggio per sola equivalenza.','Tre verdetti e test dei limiti; INCONCLUDENTE conserva il massimo criterio primario e non diventa equivalenza.','P0; blocca conformita della raccomandazione'),
      ('P0-CONFERMA','Preambolo protocollo selezione-conferma','optimizer.js:optimize',suite,unit,PART,'Selezione congelata e holdout a seed diverso presenti; nessuna pre-registrazione completa o attestazione dei flussi indipendenti.','Protocollo ratificato, finaliste conservate, N di conferma fissato, nessuna riselezione dopo conferma.','P0; distinto dalla validazione predittiva futura'),
      ('P0-IDENTITA','§4 e preambolo identita completa','Nessuna identita canonica della candidata','Nessun test identita completa',scan,NO,'SHA degli input non e identita di XI/panchina/capitano/vice; spareggio su indice.','Serializzazione non ambigua dell intera candidata, hash stabile; bench/capitano diversi producono identita diverse.','P0; dipendenza di G21'),
      ('P0-PERMUTAZIONI','§4','simulator.js:compile/scenario; optimizer.js:rankResults','audit/v3_3_1_phase0/probes.js',probe,PART,'Due difetti riprodotti: inversione record giocatori cambia output stesso seed; inversione candidate a pari punteggio cambia vincitore.','Record e candidate canonicalizzati; risultati per ID invarianti; ordine panchina preservato; spareggio stabile.','P0; blocca determinismo V3.3.1'),
      ('P0-PRNG','§4','simulator.js:rng/scenario',suite,probe,PART,'Generatore attuale a stato 32 bit, nessun PCG64 o flusso derivato da identita; seed unico sequenziale.','PCG64/trasformazioni/versione/derivazione specificati; flussi partita condivisi preservano G05; test di invarianza.','P0; dipende da contratto di casualita e G05'),
      ('P0-BUDGET','§5 e preambolo budget','run.js; simulator.js:evaluate',suite,scan,PART,'Parametro N fisso; nessuna interruzione forzata o riserva di tempo per ripiego/pubblicazione.','Controllo su tempo monotono, sottobudget coerenti col lock, test timeout e pubblicazione; benchmark completo.','P0; dipendenza bloccante di G13'),
      ('P0-FALLBACK','§5','Nessun supervisore o motore di ripiego verificato','Nessun test di attivazione fallback',scan,NO,'Blocco input esistente non equivale a timeout e percorso di ripiego compatibile.','Identificare e provare ripiego oppure percorso manuale RIPIEGO NON DISPONIBILE; disponibilita temporale verificata.','P0 di attivazione operativa anche se sviluppato come P1'),
      ('P0-NORMALIZZAZIONE','§4 e preambolo perimetro del determinismo','run.js',suite,scan,PART,'Input archiviato come JSON nell ordine originale, nessun hash semantico separato dal grezzo.','Byte grezzi preservati, modello normalizzato canonico, metadati operativi esclusi dal confronto decisionale.','P0; dipende da P0-IDENTITA'),
      ('P1-SCREENING','Preambolo dipendenza screening-rilascio','optimizer.js:searchSize/enumerate',suite,unit,PART,'Enumerazione limitata a 1000 e pannello esplicito; non esiste screening adattivo o report di perdita.','Misurare perdita e copertura su casi enumerabili con criterio pre-registrato; nessuna garanzia globale fuori campione.','P1 sviluppo; blocco promozione se usato nella scelta'),
      ('P1-AVVERSARIO','V3.3 base §9.9 come contesto, requisiti scenario condiviso §7 G05/G11','simulator.js:evaluate; real-input-template.json',suite,unit,PART,'Un solo XI avversario per run; nessuna miscela di alternative con pesi documentati.','Se attivata, distribuzione su XI avversari con pesi e perimetro; separare previsione pre-lock da scoring a XI noti.','P1; richiede conferma del perimetro della specifica sostitutiva'),
      ('P1-INCERTEZZA','Preambolo recepimento dei rilievi; V3.3 base §8 come contesto','core.js:freshness; diagnostics.js:betaVotePosterior',suite,unit,PART,'Confidence fonte e posterior marginale non costituiscono propagazione dell incertezza dei parametri.','Se attivata, distinguere rumore MC, variabilita eventi e incertezza stime; test su input perturbati.','P1; nessuna dichiarazione di intervallo predittivo completo'),
      ('P1-MONITORAGGIO','Preambolo policy degrado','Nessun monitor post-promozione','Nessun test monitor o allerta',scan,NO,'Metriche disponibili ma nessuna policy di allerta o retrocessione a versione compatibile verificata.','Protocollo ratificato, log verificabili, nessuna soglia arbitraria di quattro giornate; non inviare comunicazioni senza autorizzazione.','P1; precondizione della relativa attivazione operativa'),
      ('DOC-SPECIFICA','§1, §8 e preambolo identita specifica','audit/v3_3_1_phase0/specification-received.txt; ratification-clarifications.md','Validazione matrice e manifest di questa consegna',evidence('specification-received.txt','ratification-clarifications.md'),PART,'Testo canonico nel messaggio omette tabella confronto, lista identita, formula soglie e intestazioni nove colonne; preambolo recupera parte dei contenuti.','Conservare testo ricevuto ed estratti separati, hash reali e gerarchia; non dichiarare un file nativo utente o firma digitale inesistenti.','P0 documentale; rilievi tracciati, Fase 0 autorizzata'),
    ]
    for rid,src,code,tests,ev,state,gap,closure,dep in additions:
        if code.startswith(('core.js','run.js','simulator.js','optimizer.js')):
            code='; '.join(C+p for p in code.split('; '))
        add(rid,'V3.3.1 '+src,code,tests,ev,state,gap,closure,dep)
    with (OUT/'MATRICE_CONFORMITA_V3_3_1.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=HEADERS);writer.writeheader();writer.writerows(rows)
    table='| '+' | '.join(HEADERS)+' |\n|'+ '|'.join(['---']*9)+'|\n'
    for row in rows:
        table+='| '+' | '.join(str(row[h]).replace('|','\\|').replace('\n',' ') for h in HEADERS)+' |\n'
    (OUT/'MATRICE_CONFORMITA_V3_3_1.md').write_text('# Matrice di conformita V3.3.1 — Fase 0\n\nCommit ispezionato: `'+inspection['reviewed_remote_commit']+'`. Stato del requisito completo nel perimetro dichiarato, non etichetta di qualita del singolo test. I PASS V3.2 non chiudono automaticamente la V3.3.1. Le righe P1 riferite solo alla base sostituita sono esplicitamente segnate come contesto da confermare.\n\n'+table,encoding='utf8')
    counts=dict(Counter(r['Stato'] for r in rows))
    summary={'schema':'FS_PHASE0_MATRIX_V1','reviewed_commit':inspection['reviewed_remote_commit'],'requirements':len(rows),'columns':HEADERS,'status_counts':counts,
             'all_gate_ids_present':set('G'+str(i).zfill(2) for i in range(23)).issubset(r['ID Requisito'] for r in rows),
             'existing_test_groups_pass':inspection['inspection_checks_pass'],'target_invariance_findings':probes,
             'phase0_deliverable':'COMPLETED','phase1_tech_pass':False,'stat_validated':False,'gold':False,'independent_auditor':False,'digital_signature':False}
    (OUT/'matrix-summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    # Verify actual artifact shape/statuses and the real hashes embedded in every evidence cell.
    assert len({r['ID Requisito'] for r in rows})==len(rows)
    assert summary['all_gate_ids_present']
    assert all(r['Stato'] in {PART,NO,YES,CHECK} for r in rows)
    with (OUT/'MATRICE_CONFORMITA_V3_3_1.csv').open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f);assert reader.fieldnames==HEADERS
        parsed=list(reader);assert parsed==rows and all(len(r)==9 for r in parsed)
    for row in rows:
        for ref in row['Evidenza / Hash'].split('; '):
            name,h=ref.split(' SHA256=');assert digest(ROOT/name)==h
    (OUT/'matrix-validation.json').write_text(json.dumps({'status':'PASS_MATRIX_ARTIFACT_ONLY','rows':len(rows),'columns':9,'unique_ids':True,'gates_G00_G22_complete':True,'evidence_hashes_verified':True,'gold':False},indent=2)+'\n')
    print(json.dumps({'rows':len(rows),'columns':9,'status_counts':counts,'artifact_validation':'PASS','gold':False},indent=2,ensure_ascii=False))

if __name__=='__main__':
    main()
