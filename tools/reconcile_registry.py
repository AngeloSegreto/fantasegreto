#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

FIELDS=("nome","squadra","ruolo","ruolo_mantra","quotazione_iniziale","quotazione","fvm","starred")

def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))

def rows(obj):
    return obj.get("players", obj if isinstance(obj,list) else [])

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--old", required=True)
    ap.add_argument("--new", required=True)
    ap.add_argument("--output", required=True)
    args=ap.parse_args()
    old={str(x.get("id_ufficiale") or x.get("official_id") or x.get("id")):x for x in rows(load(args.old))}
    new_obj=load(args.new)
    new={str(x["id_ufficiale"]):x for x in rows(new_obj)}
    events=[]
    for oid in sorted(set(old)|set(new), key=lambda x:(not x.isdigit(), int(x) if x.isdigit() else x)):
        b=old.get(oid); a=new.get(oid)
        if b is None:
            event="NEW_CANONICAL"; changed=list(FIELDS)
        elif a is None:
            event="ARCHIVE_ABSENT"; changed=[]
        else:
            changed=[f for f in FIELDS if b.get(f)!=a.get(f)]
            if not changed: event="UNCHANGED"
            elif "squadra" in changed: event="RATIFICA_TEAM"
            elif "ruolo" in changed or "ruolo_mantra" in changed: event="RATIFICA_ROLE"
            elif any(f in changed for f in ("quotazione_iniziale","quotazione","fvm")): event="RATIFICA_QUOTE"
            elif "nome" in changed: event="RATIFICA_ALIAS"
            else: event="RATIFICA"
        events.append({"event":event,"id_ufficiale":oid,"changed":changed,"before":b,"after":a})
    summary={}
    for e in events: summary[e["event"]]=summary.get(e["event"],0)+1
    out={"schema":"FS_REGISTRY_DIFF_V3_9_5__V3_9_6","source_sha256":new_obj.get("source_sha256"),"summary":summary,"events":events}
    Path(args.output).parent.mkdir(parents=True,exist_ok=True)
    Path(args.output).write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False))

if __name__=="__main__":
    main()
