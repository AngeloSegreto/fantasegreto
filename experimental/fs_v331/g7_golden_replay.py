"""FS V3.3.1 - complete National League scoring replay, fail closed.

G7 screenshot from 19 October 06:07 is explicitly PARTIAL. The final game
report cannot be certified until original final receipt and ALL required
observed pure votes/fantavotes are supplied. Synthetic unit tests do not
count as official scoring evidence or a prematch forecast.
"""
from __future__ import annotations
import json
import hashlib
import re
from pathlib import Path
from datetime import datetime
from decimal import Decimal
from copy import deepcopy
from league_scoring_v331 import score, D
from p0_core import fantagol

_SHA = re.compile(r"^[a-f0-9]{64}$")
_STATES = {"VOTED", "SV", "DID_NOT_PLAY"}

def _iso(s):
    t = datetime.fromisoformat(s)
    if t.tzinfo is None or t.utcoffset() is None:
        raise ValueError("Final evidence timestamp must include UTC offset")
    return t

def _txt(x):
    s = format(x, "f")
    return s.rstrip("0").rstrip(".") if "." in s else s

def verify_receipt(receipt):
    if not isinstance(receipt, dict):
        return ["MISSING_FINAL_SCREENSHOT_RECEIPT"]
    missing = [k for k in ("original_path", "sha256", "observed_at", "evidence_kind") if not receipt.get(k)]
    if missing:
        return ["MISSING_RECEIPT_FIELDS:" + ",".join(missing)]
    if receipt["evidence_kind"] not in ("OFFICIAL_APP_FINAL", "SYNTHETIC_UNIT_TEST"):
        return ["INVALID_FINAL_EVIDENCE_KIND"]
    _iso(receipt["observed_at"])
    if not _SHA.fullmatch(receipt["sha256"]):
        return ["INVALID_RECEIPT_SHA256"]
    path = Path(receipt["original_path"])
    if not path.is_file():
        return ["FINAL_RECEIPT_BYTES_NOT_ARCHIVED"]
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != receipt["sha256"]:
        return ["FINAL_RECEIPT_HASH_MISMATCH"]
    return []

def _hydrate(side, updates, side_name):
    cloned = deepcopy(side)
    errors = []
    ids = set()
    revisions = []
    for p in cloned["starters"] + cloned["bench"]:
        key = p["id"]
        if key in ids:
            raise ValueError("duplicate identity " + key)
        ids.add(key)
        upd = updates.get(key, {})
        if upd:
            if "id" in upd or "name" in upd or "role" in upd:
                raise ValueError("identity or role revision forbidden for " + key)
            newstatus = upd.get("status", p["status"])
            if p["status"] == "VOTED" and newstatus != "VOTED":
                revisions.append({"id": key, "from": p["status"], "to": newstatus})
            if (p["status"] == "VOTED" and newstatus == "VOTED" and
                "fantavote" in upd and D(upd["fantavote"]) != D(p["fantavote"])):
                revisions.append({"id": key, "from_fantavote": p["fantavote"], "to_fantavote": upd["fantavote"]})
            p.update(upd)
        st = p.get("status")
        if st == "PENDING_MATCH":
            errors.append(side_name + ":PENDING_MATCH:" + p["name"])
            continue
        if st not in _STATES:
            errors.append(side_name + ":UNKNOWN_STATE:" + p["name"])
            continue
        if st == "VOTED":
            for field in ("pure_vote", "fantavote"):
                if p.get(field) is None:
                    errors.append(side_name + ":MISSING_" + field.upper() + ":" + p["name"])
                else:
                    try: D(p[field])
                    except (ValueError, TypeError):
                        errors.append(side_name + ":INVALID_" + field.upper() + ":" + p["name"])
        elif p.get("pure_vote") is not None or p.get("fantavote") is not None:
            errors.append(side_name + ":INVALID_NONVOTE_RATING:" + p["name"])
    if set(updates) - ids:
        raise ValueError("updates contain player IDs not in original roster for " + side_name)
    roles = {}
    for p in cloned["starters"]:
        roles[p["role"]] = roles.get(p["role"], 0) + 1
    module = "-".join(str(roles.get(r, 0)) for r in ("D", "C", "A"))
    if roles.get("P", 0) != 1 or module != cloned["module"]:
        raise ValueError("observed XI does not match its module")
    return cloned, errors, revisions

def replay(snapshot, observed_final, config):
    """Return BLOCKED, PARITY_MISMATCH or PARITY_PENDING_REVIEW; NEVER GOLD."""
    if snapshot.get("status") != "LIVE_PARTIAL_NOT_OFFICIAL_RESULT":
        raise ValueError("G7 source must be labeled incomplete, not a forecast")
    result = {
        "schema": "FS_V331_NATIONAL_LEAGUE_G7_GOLDEN_REPLAY_V1",
        "matchday": snapshot["matchday"], "candidate_state": "SHADOW",
        "gold_lock": False, "tech_pass": False, "stat_validated": False,
        "prematch_holdout_eligible": False,
    }
    if not observed_final:
        result.update(status="BLOCKED_OFFICIAL_FINAL_NOT_PROVIDED",
                      missing=["FINAL_APP_SCOREBOARD", "MALDINI_FINAL_VOTE",
                               "SIMEONE_FINAL_VOTE", "PURE_VOTES_AND_FANTAVOTES",
                               "ORIGINAL_APP_EVIDENCE_BYTES"],
                      observed_partial={"home": "50", "away": "60.5"},
                      known_substitution_bases={"home": "56", "away": "66.5"})
        return result
    if observed_final.get("schema") != "FS_V331_G7_OFFICIAL_RESULT_INPUT_V1":
        raise ValueError("invalid observed-final input schema")
    if observed_final.get("matchday") != snapshot["matchday"]:
        raise ValueError("matchday mismatch")
    receipt = observed_final.get("receipt")
    blocked = verify_receipt(receipt)
    updates = observed_final.get("player_updates")
    if not isinstance(updates, dict):
        raise ValueError("player_updates must be ID-keyed map")
    for side in ("home", "away"):
        if side not in updates or not isinstance(updates[side], dict):
            raise ValueError("player updates missing for " + side)
    final_sides={}
    revisions={}
    for side in ("home", "away"):
        final_sides[side],errs,revs = _hydrate(snapshot[side], updates[side], side)
        blocked += errs
        revisions[side] = revs
    if revisions["home"] or revisions["away"]:
        blocked.append("PRIOR_VOTE_REVISIONS_REQUIRE_SEPARATE_APP_ATTESTATION")
    platform = observed_final.get("platform")
    if not isinstance(platform, dict):
        blocked.append("MISSING_FINAL_PLATFORM_SCORES")
    else:
        for key in ("home_total", "away_total", "home_goals", "away_goals"):
            if key not in platform:
                blocked.append("MISSING_PLATFORM_" + key.upper())
    if blocked:
        result.update(status="BLOCKED_INCOMPLETE_OFFICIAL_EVIDENCE",missing=sorted(set(blocked)),
                      no_total_inferred=True)
        return result

    calculated={}
    for name,side in final_sides.items():
        calculated[name]=score(side["starters"], side["bench"],side["captain_id"],
                               side["vice_id"], config, fantagol)
    mismatch = {}
    for name in ("home","away"):
        expected_total=D(platform[name + "_total"])
        observed_goals=platform[name+"_goals"]
        if not isinstance(observed_goals,int) or isinstance(observed_goals,bool) or observed_goals<0:
            raise ValueError("Invalid integer goal from official app for " + name)
        ours=D(calculated[name]["total"])
        if ours != expected_total or calculated[name]["fantagoals"] != observed_goals:
            mismatch[name]={"replayed_total":_txt(ours),"platform_total":_txt(expected_total),
                            "delta":_txt(ours-expected_total),
                            "replayed_goals":calculated[name]["fantagoals"],
                            "platform_goals":observed_goals}
    synthetic = receipt["evidence_kind"] == "SYNTHETIC_UNIT_TEST"
    result.update(
        status=("SOFTWARE_TEST_ONLY" if synthetic else
                ("SCORING_PARITY_FAIL" if mismatch else "SCORING_PARITY_PASS_PENDING_INDEPENDENT_AUDIT")),
        evidence_kind=receipt["evidence_kind"],receipt_sha256=receipt["sha256"],
        platform=platform,replay=calculated,discrepancies=mismatch,
        evidence_observed_at=receipt["observed_at"],
        independent_source_transcription_verified=False,
        golden_gate_G16="DA_VERIFICARE")
    return result

def main():
    import argparse
    from p0_core import load_config
    p=argparse.ArgumentParser(description="G7 final scoring replay, SHADOW only")
    p.add_argument("--partial",required=True)
    p.add_argument("--config",required=True)
    p.add_argument("--final")
    p.add_argument("--output")
    args=p.parse_args()
    partial=json.loads(Path(args.partial).read_text(encoding="utf-8"))
    obs=json.loads(Path(args.final).read_text(encoding="utf-8")) if args.final else None
    v=replay(partial,obs,load_config(args.config))
    data=json.dumps(v,ensure_ascii=False,indent=2)+"\n"
    if args.output:
        Path(args.output).write_text(data,encoding="utf-8")
    print(data)
if __name__=="__main__":
    main()
