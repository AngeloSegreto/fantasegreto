"""FS V3.3.1 SHADOW: validate and enrich the next fantasy rival's roster.

ARTIBANAIKOS complete roster is evidence-grounded by league screenshots.
This is NOT evidence of the opponent's actual G8 XI/captain/ordered bench.
"""
import json
from pathlib import Path

from fixture_bridge import fixture_bridge

def validate_pair(own, rival, fixtures):
    if own.get("fantasy_team") != "Mall & Dealer Sikuli":
        raise ValueError("wrong own fantasy team")
    if rival.get("fantasy_team") != "ARTIBANAIKOS":
        raise ValueError("wrong rival fantasy team")
    if rival.get("assigned_as_matchday8_opponent_by") != "USER_EXPLICIT_STATEMENT":
        raise ValueError("no explicit matchup identification")
    if rival.get("status") != "SCREENSHOT_GROUNDED_SHADOW_ONLY":
        raise ValueError("unknown provenance")
    if not (len(rival.get("provenance",{}).get("shots",[]))==3 and
            all(len(x.get("sha256",""))==64 for x in rival["provenance"]["shots"])):
        raise ValueError("source screenshot manifest incomplete")
    original=fixture_bridge(own,fixtures)
    opponents=fixture_bridge(rival,fixtures)
    ids_a={p["official_id"] for p in original}
    ids_b={p["official_id"] for p in opponents}
    if ids_a & ids_b:
        raise ValueError("shared official athlete across rival fantasy teams")
    if len(ids_a)!=25 or len(ids_b)!=25:
        raise ValueError("incomplete player identity registry")
    for snap,label,remaining in ((own,"Mall & Dealer",8),(rival,"ARTIBANAIKOS",6)):
        rows=snap["roster"]
        counts={c:sum(p["role"]==c for p in rows) for c in "PDCA"}
        if counts!={"P":3,"D":8,"C":8,"A":6}:
            raise ValueError(label+" role distribution invalid")
        if snap["app_display_remaining_credits"] !=remaining:
            raise ValueError(label+" residual budget mismatch")
        if sum(p["league_app_values"]["v_a_visible"] for p in rows)!=500-remaining:
            raise ValueError(label+" acquisition-column budget mismatch")
    return original,opponents

def assessment(own,rival,fixtures):
    us,them=validate_pair(own,rival,fixtures)
    return {
      "schema":"FS_V331_G8_RIVAL_FIXTURE_INTAKE_V1",
      "league":"NATIONAL_LEAGUE_2026_27",
      "matchday":8,
      "matchup":{"home":"Mall & Dealer Sikuli","away":"ARTIBANAIKOS",
                 "evidence":"USER_EXPLICIT_MATCHUP_NOT_SCHEDULE_SCREEN"},
      "roster_status":"BOTH_25_OF_25_REGISTRY_IDS_VERIFIED",
      "rival_acquisition_column_total":494,
      "rival_remaining_credits":6,
      "own_players":sorted(us,key=lambda p:(p["role"],p["name"])),
      "rival_players":sorted(them,key=lambda p:(p["role"],p["name"])),
      "last_rival_observed_module":rival.get("historic_g7_formation_observation",{}).get("module"),
      "last_rival_module_is_g8_confirmed":False,
      "actual_rival_g8_XI":None,
      "actual_rival_g8_bench_order":None,
      "actual_rival_g8_captain":None,
      "actual_rival_g8_vice":None,
      "joint_real_prelock_forecasts":False,
      "prediction_status":"BLOCKED_OPPONENT_G8_LINEUP_AND_JOINT_MODEL_MISSING",
      "G05":"NOT_VERIFIED",
      "G14_G15":"NOT_VERIFIED",
      "gold_lock":False
    }

def main():
    import argparse
    parser=argparse.ArgumentParser()
    for x in ("own","opponent","calendar"):
        parser.add_argument("--"+x,required=True)
    parser.add_argument("--out")
    args=parser.parse_args()
    load=lambda path:json.loads(Path(path).read_text(encoding="utf8"))
    data=assessment(load(args.own),load(args.opponent),load(args.calendar))
    out=json.dumps(data,indent=2,ensure_ascii=False)+"\n"
    if args.out: Path(args.out).write_text(out,encoding="utf8")
    print(out,end="")

if __name__=="__main__":main()
