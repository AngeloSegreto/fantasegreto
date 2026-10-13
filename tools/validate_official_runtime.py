#!/usr/bin/env python3
"""FantaSegreto offline official-listone gate. Run: python3 tools/validate_official_runtime.py"""
import json
from pathlib import Path

def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def main():
    reg=load("registry.json")
    ver=load("version.json")
    official=load("listone-13oct2026.json")
    details=load("player-details.json")
    sw=Path("sw.js").read_text(encoding="utf-8")
    index=Path("index.html").read_text(encoding="utf-8")
    app=Path("app.js").read_text(encoding="utf-8")
    engine=Path("engine.js").read_text(encoding="utf-8")
    players=reg["players"]
    official_players=official["players"]
    expected=official["active_count"]
    assert expected==539, "Unexpected source snapshot"
    assert len(players)==reg["count"]==ver["runtime_registry_count"]==expected
    assert len(official_players)==expected
    assert len(official["ceduti"])==official["ceduti_count"]==64
    ids=[str(p["official_id"]) for p in players]
    official_ids=[str(p["official_id"]) for p in official_players]
    assert len(set(ids))==len(set(official_ids))==expected
    assert set(ids)==set(official_ids), "Registry/Listone ID parity"
    assert len({p["id"] for p in players})==expected
    by_id={str(p["official_id"]):p for p in official_players}
    for p in players:
        q=by_id[str(p["official_id"])]
        for key in ("name","team","role","mantra_role"):
            assert str(p.get(key))==str(q.get(key)), (p["official_id"],key)
        for key in ("quote","initial_quote","quote_delta","fvm","mantra_quote","mantra_initial_quote","mantra_quote_delta","mantra_fvm"):
            assert float(p[key])==float(q[key]), (p["official_id"],key)
        assert p["serie_a_membership"]=="ACTIVE_OFFICIAL_13OCT2026"
        assert all(p.get(k) is None for k in ("score","ideal","max"))
    assert ver["gold"] is False and ver["optimizerMax_mutated"] is False
    assert ver["model_recalculation_status"]=="PENDING_FULL_FOS_RISK_MAX_13OCT"
    assert "fsModelBlocked()" in engine and "WAIT · FOS PENDING" in app
    assert "fantasegreto-v4-2-5-13oct-fail-closed-r1" in sw
    assert "listone-13oct2026.json" in sw
    assert "sw.js?v=42513r1" in index
    # Historical details archive may contain more records than active roster.
    assert details["count"]==expected
    active_ids={p["id"] for p in players}
    missing=active_ids-set(details["details"])
    archived=set(details["details"])-active_ids
    assert "merged.details[p.id]={id:p.id" in app, "Safe UI detail fallback missing"
    print("FS_OFFICIAL_13OCT_RUNTIME_SAFE_PASS",expected)
    print("FS_LEGACY_DETAILS_ARCHIVED",len(archived),"ACTIVE_DETAIL_FALLBACKS",len(missing))
    print("FS_BUY_MAX_FAIL_CLOSED_PASS")
    print("FS_PREMIUM_MODEL_PENDING_NOT_CERTIFIED")

if __name__=="__main__":
    main()
