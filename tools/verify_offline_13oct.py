#!/usr/bin/env python3
"""FantaSegreto offline runtime data gate. No GitHub Actions, no dependencies."""
import json
from pathlib import Path

def read(name):
    return json.loads(Path(name).read_text(encoding="utf-8"))

reg, ver, official = map(read, ("registry.json", "version.json", "listone-13oct2026.json"))
players, source = reg["players"], official["players"]
expected = int(ver["runtime_registry_count"])
assert expected == reg["count"] == len(players) == official["active_count"] == len(source), "COUNT_MISMATCH"
rids = [str(p["official_id"]) for p in players]
sids = [str(p["official_id"]) for p in source]
assert len(set(rids)) == len(rids) and len(set(sids)) == len(sids), "DUPLICATE_OFFICIAL_ID"
assert set(rids) == set(sids), "MEMBERSHIP_MISMATCH"
assert len(set(p["id"] for p in players)) == expected, "DUPLICATE_RUNTIME_ID"
assert all(p.get("serie_a_membership") == "ACTIVE_OFFICIAL_13OCT2026" for p in players), "STALE_MEMBERSHIP"
byid = {str(p["official_id"]): p for p in source}
for p in players:
    q = byid[str(p["official_id"])]
    for field in ("name", "team", "role", "mantra_role", "quote", "initial_quote", "quote_delta", "fvm", "mantra_quote", "mantra_initial_quote", "mantra_quote_delta", "mantra_fvm"):
        a, b = p.get(field), q.get(field)
        if a is None or b is None:
            raise AssertionError(f"MISSING_FIELD:{p['official_id']}:{field}")
        if str(a) != str(b):
            raise AssertionError(f"FIELD_MISMATCH:{p['official_id']}:{field}:{a}:{b}")
assert ver.get("gold") is False and ver.get("optimizerMax_mutated") is False, "UNSAFE_GOLD"
assert ver.get("model_recalculation_status") == "PENDING_FULL_FOS_RISK_MAX_13OCT", "UNSAFE_MODEL_STATE"
assert all(p.get(k) is None for p in players for k in ("score", "ideal", "max")), "UNCERTIFIED_MODEL_VALUES"
app = Path("app.js").read_text(encoding="utf-8")
engine = Path("engine.js").read_text(encoding="utf-8")
assert "return 'WAIT · FOS PENDING'" in app, "UI_WAIT_GUARD_MISSING"
assert "if(fsModelBlocked())return 0;" in engine, "MAX_GUARD_MISSING"
assert "if(fsModelBlocked())return 'WAIT';" in engine, "DECISION_GUARD_MISSING"
assert "if(fsModelBlocked())return [];" in engine, "CANDIDATE_GUARD_MISSING"
print(f"FS_OFFLINE_13OCT_DATA_PARITY_PASS {expected}")
print("FS_BUY_MAX_FAIL_CLOSED_PASS")
print("FS_GOLD_NOT_CERTIFIED")
