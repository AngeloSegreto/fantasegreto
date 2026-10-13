#!/usr/bin/env python3
"""FantaSegreto: validate official 13OCT staging before runtime promotion."""
import json, sys
from collections import Counter
from pathlib import Path

def fail(message):
    raise SystemExit("BLOCKED: " + message)

def validate(new_path, old_path):
    new=json.loads(Path(new_path).read_text(encoding="utf-8"))
    old=json.loads(Path(old_path).read_text(encoding="utf-8"))
    players=new["players"]
    ids=[str(p["official_id"]) for p in players]
    if len(ids)!=len(set(ids)): fail("duplicate official IDs")
    if len(players)!=new["active_count"]: fail("active_count mismatch")
    if len(new["ceduti"])!=new["ceduti_count"]: fail("ceduti_count mismatch")
    counts=dict(Counter(p["role"] for p in players))
    if counts!={"P":65,"D":192,"C":195,"A":87}: fail("unexpected role counts "+repr(counts))
    previous={str(p["official_id"]):p for p in old["players"]}
    current={str(p["official_id"]):p for p in players}
    added=sorted(set(current)-set(previous),key=int)
    removed=sorted(set(previous)-set(current),key=int)
    fields=("name","team","role","quote","fvm","mantra_role")
    changed=[]
    for k in sorted(set(current)&set(previous),key=int):
        delta={f:{"old":previous[k].get(f),"new":current[k].get(f)}
               for f in fields if str(previous[k].get(f,""))!=str(current[k].get(f,""))}
        if delta:changed.append({"official_id":k,"changes":delta})
    result={"schema":"FS_LISTONE_RECONCILIATION_V1",
            "source_sha256":new["source_sha256"],"active_count":len(players),
            "added":[current[k] for k in added],
            "removed":[previous[k] for k in removed],
            "changed":changed,"changed_count":len(changed),
            "promotion":"BLOCKED_PENDING_RUNTIME_PARITY_AND_GOLDEN_GATES",
            "optimizerMax_mutated":False}
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return result

if __name__=="__main__":
    if len(sys.argv)!=3:fail("usage: python tools/reconcile_listone_13oct.py NEW_JSON OLD_JSON")
    validate(sys.argv[1],sys.argv[2])
