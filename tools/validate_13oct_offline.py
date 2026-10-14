#!/usr/bin/env python3
"""Free, offline, fail-closed FantaSegreto official roster validation."""
import json
from pathlib import Path

def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def check(condition, message):
    if not condition:
        raise AssertionError(message)

reg = load("registry.json")
ver = load("version.json")
official = load("listone-13oct2026.json")
details = load("player-details.json")
players = reg["players"]
source = official["players"]
expected = official["active_count"]
check(expected == len(source) == len(players) == reg["count"] == ver["runtime_registry_count"], "Runtime count parity")
check(len({str(p["official_id"]) for p in players}) == expected, "Duplicate runtime official ID")
check(len({p["id"] for p in players}) == expected, "Duplicate runtime ID")
check(len({str(p["official_id"]) for p in source}) == expected, "Duplicate source ID")
by_id = {str(p["official_id"]): p for p in players}
check(set(by_id) == {str(p["official_id"]) for p in source}, "Official ID membership mismatch")
for p in source:
    q = by_id[str(p["official_id"])]
    for field in ("name", "team", "role", "quote", "fvm", "mantra_role", "mantra_quote", "mantra_fvm"):
        check(str(q.get(field, "")) == str(p.get(field, "")), f"Official parity {p['official_id']} {field}")
    check(q.get("serie_a_membership") == "ACTIVE_OFFICIAL_13OCT2026", "Stale membership")
    check(all(q.get(k) is None for k in ("score", "ideal", "max")), "Uncertified model data")
check(official["ceduti_count"] == len(official["ceduti"]) == 64, "Ceduti count")
check(ver["gold"] is False and ver["optimizerMax_mutated"] is False, "Golden/optimizer mutation")
check(ver["model_recalculation_status"] == "PENDING_FULL_FOS_RISK_MAX_13OCT", "Unsafe model promotion")
check(isinstance(details.get("details"), dict), "Legacy detail archive invalid")
# Legacy details are archival, not required to match the current active count.
sw = Path("sw.js").read_text(encoding="utf-8")
html = Path("index.html").read_text(encoding="utf-8")
check("fantasegreto-v4-2-5-13oct-fail-closed-r1" in sw, "PWA cache version")
check("sw.js?v=42513r1" in html, "PWA registration version")
check("./listone-13oct2026.json" in sw, "PWA source missing")
print("FS_13OCT_OFFICIAL_539_PARITY_PASS")
print("FS_13OCT_BUY_MAX_FAIL_CLOSED_PASS")
print("FS_13OCT_PWA_STATIC_GATE_PASS")
print("FS_LEGACY_DETAILS_ARCHIVE", len(details["details"]))
print("FS_PHYSICAL_IPHONE_GATE_PENDING")
