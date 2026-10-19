"""FS V3.3.1 SHADOW: paired pre-lock lineup comparison.

Consumes PRE-GENERATED JOINT matchday scenarios, never G7 realized scores,
never assigns invented player probabilities. The event-level generative
model and official opponent fantasy lineup are separate, unverified inputs.

No G14/G15 validation, production promotion or gold=true in this module.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from hashlib import sha256
import json
import math
import random

from fixture_bridge import fixture_bridge
from league_scoring_v331 import score, UncertifiedScoringCase
from p0_core import decision_hash, fantagol

ALLOWED_STATUS={"VOTED","SV","DID_NOT_PLAY"}
MODES={"PUNTI_ATTESI","MAX_VITTORIA"}
FIXTURES_PER_MATCHDAY=10

def _require(value, text):
    if not value: raise ValueError(text)

def _timestamp(value):
    t=datetime.fromisoformat(value)
    _require(t.tzinfo is not None and t.utcoffset() is not None,"timezone required")
    return t

def _fmt(x):
    return format(Decimal(str(x)).quantize(Decimal("0.000001")), "f").rstrip("0").rstrip(".")

def _norm_lineup(lineup,byid,config):
    _require(isinstance(lineup,dict),"lineup record required")
    xi=lineup.get("starting_xi",[])
    bench=lineup.get("bench",[])
    _require(len(xi)==11 and len(set(xi))==11,"11 unique starters required")
    _require(len(set(bench))==len(bench) and not set(xi)&set(bench),"bench duplicate or overlap")
    _require(len(xi+bench)==len(byid),"exactly entire registered fantasy roster in XI/bench")
    _require(set(xi+bench)==set(byid),"unavailable/missing roster players")
    _require(lineup.get("captain") in xi and lineup.get("vice") in xi and lineup["captain"]!=lineup["vice"],"captain or vice not nominated")
    counts={k:sum(byid[i]["role"]==k for i in xi) for k in "PDCA"}
    _require(counts["P"]==1,"one starting goalkeeper required")
    name="-".join(str(counts[x]) for x in "DCA")
    _require(name==lineup.get("module"),"module inconsistent with XI")
    _require(name in config["rules"]["allowed_formations"]["values"],"formation not supported by provisional rules")
    return decision_hash(xi,bench,lineup["captain"],lineup["vice"])

def _to_players(ids,byid,events):
    return [{**byid[pid],**events[pid]} for pid in ids]

def _check_outcomes(data,playerids):
    _require(isinstance(data,dict) and set(data)==playerids,"outcomes must cover every fantasy player exactly")
    for pid,x in data.items():
        _require(isinstance(x,dict) and x.get("status") in ALLOWED_STATUS,"invalid vote status: "+pid)
        if x["status"]=="VOTED":
            for k in ("pure_vote","fantavote"):
                _require(k in x and x[k] is not None,"missing "+k+": "+pid)
                _require(not isinstance(x[k],(bool,float)),"decimal string required: "+pid)
                d=Decimal(str(x[k]))
                bottom,top=(Decimal("0"),Decimal("10")) if k=="pure_vote" else (Decimal("-20"),Decimal("50"))
                _require(d.is_finite() and bottom<=d<=top,"invalid vote: "+pid)
            _require(Decimal(str(x["pure_vote"]))*2 == (Decimal(str(x["pure_vote"]))*2).to_integral_value(),
                     "pure vote off permitted half point tick: "+pid)
        else:
            _require("pure_vote" not in x and "fantavote" not in x,"cannot score non-vote: "+pid)

def _opponent_meta(opponent,config,cal):
    _require(isinstance(opponent,dict),"opponent full fantasy-team input required")
    _require(opponent.get("evidence_kind") in ("SYNTHETIC_UNIT_TEST","AUTHENTICATED_PRELOCK"),
             "opponent source evidence kind required")
    rows=opponent.get("roster")
    _require(isinstance(rows,list) and len(rows)>=11,"full opponent player roster missing")
    oppids=[x.get("id") for x in rows]
    _require(all(isinstance(x,str) and x for x in oppids) and len(set(oppids))==len(oppids),
             "duplicate/unknown opponent IDs")
    _require(set(oppids).isdisjoint(cal),"duplicate fantasy athlete IDs between teams")
    clubs={x["home"] for x in cal}|{x["away"] for x in cal}
    for x in rows:
        _require(x.get("team") in clubs and x.get("role") in ("P","D","C","A"),
                 "unmapped opponent player to Serie A fixture")
    byid={x["id"]:x for x in rows}
    d=_norm_lineup(opponent["lineup"],byid,config)
    return byid,d

def _fixture_key(group):
    return group["home"]+"|"+group["away"]+"|"+group["kickoff"]

def _quantile(sorted_samples,q):
    if not sorted_samples:return 0.0
    pos=(len(sorted_samples)-1)*q
    lo=math.floor(pos);hi=math.ceil(pos)
    return sorted_samples[lo]+(sorted_samples[hi]-sorted_samples[lo])*(pos-lo)

def _bootstrap(values,seed,reps,alpha):
    """Paired scenario bootstrap; MC SE only, not forecast accuracy evidence."""
    n=len(values);rng=random.Random(seed)
    means=[]
    for _ in range(reps):
        means.append(sum(values[rng.randrange(n)] for _ in range(n))/n)
    means.sort()
    return (_quantile(means,alpha/2),_quantile(means,1-alpha/2))

def analyze(roster,calendar,config,candidates,opponent,scenario_bundle,protocol):
    """Compare lineups on SAME joint scenario, with exact league scoring.

    Returns a purely numerical SHADOW comparison only if all common
    scenario evidence is present. Without opponent or scenarios fail closed.
    """
    status={"engine":"FS_V331_SHADOW_PAIRED_SCENARIO_EVALUATOR_V1",
            "GOLD_LOCK":False,"TECH_PASS":False,"STAT_VALIDATED":False,
            "promoted":False,"G14_G15_eligible":False}
    if opponent is None:
        return {**status,"status":"BLOCKED_OPPONENT_G8_FANTASY_LINEUP_MISSING",
                "missing":["OPPONENT_ROSTER","OPPONENT_LINEUP_AND_CAPTAIN"]}
    if not scenario_bundle:
        return {**status,"status":"BLOCKED_NO_PRELOCK_JOINT_SCENARIOS",
                "missing":["JOINT_PRELOCK_SCENARIOS","OPPONENT_FORECAST","OBSERVED_SOURCE_RECEIPTS"]}
    _require(calendar.get("matchday")==8,"matchday 8 fixture calendar required")
    _require(roster.get("status")=="SCREENSHOT_GROUNDED_SHADOW_ONLY","wrong roster source")
    mapped=fixture_bridge(roster,calendar)
    own_byid={p["id"]:p for p in roster["roster"]}
    groups={_fixture_key(g) for g in scenario_bundle.get("joint_fixture_groups",[])}
    legal_groups={_fixture_key(g) for g in calendar["games"]}
    _require(groups==legal_groups and len(scenario_bundle["joint_fixture_groups"])==10,
             "all 10 fixtures must be shared")
    opp_byid,opp_decision=_opponent_meta(opponent,config,calendar["games"])
    all_ids=set(own_byid)|set(opp_byid)
    _require(len(all_ids)==len(own_byid)+len(opp_byid),"player ID collision")
    _require(scenario_bundle.get("matchday")==8,"scenario matchday mismatch")
    _require(scenario_bundle.get("sampling_design")=="IID_JOINT_MATCHDAY_SCENARIOS",
             "invalid sampling design")
    kind=scenario_bundle.get("evidence_kind")
    _require(kind in ("SYNTHETIC_UNIT_TEST","PRELOCK_JOINT_MODEL_OUTPUT"),
             "unrecognized scenario evidence kind")
    _require(_timestamp(scenario_bundle["generated_at"])<=_timestamp(scenario_bundle["lock_at"]),
             "post-lock model generation not allowed")
    _require(_timestamp(scenario_bundle["source_cutoff_at"])<=_timestamp(scenario_bundle["generated_at"]),
             "future data leakage")
    first=min(_timestamp(x["kickoff"]) for x in calendar["games"])
    _require(_timestamp(scenario_bundle["lock_at"])<=first,"league lock must precede first kickoff")
    _require(isinstance(protocol.get("alpha"),(float,int)) and 0<protocol["alpha"]<0.5,
             "preregistered alpha missing")
    _require(isinstance(protocol.get("delta"),(float,int)) and 0<=protocol["delta"]<1,
             "preregistered practical difference margin missing")
    _require(isinstance(protocol.get("seed"),int),"seed required")
    reps=protocol.get("bootstrap_reps")
    _require(isinstance(reps,int) and 100<=reps<=10000,"bootstrap budget invalid")
    _require(protocol.get("profile") in MODES,"profile must be PUNTI_ATTESI or MAX_VITTORIA")
    _require(protocol.get("preregistered_at") and
             _timestamp(protocol["preregistered_at"])<=_timestamp(scenario_bundle["generated_at"]),
             "protocol must be registered before scenarios")

    by_hash={}
    for line in candidates:
        digest=_norm_lineup(line,own_byid,config)
        _require(digest not in by_hash,"duplicate full decision")
        by_hash[digest]=line
    _require(len(by_hash)>=2,"at least two candidates required")
    _require({"4-3-3","4-4-2","3-5-2"}.issubset({c["module"] for c in by_hash.values()}),
             "comparison of all three modules mandatory")

    events=scenario_bundle.get("scenarios")
    _require(isinstance(events,list) and len(events)>=2,"at least two shared joint scenarios required")
    scenario_ids=set()
    values={ident:[] for ident in by_hash}
    ownfantasy={ident:[] for ident in by_hash}
    win={ident:[] for ident in by_hash}
    draw={ident:[] for ident in by_hash}
    lose={ident:[] for ident in by_hash}
    sorted_candidates=sorted(by_hash)
    for evt in events:
        i=evt.get("scenario_id")
        _require(isinstance(i,int) and i>=0 and i not in scenario_ids,"duplicate scenario id")
        scenario_ids.add(i)
        draws=evt.get("player_outcomes")
        _check_outcomes(draws,all_ids)
        # A single joint fixture state is drawn per real Serie A match;
        # player outcomes are passed by the upstream generator, not redrawn.
        states=evt.get("fixture_states")
        _require(isinstance(states,dict) and set(states)==legal_groups,
                 "shared fixture state missing/duplicated")
        for key,state in states.items():
            _require(isinstance(state,dict) and set(state)>={"home_goals","away_goals"},
                     "fixture result absent: "+key)
            for label in ("home_goals","away_goals"):
                z=state[label]
                _require(isinstance(z,int) and not isinstance(z,bool) and 0<=z<=15,
                         "invalid fixture goal count")
        def calc(line,players):
            return score(_to_players(line["starting_xi"],players,draws),
                         _to_players(line["bench"],players,draws),
                         line["captain"],line["vice"],config,fantagol)
        rival=calc(opponent["lineup"],opp_byid)
        for ident in sorted_candidates:
            own=calc(by_hash[ident],own_byid)
            g_own=int(own["fantagoals"])
            g_rival=int(rival["fantagoals"])
            w=int(g_own>g_rival);d=int(g_own==g_rival);l=int(g_own<g_rival)
            win[ident].append(w);draw[ident].append(d);lose[ident].append(l)
            values[ident].append(float(3*w+d) if protocol["profile"]=="PUNTI_ATTESI" else float(w))
            ownfantasy[ident].append(float(Decimal(own["total"])))
    n=len(events)
    measures={}
    for ident in sorted_candidates:
        c=by_hash[ident]
        measures[ident]={
            "module":c["module"],"decision_hash":ident,
            "expected_league_points":sum(3*a+b for a,b in zip(win[ident],draw[ident]))/n,
            "p_win":sum(win[ident])/n,"p_draw":sum(draw[ident])/n,"p_loss":sum(lose[ident])/n,
            "expected_fantapoints":sum(ownfantasy[ident])/n,
            "estimated_primary":sum(values[ident])/n}
    ranked=sorted(sorted_candidates,key=lambda k:(-measures[k]["estimated_primary"],k))
    winner=ranked[0]
    comparisons={}
    for other in ranked[1:]:
        delta=[a-b for a,b in zip(values[winner],values[other])]
        seed=int.from_bytes(sha256(json.dumps([protocol["seed"],min(winner,other),max(winner,other)],
                   separators=(",",":")).encode()).digest()[:8],"big")
        lo,hi=_bootstrap(delta,seed,reps,protocol["alpha"])
        margin=protocol["delta"]
        if lo>margin: verdict="A_SUPERIORE"
        elif hi< -margin: verdict="B_SUPERIORE"
        elif -margin<=lo<=hi<=margin: verdict="EQUIVALENTI_ENTRO_DELTA"
        else: verdict="INCONCLUDENTE"
        comparisons[other]={"paired_delta_estimate":sum(delta)/n,
                            "paired_ci":[lo,hi],"verdict":verdict}
    # Contract V3.3.1: only equivalence within delta permits secondary
    # comparison. INCONCLUDENTE keeps primary point-estimate winner.
    equivalent=[winner]+[k for k,v in comparisons.items()
                         if v["verdict"]=="EQUIVALENTI_ENTRO_DELTA"]
    def secondary(k):
        m=measures[k]
        main_secondary=(m["p_win"] if protocol["profile"]=="PUNTI_ATTESI"
                        else m["expected_league_points"])
        return (-main_secondary,m["p_loss"],
                0 if protocol.get("previous_full_decision_hash")==k else 1,k)
    operational_choice=sorted(equivalent,key=secondary)[0]
    return {**status,"status":"SHADOW_COMPARISON_COMPUTED_UNCALIBRATED",
            "evidence_kind":kind,"claim_external_predictive_validation":False,
            "n_scenarios":n,"profile":protocol["profile"],
            "opponent_decision_hash":opp_decision,"candidate_results":measures,
            "point_estimate_preferred":winner,"operational_choice":operational_choice,
            "decision_method":"V331_EQUIVALENCE_SECONDARY_TIEBREAK_OR_PRIMARY_INCONCLUSIVE",
            "paired_vs_point_estimate_preferred":comparisons,
            "warnings":["No demonstration that input scenarios reproduce real match events.",
                        "G05 event/correlation coherence needs generator-level audit.",
                        "Bootstrap confidence measures MC sampling error, not predictive calibration.",
                        "No real prelock forecasts or verified opponent lineup were supplied to this execution.",
                        "Never treat G7 postmatch votes as input distributions or calibrating holdout."]}
