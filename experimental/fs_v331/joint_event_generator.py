#!/usr/bin/env python3
"""FS V3.3.1 native joint event generator. Deterministic, offline, SHADOW.

One Serie A fixture is drawn once per scenario; real-match goals, scorer,
assist, team shock, vote statuses and keeper conceded goals are shared by both
fantasy teams. No calibrated forecast or provenance attestation is claimed.
"""
from __future__ import annotations
import argparse
from datetime import datetime
from hashlib import sha256
import json
import math
from pathlib import Path
import random

SCHEMA = "FS_NATIVE_JOINT_EVENT_GENERATOR_V1"
MAX_SCENARIOS = 10000  # A JSON bundle of 50 player observations per scenario grows quickly.

class InputError(ValueError):
    """Input cannot be trusted to generate a matchday scenario."""

def require(ok, message):
    if not ok:
        raise InputError(message)

def number(v, name, low, high):
    require(not isinstance(v, bool) and isinstance(v, (float, int)) and
            math.isfinite(v) and low <= v <= high, f"{name} must be finite in [{low},{high}]")
    return float(v)

def stamp(s):
    try:
        d = datetime.fromisoformat(s)
    except (TypeError, ValueError) as exc:
        raise InputError("timestamp must be ISO-8601") from exc
    require(d.tzinfo is not None and d.utcoffset() is not None, "timestamp requires UTC offset")
    return d

def canonical_hash(o):
    return sha256(json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()

def fixture_key(game):
    return "|".join((game["home"], game["away"], game["kickoff"]))

def poisson(rng, mean):
    """Exact Poisson inversion for bounded per-match intensities."""
    threshold = math.exp(-mean)
    k, product = 0, 1.0
    while True:
        k += 1
        product *= rng.random()
        if product <= threshold:
            return k - 1

def weighted(rng, choices):
    total = sum(w for _, w in choices)
    require(total > 0, "empty sampling weights")
    p = rng.random() * total
    for key, weight in choices:
        p -= weight
        if p < 0:
            return key
    return choices[-1][0]

def validate(calendar, players, parameters, times, n):
    require(isinstance(n, int) and not isinstance(n, bool) and 1 <= n <= MAX_SCENARIOS,
            f"scenario count must be 1..{MAX_SCENARIOS}")
    require(isinstance(calendar, dict) and isinstance(calendar.get("matchday"), int), "calendar matchday missing")
    games = calendar.get("games")
    require(isinstance(games, list) and len(games) == 10, "calendar requires ten fixtures")
    keys, teams = set(), set()
    for game in games:
        require(all(isinstance(game.get(k), str) and game[k] for k in ("home", "away", "kickoff")),
                "fixture missing club/kickoff")
        require(game["home"] != game["away"], "club plays itself")
        stamp(game["kickoff"])
        key = fixture_key(game)
        require(key not in keys, "duplicate fixture")
        keys.add(key)
        for club in (game["home"], game["away"]):
            require(club not in teams, "a club appears in multiple fixtures")
            teams.add(club)
    require(len(teams) == 20, "exactly twenty unique clubs required")
    require(isinstance(players, list) and len(players) >= 1, "player roster missing")
    ids = set()
    for p in players:
        require(isinstance(p, dict) and all(isinstance(p.get(k), str) and p[k]
                 for k in ("id", "team", "role")), "player identity missing")
        require(p["id"] not in ids, "duplicate player id across fantasy rosters")
        ids.add(p["id"])
        require(p["team"] in teams and p["role"] in "PDCA", "player team or classic role not mapped")
    require(isinstance(parameters, dict) and parameters.get("source_kind") in
            ("SYNTHETIC_UNIT_TEST", "EXPLORATORY_ASSUMED"),
            "uncertified parameter mode: fail closed")
    fixture_params = parameters.get("fixtures")
    pp = parameters.get("players")
    require(isinstance(fixture_params, dict) and set(fixture_params) == keys,
            "every fixture needs one parameter record")
    require(isinstance(pp, dict) and set(pp) == ids, "every registered player needs parameters")
    for key, f in fixture_params.items():
        for k in ("home_goal_mean", "away_goal_mean"):
            number(f.get(k), key + "." + k, 0, 5)
        number(f.get("shared_pace_shape"), "shared_pace_shape", 0.1, 1000)
        number(f.get("assist_event_probability"), "assist_event_probability", 0, 1)
        for k in ("other_scorer_weight", "other_assist_weight"):
            number(f.get(k), key + "." + k, 0.001, 100)
    gks_by_team = {}
    for p in players:
        q = pp[p["id"]]
        for k, a, b in (("pure_mean",3,9),("pure_sd",0,3),("vote_probability",0,1),
                        ("scorer_weight",0,100),("assist_weight",0,100),
                        ("yellow_probability",0,1),("red_probability",0,1)):
            number(q.get(k), p["id"] + "." + k, a, b)
        require(q["red_probability"] + q["yellow_probability"] <= 1.000000001,
                "red and yellow rates must sum <=1")
        if p["role"] == "P":
            require(q["scorer_weight"] == 0 and q["assist_weight"] == 0 and
                    q["red_probability"] == 0, "goalkeeper unsupported attacking/red events")
            gks_by_team[p["team"]] = gks_by_team.get(p["team"], 0) + q["vote_probability"]
    require(all(v <= 1.000000001 for v in gks_by_team.values()),
            "team goalkeeper start probabilities sum above one")
    require(isinstance(times, dict), "timestamps missing")
    source, generated, lock = (stamp(times[k]) for k in
                               ("source_cutoff_at", "generated_at", "lock_at"))
    require(source <= generated <= lock <= min(stamp(g["kickoff"]) for g in games),
            "future leakage, post-lock generation or invalid kickoff order")
    return games, pp, fixture_params

def sample_one(rng, games, players, pp, fixture_params, scenario_id):
    by_team = {}
    for p in players:
        by_team.setdefault(p["team"], []).append(p)
    outcomes, fixtures = {}, {}
    for game in games:
        key = fixture_key(game)
        f = fixture_params[key]
        home, away = game["home"], game["away"]
        pace = rng.gammavariate(f["shared_pace_shape"], 1.0 / f["shared_pace_shape"])
        home_goals = poisson(rng, pace * f["home_goal_mean"])
        away_goals = poisson(rng, pace * f["away_goal_mean"])
        active = {}
        state = {}
        performance_shock = {home: rng.gauss(0, 0.25), away: rng.gauss(0, 0.25)}
        for club in (home, away):
            members = by_team.get(club, [])
            gks = [p for p in members if p["role"] == "P"]
            if gks:
                # At most one rated keeper for the same real club in this simplified
                # model. Remaining mass represents a keeper outside the fantasy rosters.
                chosen = weighted(rng, [(p["id"], pp[p["id"]]["vote_probability"])
                                       for p in gks if pp[p["id"]]["vote_probability"] > 0]
                                  + [(None, max(0, 1 - sum(pp[p["id"]]["vote_probability"]
                                                         for p in gks)))])
            else:
                chosen = None
            active[club] = set()
            for p in members:
                q = pp[p["id"]]
                voted = (p["id"] == chosen) if p["role"] == "P" else rng.random() < q["vote_probability"]
                state[p["id"]] = {"status": "VOTED" if voted else "DID_NOT_PLAY", "fixture_ref": key}
                if voted:
                    active[club].add(p["id"])
                    score_differential = ((home_goals - away_goals) if club == home else
                                          (away_goals - home_goals))
                    pure = max(3., min(9., round((rng.gauss(q["pure_mean"], q["pure_sd"])
                                  + performance_shock[club] + 0.10 * score_differential) * 2) / 2))
                    state[p["id"]].update(pure_vote=f"{pure:g}", _pure=pure,
                                           goals=0, assists=0, yellow=0, red=0)
        goal_events = []
        for club, goals in ((home, home_goals), (away, away_goals)):
            for _ in range(goals):
                roster_scorers = [(p["id"], pp[p["id"]]["scorer_weight"])
                                  for p in by_team.get(club, [])
                                  if p["id"] in active[club] and pp[p["id"]]["scorer_weight"] > 0]
                scorer = weighted(rng, roster_scorers + [(None, f["other_scorer_weight"])])
                if scorer is not None:
                    state[scorer]["goals"] += 1
                assist = None
                if rng.random() < f["assist_event_probability"]:
                    roster_assisters = [(p["id"], pp[p["id"]]["assist_weight"])
                                        for p in by_team.get(club, [])
                                        if p["id"] in active[club] and p["id"] != scorer and
                                        pp[p["id"]]["assist_weight"] > 0]
                    assist = weighted(rng, roster_assisters + [(None, f["other_assist_weight"])])
                    if assist is not None:
                        state[assist]["assists"] += 1
                goal_events.append({"scoring_club": club, "scorer_player_id": scorer,
                                    "assist_player_id": assist})
        for club in (home, away):
            conceded = away_goals if club == home else home_goals
            for p in by_team.get(club, []):
                record = state[p["id"]]
                if record["status"] != "VOTED":
                    continue
                q = pp[p["id"]]
                if p["role"] == "P":
                    # Keeper is modelled as a 90-minute starter; saves/penalties
                    # and mid-match keeper substitutions remain unsupported.
                    penalty = -conceded + (1 if conceded == 0 else 0)
                    record["conceded_goals"] = conceded
                else:
                    x = rng.random()
                    record["red"] = int(x < q["red_probability"])
                    record["yellow"] = int(q["red_probability"] <= x <
                                           q["red_probability"] + q["yellow_probability"])
                    penalty = 3 * record["goals"] + record["assists"] \
                              - 0.5 * record["yellow"] - record["red"]
                fantavote = record.pop("_pure") + penalty
                record["fantavote"] = f"{fantavote:g}"
                # Extra event diagnostics are carried by fixture state, not
                # player outcome, so legacy league scoring stays compatible.
                for k in ("goals", "assists", "yellow", "red", "conceded_goals"):
                    record.pop(k, None)
        outcomes.update(state)
        fixtures[key] = {"home_goals": home_goals, "away_goals": away_goals,
                         "goals": goal_events, "shared_pace": round(pace, 6)}
    return {"scenario_id": scenario_id, "fixture_states": fixtures, "player_outcomes": outcomes}

def generate(calendar, players, parameters, times, *, count, seed):
    games, pp, fixture_params = validate(calendar, players, parameters, times, count)
    require(isinstance(seed, int) and not isinstance(seed, bool) and 0 <= seed < 2**64,
            "seed must be uint64")
    rng = random.Random(seed)
    # IMPORTANT: comparator accepts SYNTHETIC_UNIT_TEST as uncalibrated data.
    # Never set PRELOCK_JOINT_MODEL_OUTPUT from unvalidated parameters.
    return {"schema": SCHEMA, "matchday": calendar["matchday"],
            "sampling_design": "IID_JOINT_MATCHDAY_SCENARIOS",
            "evidence_kind": "SYNTHETIC_UNIT_TEST", "source_parameter_kind": parameters["source_kind"],
            "STAT_VALIDATED": False, "GOLD_LOCK": False, "G05_EVENT_COHERENCE_TESTED": True,
            "G05_EXTERNAL_VALIDATION": False, "source_cutoff_at": times["source_cutoff_at"],
            "generated_at": times["generated_at"], "lock_at": times["lock_at"],
            "seed": seed, "parameter_sha256": canonical_hash(parameters),
            "joint_fixture_groups": games,
            "scenarios": [sample_one(rng, games, players, pp, fixture_params, i)
                          for i in range(count)],
            "limitations": ["Uncalibrated input probabilities", "GK always full match if voted",
                            "No own goals, penalties, explicit saves or keeper substitution",
                            "Goals by players outside these two rosters represented by null IDs",
                            "Requires historical backtest G14/G15 before any predictive claim"]}

def synthetic_parameters(calendar, players):
    """Explicit opt-in example parameters only. Never treat as observed data."""
    base_vote = {"P": 0.80, "D": 0.80, "C": 0.82, "A": 0.76}
    scorer = {"P": 0, "D": 0.15, "C": 0.55, "A": 1.6}
    assister = {"P": 0, "D": 0.3, "C": 0.9, "A": 0.7}
    counts = {}
    for p in players:
        if p["role"] == "P":
            counts[p["team"]] = counts.get(p["team"], 0) + 1
    return {"source_kind": "SYNTHETIC_UNIT_TEST", "fixtures": {
        fixture_key(g): {"home_goal_mean": 1.3, "away_goal_mean": 1.1,
                         "shared_pace_shape": 6, "assist_event_probability": 0.6,
                         "other_scorer_weight": 5., "other_assist_weight": 5.}
        for g in calendar["games"]},
        "players": {p["id"]: {
            "pure_mean": 6., "pure_sd": .70,
            "vote_probability": (.80 / counts[p["team"]] if p["role"] == "P"
                                 else base_vote[p["role"]]),
            "scorer_weight": scorer[p["role"]], "assist_weight": assister[p["role"]],
            "yellow_probability": 0.12 if p["role"] != "P" else 0.,
            "red_probability": 0.015 if p["role"] != "P" else 0.
        } for p in players}}

def cli(argv=None):
    parser = argparse.ArgumentParser(description="FantaSegreto native joint matchday SHADOW generator")
    parser.add_argument("--calendar", required=True)
    parser.add_argument("--own-roster", required=True)
    parser.add_argument("--opponent-roster", required=True)
    parser.add_argument("--parameters")
    parser.add_argument("--synthetic-demo", action="store_true",
                        help="Generate explicitly fabricated demo parameters, never for real predictions")
    parser.add_argument("--count", type=int, default=250)
    parser.add_argument("--seed", type=int, default=33111)
    for k in ("source-cutoff-at", "generated-at", "lock-at"):
        parser.add_argument("--" + k, required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    load = lambda path: json.loads(Path(path).read_text(encoding="utf-8"))
    calendar = load(args.calendar)
    rosters = [load(args.own_roster), load(args.opponent_roster)]
    players = [p for r in rosters for p in r["roster"]]
    require(args.synthetic_demo != bool(args.parameters),
            "choose exactly one of --synthetic-demo or --parameters")
    params = synthetic_parameters(calendar, players) if args.synthetic_demo else load(args.parameters)
    times = {"source_cutoff_at": args.source_cutoff_at,
             "generated_at": args.generated_at, "lock_at": args.lock_at}
    bundle = generate(calendar, players, params, times, count=args.count, seed=args.seed)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(bundle, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": "SHADOW_SYNTHETIC_GENERATED", "path": str(output),
                      "scenarios": args.count, "fixtures": 10, "players": len(players),
                      "sha256": sha256(output.read_bytes()).hexdigest(),
                      "GOLD_LOCK": False}, ensure_ascii=False))

if __name__ == "__main__":
    cli()
