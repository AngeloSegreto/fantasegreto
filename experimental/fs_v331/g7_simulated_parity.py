"""V3.3.1 SHADOW: observed platform simulation vs independently transcribed components.

This is an APP-simulated-result reconciliation, NOT an independent full
pure-vote scoring replay, and NOT an authenticated final result for G16/GOLD.
"""
from __future__ import annotations
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path
from p0_core import fantagol

class EvidenceConflict(ValueError): pass

def d(v):
    if v is None or isinstance(v, (bool,float)):
        raise EvidenceConflict("Decimal string/integer only")
    try: x=Decimal(str(v))
    except (InvalidOperation,ValueError,TypeError) as e:
        raise EvidenceConflict("invalid number") from e
    if not x.is_finite():raise EvidenceConflict("non-finite number")
    return x

def display(x):
    s=format(x,"f")
    return s.rstrip("0").rstrip(".") if "." in s else s

def reconcile(data,config):
    if data.get("evidence_kind")!="USER_APP_SCREENSHOTS_WITH_LABEL_RISULTATO_SIMULATO":
        raise EvidenceConflict("unexpected evidence kind")
    if data.get("status")!="APP_SIMULATED_SCORE_NOT_OFFICIAL_FINAL":
        raise EvidenceConflict("untrusted final status")
    if data.get("use_for_calibration") is not False or data.get("use_as_prelock_prediction") is not False:
        raise EvidenceConflict("must not feed live results into a forecast backtest")
    if data.get("gold_lock") is not False:
        raise EvidenceConflict("promotion forbidden")
    g=[m for m in data.get("matches",[]) if m.get("home")=="Mall & Dealer Sikuli" and m.get("away")=="AC DENTI"]
    if len(g)!=1:
        raise EvidenceConflict("target match not unique")
    m=g[0]
    if m.get("home_formation")!="4-3-3" or m.get("away_formation")!="3-5-2":
        raise EvidenceConflict("formation mismatch")
    p=m["simulated_platform"]
    if p["label"]!="Risultato simulato":
        raise EvidenceConflict("not a simulated app receipt")
    components=m["independently_visible_components"]
    result={}
    for side in ("home","away"):
        part=components[side]
        if len(part["true_subs"])!=1:
            raise EvidenceConflict("unverified substitute chain")
        sub=part["true_subs"][0]
        if sub["out_status"] not in ("SV","DID_NOT_PLAY"):
            raise EvidenceConflict("invalid substitution")
        if sub["role"] != ("D" if side=="home" else "C"):
            raise EvidenceConflict("Traditional requires same-role replacement")
        if side=="home":
            if sub["out"]!="Wesley" or sub["in"]!="Cambiaso" or part["captain"]!="Maldini":
                raise EvidenceConflict("starter/captain mismatch with snapshot")
            assert d(part["starter_votes_sum"]) == d(m["live_titulars"]["home"])
            added=d(sub["fantavote"])
            base=d(part["starter_votes_sum"])
        else:
            if sub["out"]!="Adzic" or sub["in"]!="Perrone" or part["captain"]!="Nico Paz":
                raise EvidenceConflict("starter/captain mismatch with snapshot")
            if d(part["starter_votes_sum_without_simeone"]) != d(m["live_titulars"]["away"]):
                raise EvidenceConflict("partial mismatch")
            added=d(sub["fantavote"]) + d(part["simeone_fantavote"])
            base=d(part["starter_votes_sum_without_simeone"])
        factor=d(part["captain_factor"])
        before_mod=base+added+factor
        observed=d(p[side+"_total"])
        residual=observed-before_mod
        # Platform screenshots show factor explicitly but do not supply raw
        # defense votes; the zero modifier is an INFERRED RESIDUAL, not
        # independent verification of the modifier formula.
        if residual!=d(m["residual_modifier_from_platform_if_no_other_components"][side]):
            raise EvidenceConflict("defense/unknown component residual changed")
        if side=="away" and not part["defense_three_no_modifier"]:
            raise EvidenceConflict("3-5-2 cannot claim four-defender modifier")
        goals=p[side+"_goals"]
        if isinstance(goals,bool) or not isinstance(goals,int) or goals<0:
            raise EvidenceConflict("invalid platform goal count")
        observed_goals=fantagol(observed,config)
        if observed_goals!=goals:
            raise EvidenceConflict("platform goal threshold mismatch")
        result[side]={"starter_partial":display(base),"included_later_and_substitutions":display(added),
                      "captain_factor_observed":display(factor),"before_modifier":display(before_mod),
                      "modifier_residual_inferred":display(residual),"platform_total":display(observed),
                      "fantagoals":goals}
    return {"schema":"FS_V331_G7_APP_SIMULATED_PARITY_RESULT_V1",
            "status":"APP_SIMULATED_TOTAL_DECOMPOSITION_PASS",
            "parity_vs_app_simulation":True,
            "G07":"PARTIALLY_EVIDENCED",
            "G09":"NO_INDEPENDENT_PURE_VOTE_REPLAY",
            "G10":"FACTOR_OBSERVED_IN_APP_NOT_RAW_VOTE_REPLAYED",
            "G16":"DA_VERIFICARE",
            "g14_g15_eligible":False,"tech_pass":False,"stat_validated":False,"gold_lock":False,
            "home":result["home"],"away":result["away"],
            "notes":["Screenshot labelled Risultato simulato, not final certified report.",
                     "Defense modifier zero is computed as residual of displayed total, not proven from pure votes.",
                     "No official-source signed/independently timestamped receipt.",
                     "G7 postlock results cannot be used as prelock validation predictions."]}

def main():
    import argparse
    from p0_core import load_config
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True)
    p.add_argument("--config",required=True)
    p.add_argument("--output")
    a=p.parse_args()
    report=reconcile(json.loads(Path(a.input).read_text(encoding="utf-8")),load_config(a.config))
    s=json.dumps(report,ensure_ascii=False,indent=2)+"\n"
    if a.output:Path(a.output).write_text(s,encoding="utf8")
    print(s)
if __name__=="__main__":main()
