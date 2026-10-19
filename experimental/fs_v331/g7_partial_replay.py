"""FS V3.3.1 — reconcile an INCOMPLETE matchday screen, never a certified result."""
from __future__ import annotations
from decimal import Decimal
import json

PENDING = "PENDING_MATCH"
NONVOTES = ("SV", "DID_NOT_PLAY")

def checked_score(v):
    d = Decimal(v)
    if not d.is_finite():
        raise ValueError("Non-finite vote")
    return d

def display_number(d):
    s=format(d,"f")
    return s.rstrip("0").rstrip(".") if "." in s else s

def reconcile_side(side, *, max_changes=5):
    starters = side["starters"]
    bench = side["bench"]
    if len(starters) != 11 or len(set(p["id"] for p in starters+bench))!=len(starters)+len(bench):
        raise ValueError("invalid XI/bench")
    pending = [p["name"] for p in starters if p["status"] == PENDING]
    confirmed_base = sum((checked_score(p["fantavote"]) for p in starters if p["status"] == "VOTED"),Decimal("0"))
    if confirmed_base != checked_score(side["raw_voted_starters_sum"]):
        raise ValueError("scoreboard sum doesn't match the uploaded screenshot")
    changes=[]
    used=set()
    effective_base=confirmed_base
    for p in starters:
        if p["status"] not in NONVOTES:
            continue
        substitute=next((b for b in bench if b["role"]==p["role"] and
                         b["status"]=="VOTED" and b["id"] not in used),None)
        if substitute is not None and len(changes)<max_changes:
            used.add(substitute["id"])
            effective_base+=checked_score(substitute["fantavote"])
            changes.append({"out":p["name"],"in":substitute["name"],"fantavote":substitute["fantavote"]})
    if pending:
        state="LIVE_PARTIAL_PENDING_MATCH"
    else:
        state="VOTES_AVAILABLE_NOT_OFFICIAL_REPLAY"
    return {"status":state,"voted_titulars_sum":display_number(confirmed_base),
            "known_substituted_sum":display_number(effective_base),"substitutions":changes,
            "pending_starters":pending,"modifier_and_captain_not_applied":True}

def reconcile(data):
    if data["status"] != "LIVE_PARTIAL_NOT_OFFICIAL_RESULT" or data["strict_context"]["prelock_evidence"]:
        raise ValueError("historical snapshot not eligible for prematch evaluation")
    own=reconcile_side(data["home"])
    against=reconcile_side(data["away"])
    if own["voted_titulars_sum"]!=data["scoreboard"]["home_partial_titulars_fantavotes"]:
        raise ValueError("home snapshot scoreboard mismatch")
    if against["voted_titulars_sum"]!=data["scoreboard"]["away_partial_titulars_fantavotes"]:
        raise ValueError("opponent snapshot scoreboard mismatch")
    return {"release_status":"SHADOW_LIVE_PARTIAL_ONLY","gold_lock":False,
            "prematch_prediction":False,"stat_validated":False,
            "home":own,"away":against,
            "next_event":"WAIT_FOR_MALDINI_AND_SIMEONE_OFFICIAL_VOTES"}
if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("json_file")
    args=p.parse_args()
    with open(args.json_file,encoding="utf8") as f:data=json.load(f)
    print(json.dumps(reconcile(data),ensure_ascii=False,indent=2))
