"""V3.3.1 SHADOW: link the user's full roster to Serie A matchday fixtures.
No fantasy point forecasts and no implicit opponent-strength estimates.
"""
import json
from pathlib import Path
from datetime import datetime

def fixture_bridge(roster_snapshot, fixtures):
    roster=roster_snapshot.get("roster")
    games=fixtures.get("games")
    if not isinstance(roster,list) or len(roster)!=25 or not isinstance(games,list) or len(games)!=10:
        raise ValueError("incomplete roster/fixture dataset")
    all_teams=[]
    by_team={}
    for game in games:
        a,b=game.get("home"),game.get("away")
        t=datetime.fromisoformat(game.get("kickoff",""))
        if t.tzinfo is None or t.utcoffset() is None:
            raise ValueError("timezone required for every fixture")
        if not a or not b or a==b:
            raise ValueError("invalid fixture")
        all_teams.extend([a,b])
        by_team[a]={"opponent":b,"venue":"HOME","kickoff":game["kickoff"],"home":a,"away":b}
        by_team[b]={"opponent":a,"venue":"AWAY","kickoff":game["kickoff"],"home":a,"away":b}
    if len(set(all_teams))!=20:
        raise ValueError("duplicate or missing team in fixture calendar")
    rows=[]
    used=set()
    for p in roster:
        pid=str(p.get("id",""))
        if pid in used or not pid:
            raise ValueError("duplicate or missing official player ID")
        used.add(pid)
        team=p.get("team")
        if team not in by_team:
            raise ValueError("team not in matchday fixture calendar: "+str(team))
        row={"official_id":pid, "registry_id":p.get("registry_id"),"name":p["name"],
             "role":p["role"],"team":team,**by_team[team]}
        rows.append(row)
    if len(rows)!=25 or len(used)!=25:
        raise ValueError("roster completeness violation")
    return rows


def correlated_match_groups(rows):
    """Structural match groups; score-model coefficients are not inferred here.

    Players in the same real fixture MUST share one simulated match outcome.
    The goalkeeper of either club can never receive an independently drawn
    score for a separate copy of that real fixture.
    """
    if not isinstance(rows, list) or not rows:
        raise ValueError("player-to-fixture rows required")
    groups={}
    seen=set()
    for p in rows:
        pid=str(p.get("official_id",""))
        if not pid or pid in seen:
            raise ValueError("duplicate/missing canonical player")
        seen.add(pid)
        home,away,kickoff=p["home"],p["away"],p["kickoff"]
        if p["team"] not in (home,away) or p["opponent"] == p["team"]:
            raise ValueError("malformed real-fixture relation")
        key=(kickoff,home,away)
        g=groups.setdefault(key,{"kickoff":kickoff,"home":home,"away":away,"player_ids":[]})
        g["player_ids"].append(pid)
    result=sorted(groups.values(),key=lambda x:(x["kickoff"],x["home"],x["away"]))
    for g in result:
        g["player_ids"].sort(key=lambda x:(0,int(x)) if x.isdecimal() else (1,x))
    return result

def load_and_bridge(root):
    root=Path(root)
    roster=json.loads((root/"data"/"mall_dealer_roster_20261019.json").read_text(encoding="utf8"))
    fixtures=json.loads((root/"fixtures"/"md08_serie_a_2026_27.json").read_text(encoding="utf8"))
    return fixture_bridge(roster,fixtures)

if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--fs-v331-directory",default=str(Path(__file__).resolve().parent))
    args=parser.parse_args()
    print(json.dumps(load_and_bridge(args.fs_v331_directory),indent=2,ensure_ascii=False))
