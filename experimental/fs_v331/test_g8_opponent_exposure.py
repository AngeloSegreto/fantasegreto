"""G8 player-to-fixture exposures, no prediction or confirmed rival XI."""
import json
from pathlib import Path
import unittest
from g8_opponent_exposure import build_exposure
from g8_opponent_bridge import validate_pair

ROOT=Path(__file__).resolve().parent
read=lambda p:json.loads((ROOT/p).read_text(encoding="utf8"))
OWN=read("data/mall_dealer_roster_20261019.json")
RIVAL=read("data/artibanaikos_roster_20261019.json")
CAL=read("fixtures/md08_serie_a_2026_27.json")

class G8StructuralExposureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.v=build_exposure(OWN,RIVAL,CAL)
        cls.k={ (x["owner"],x["goalkeeper"]):x for x in cls.v["keeper_exposures"]}
    def test_ten_joint_fixtures(self):
        self.assertEqual(len(self.v["serie_a_games"]),10)
        self.assertEqual(self.v["game_count"],10)
        self.assertEqual(self.v["players_count"],{"Mall & Dealer Sikuli":25,"ARTIBANAIKOS":25})
    def test_every_athlete_in_exact_one_real_match(self):
        for fantasy_name, roster in (("Mall & Dealer Sikuli",OWN),("ARTIBANAIKOS",RIVAL)):
            in_groups=[]
            for game in self.v["serie_a_games"]:
                in_groups+=game["fantasy_teams"][fantasy_name]["home"]
                in_groups+=game["fantasy_teams"][fantasy_name]["away"]
            self.assertEqual(len(in_groups),25)
            self.assertEqual(set(in_groups),{x["name"] for x in roster["roster"]})
    def test_meret_exposed_to_soule(self):
        p=self.k["OURS","Meret"]
        self.assertEqual(p["fixture"],"Napoli-Roma")
        self.assertIn("Soulè",p["rival_fantasy_attackers_playing_against_this_goalkeeper"])
        self.assertNotIn("Hojlund",p["rival_fantasy_attackers_playing_against_this_goalkeeper"])
    def test_gollini_exposed_to_hojlund(self):
        for name in ("Gollini","Svilar"):
            p=self.k["OURS",name]
            self.assertEqual(p["fixture"],"Napoli-Roma")
            self.assertIn("Hojlund",p["rival_fantasy_attackers_playing_against_this_goalkeeper"])
    def test_opponent_palmisani_exposed_to_our_raspadori(self):
        p=self.k["RIVAL","Palmisani"]
        self.assertEqual(p["fixture"],"Atalanta-Frosinone")
        self.assertIn("Raspadori",p["rival_fantasy_attackers_playing_against_this_goalkeeper"])
    def test_g8_not_assigned_expected_winner(self):
        self.assertFalse(self.v["can_generate_win_probability"])
        self.assertFalse(self.v["validated_predictive_accuracy"])
        self.assertFalse(self.v["gold_lock"])
        self.assertFalse(self.v["g05_joint_match_statistical_coherence_verified"])
    def test_correct_role_and_injury_are_not_inferred(self):
        self.assertTrue(any("not yet known" in x for x in self.v["source_limits"]))
        self.assertEqual(len(self.v["keeper_exposures"]),6)
    def test_deterministic_after_reordering_roster(self):
        import copy
        own=copy.deepcopy(OWN)
        rival=copy.deepcopy(RIVAL)
        own["roster"].reverse()
        rival["roster"].reverse()
        self.assertEqual(build_exposure(own,rival,CAL),self.v)

if __name__=="__main__":unittest.main()
