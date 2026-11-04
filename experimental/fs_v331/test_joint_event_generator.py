"""Offline unit tests for native event generator; all fixtures synthetic."""
import copy
from datetime import datetime, timedelta, timezone
import unittest
from joint_event_generator import InputError, generate, synthetic_parameters, fixture_key


def make_data():
    now = datetime(2030, 5, 5, 10, tzinfo=timezone.utc)
    games = [{"home": f"H{i}", "away": f"A{i}",
              "kickoff": (now + timedelta(days=2, hours=i)).isoformat()}
             for i in range(10)]
    cal = {"matchday": 31, "games": games}
    players = [{"id": "PH", "role": "P", "team": "H0"},
               {"id": "PH2", "role": "P", "team": "H0"},
               {"id": "PA", "role": "P", "team": "A0"},
               {"id": "SC", "role": "A", "team": "H0"},
               {"id": "AS", "role": "C", "team": "H0"},
               {"id": "ES", "role": "D", "team": "A0"}]
    times = {"source_cutoff_at": now.isoformat(),
             "generated_at": (now + timedelta(minutes=5)).isoformat(),
             "lock_at": (now + timedelta(days=1)).isoformat()}
    pars = synthetic_parameters(cal, players)
    for pid in ("SC", "AS", "ES"):
        pars["players"][pid]["vote_probability"] = 1.0
    for g in games[1:]:
        pars["fixtures"][fixture_key(g)]["home_goal_mean"] = 0
        pars["fixtures"][fixture_key(g)]["away_goal_mean"] = 0
    return cal, players, pars, times


class GeneratorTest(unittest.TestCase):
    def test_seed_is_reproducible(self):
        a = make_data()
        self.assertEqual(generate(*a, count=10, seed=1), generate(*a, count=10, seed=1))
        self.assertNotEqual(generate(*a, count=10, seed=1)["scenarios"],
                            generate(*a, count=10, seed=2)["scenarios"])

    def test_joint_goals_assists_and_keepers(self):
        a = make_data()
        bundle = generate(*a, count=200, seed=712)
        self.assertEqual(bundle["evidence_kind"], "SYNTHETIC_UNIT_TEST")
        self.assertFalse(bundle["STAT_VALIDATED"])
        for row in bundle["scenarios"]:
            states = row["fixture_states"]
            self.assertEqual(len(states), 10)
            first = states[fixture_key(a[0]["games"][0])]
            goals = first["goals"]
            self.assertEqual(sum(e["scoring_club"] == "H0" for e in goals), first["home_goals"])
            self.assertEqual(sum(e["scoring_club"] == "A0" for e in goals), first["away_goals"])
            voted = row["player_outcomes"]
            self.assertLessEqual(sum(voted[p]["status"] == "VOTED" for p in ("PH", "PH2")), 1)
            for e in goals:
                if e["scorer_player_id"] is not None and e["assist_player_id"] is not None:
                    self.assertNotEqual(e["scorer_player_id"], e["assist_player_id"])
                if e["scorer_player_id"]:
                    self.assertEqual(voted[e["scorer_player_id"]]["status"], "VOTED")
                if e["assist_player_id"]:
                    self.assertEqual(voted[e["assist_player_id"]]["status"], "VOTED")
            for keeper in ("PH", "PH2"):
                if voted[keeper]["status"] == "VOTED":
                    self.assertEqual(float(voted[keeper]["fantavote"]) - float(voted[keeper]["pure_vote"]),
                                     -first["away_goals"] + (first["away_goals"] == 0))
            if voted["PA"]["status"] == "VOTED":
                self.assertEqual(float(voted["PA"]["fantavote"]) - float(voted["PA"]["pure_vote"]),
                                 -first["home_goals"] + (first["home_goals"] == 0))
            self.assertEqual(set(voted), {x["id"] for x in a[1]})
            for outcome in voted.values():
                if outcome["status"] == "VOTED":
                    self.assertEqual(2 * float(outcome["pure_vote"]),
                                     int(2 * float(outcome["pure_vote"])))
                else:
                    self.assertNotIn("pure_vote", outcome)
                    self.assertNotIn("fantavote", outcome)

    def test_goal_components_exact_when_no_cards(self):
        a = make_data()
        for p in a[2]["players"].values():
            p["yellow_probability"] = 0
            p["red_probability"] = 0
        bundle = generate(*a, count=100, seed=24)
        key = fixture_key(a[0]["games"][0])
        for scenario in bundle["scenarios"]:
            events = scenario["fixture_states"][key]["goals"]
            for pid in ("SC", "AS", "ES"):
                d = scenario["player_outcomes"][pid]
                goals = sum(e["scorer_player_id"] == pid for e in events)
                assists = sum(e["assist_player_id"] == pid for e in events)
                self.assertEqual(float(d["fantavote"]) - float(d["pure_vote"]),
                                 3 * goals + assists)

    def test_invalid_goals_and_missing_player_rejected(self):
        a = list(make_data())
        a[2] = copy.deepcopy(a[2]); a[2]["players"].pop("SC")
        with self.assertRaisesRegex(InputError, "every registered player"):
            generate(*a, count=2, seed=1)
        a = list(make_data()); a[2]["fixtures"][fixture_key(a[0]["games"][0])]["home_goal_mean"] = -1
        with self.assertRaisesRegex(InputError, "home_goal_mean"):
            generate(*a, count=2, seed=1)

    def test_keeper_probabilities_must_sum_at_most_one(self):
        a = list(make_data())
        a[2]["players"]["PH"]["vote_probability"] = .9
        a[2]["players"]["PH2"]["vote_probability"] = .9
        with self.assertRaisesRegex(InputError, "keeper start probabilities"):
            generate(*a, count=3, seed=2)

    def test_same_club_twice_invalid(self):
        a = list(make_data())
        a[0]["games"][1]["home"] = "H0"
        with self.assertRaisesRegex(InputError, "multiple fixtures"):
            generate(*a, count=2, seed=2)

    def test_future_leakage_rejected(self):
        a = list(make_data())
        a[3] = dict(a[3], generated_at="2030-05-08T01:00:00+00:00")
        with self.assertRaisesRegex(InputError, "future leakage"):
            generate(*a, count=2, seed=2)

    def test_uncertified_source_rejected(self):
        a = list(make_data())
        a[2]["source_kind"] = "OFFICIAL_VERIFIED_GOLD"
        with self.assertRaisesRegex(InputError, "fail closed"):
            generate(*a, count=2, seed=2)

    def test_not_enough_fixtures_rejected(self):
        a = list(make_data()); a[0]["games"].pop()
        with self.assertRaisesRegex(InputError, "ten fixtures"):
            generate(*a, count=2, seed=2)

    def test_no_zero_scorer_issue(self):
        a = list(make_data())
        a[2]["players"]["SC"]["vote_probability"] = 0
        a[2]["players"]["AS"]["vote_probability"] = 0
        a[2]["players"]["ES"]["vote_probability"] = 0
        bundle = generate(*a, count=10, seed=2)
        self.assertEqual(len(bundle["scenarios"]), 10)

    def test_synthetic_only_no_gold_even_with_exploratory_inputs(self):
        a = list(make_data()); a[2]["source_kind"] = "EXPLORATORY_ASSUMED"
        r = generate(*a, count=2, seed=20)
        self.assertEqual(r["evidence_kind"], "SYNTHETIC_UNIT_TEST")
        self.assertFalse(r["GOLD_LOCK"])

if __name__ == "__main__":
    unittest.main()
