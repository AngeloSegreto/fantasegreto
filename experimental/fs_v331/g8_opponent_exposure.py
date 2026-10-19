"""Structural opponent-exposure intelligence for FS V3.3.1 G8 SHADOW.

No model probabilities are generated; roster membership is NOT a forecast
of who will start. Each match's player pools are joined to the same fixture.
"""
from __future__ import annotations
import json
from pathlib import Path
from g8_opponent_bridge import validate_pair

def build_exposure(own, rival, fixture_calendar):
    own_rows,rival_rows=validate_pair(own,rival,fixture_calendar)
    fixtures=fixture_calendar["games"]
    byteam={"Mall & Dealer Sikuli":own_rows,"ARTIBANAIKOS":rival_rows}
    byname=lambda rows,team,roles: sorted(
        [p["name"] for p in rows if p["team"]==team and p["role"] in roles])
    games=[]
    for game in sorted(fixtures,key=lambda g:(g["kickoff"],g["home"],g["away"])):
        home,away=game["home"],game["away"]
        groups={}
        for club,rows in byteam.items():
            groups[club]={
              "home":byname(rows,home,"PDCA"),
              "away":byname(rows,away,"PDCA")
            }
        games.append({"fixture":home+"-"+away,"home":home,"away":away,
                      "kickoff":game["kickoff"],"fantasy_teams":groups})
    keepers=[]
    for side,roster,other in (("OURS",own_rows,rival_rows),("RIVAL",rival_rows,own_rows)):
        for goalkeeper in sorted([p for p in roster if p["role"]=="P"],key=lambda p:p["name"]):
            attacker_opposition=byname(other,goalkeeper["opponent"],"A")
            other_match_players=byname(other,goalkeeper["opponent"],"PDCA")
            keepers.append({
              "owner":side,
              "goalkeeper":goalkeeper["name"],
              "goalkeeper_club":goalkeeper["team"],
              "match_opponent_club":goalkeeper["opponent"],
              "fixture":goalkeeper["home"]+"-"+goalkeeper["away"],
              "rival_fantasy_attackers_playing_against_this_goalkeeper":attacker_opposition,
              "rival_fantasy_players_on_opposing_real_club":other_match_players,
              "warning":"STRUCTURAL_ONLY_OPPONENT_PLAYERS_NOT_CONFIRMED_TO_START"
            })
    return {"schema":"FS_V331_G8_OPPONENT_EXPOSURE_GRAPH_V1",
            "status":"SHADOW_ROSTER_FIXTURE_JOIN_VERIFIED_NO_MATCH_PROBABILITIES",
            "fantasy_match":{"ours":"Mall & Dealer Sikuli","opponent":"ARTIBANAIKOS","matchday":8},
            "game_count":len(games),"players_count":{team:len(players) for team,players in byteam.items()},
            "serie_a_games":games,"keeper_exposures":keepers,
            "source_limits":["User-declared fantasy opponent, not a screenshot of the G8 fantasy fixture screen.",
                             "Rival roster verified, G8 starting XI/bench and captain not yet known.",
                             "Fixture membership does not imply playing probability or guarantee goals.",
                             "No credit values or G7 realized fantasy scores enter the forecast model."],
            "validated_predictive_accuracy":False,"can_generate_win_probability":False,
            "g05_joint_match_statistical_coherence_verified":False,
            "gold_lock":False}

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    for x in ("own","opponent","calendar"):p.add_argument("--"+x,required=True)
    p.add_argument("--output")
    a=p.parse_args()
    load=lambda fn:json.loads(Path(fn).read_text(encoding="utf8"))
    result=build_exposure(load(a.own),load(a.opponent),load(a.calendar))
    data=json.dumps(result,indent=2,ensure_ascii=False,sort_keys=True)+"\n"
    if a.output:Path(a.output).write_text(data,encoding="utf8")
    print(data,end="")
