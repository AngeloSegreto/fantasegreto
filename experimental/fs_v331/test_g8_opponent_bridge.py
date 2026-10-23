"""G8 ARTIBANAIKOS intake tests: real screenshot roster != future match XI."""
import copy
import json
from pathlib import Path
import unittest

from g8_opponent_bridge import validate_pair,assessment
from prelock_scenario_compare import analyze
from p0_core import load_config

ROOT=Path(__file__).resolve().parent
OWN=json.loads((ROOT/"data"/"mall_dealer_roster_20261019.json").read_text(encoding="utf-8"))
RIVAL=json.loads((ROOT/"data"/"artibanaikos_roster_20261019.json").read_text(encoding="utf-8"))
CAL=json.loads((ROOT/"fixtures"/"md08_serie_a_2026_27.json").read_text(encoding="utf-8"))
CFG=load_config(ROOT/"league_config.yaml")

class G8OpponentTests(unittest.TestCase):
    def test_roster_both_25_of_25(self):
        a,b=validate_pair(OWN,RIVAL,CAL)
        self.assertEqual(len(a),25)
        self.assertEqual(len(b),25)
        self.assertFalse(set(x["official_id"] for x in a)&set(x["official_id"] for x in b))
    def test_roles_exact(self):
        self.assertEqual(RIVAL["role_count"],{"P":3,"D":8,"C":8,"A":6})
    def test_494_spent_plus_six_credits(self):
        self.assertEqual(RIVAL["total_va_column"],494)
        self.assertEqual(RIVAL["total_va_plus_remaining_credits"],500)
    def test_three_real_screenshots_manifest_only(self):
        self.assertEqual(len(RIVAL["provenance"]["shots"]),3)
        self.assertFalse(RIVAL["provenance"]["raw_files_archived_in_github"])
    def test_no_g8_lineup_inferred_from_g7(self):
        self.assertEqual(RIVAL["historic_g7_formation_observation"]["module"],"3-4-3")
        self.assertFalse(RIVAL["historic_g7_formation_observation"]["use_as_g8_lineup"])
        self.assertIsNone(RIVAL["matchday8_starting_xi"])
        self.assertIsNone(RIVAL["matchday8_captain"])
    def test_rivals_serie_a_opponent_for_all_25(self):
        a,b=validate_pair(OWN,RIVAL,CAL)
        self.assertTrue(all(x["opponent"] and x["kickoff"] for x in b))
        byname={p["name"]:p for p in b}
        self.assertEqual(byname["Hojlund"]["opponent"],"Roma")
        self.assertEqual(byname["Soulè"]["opponent"],"Napoli")
        self.assertEqual(byname["Yildiz"]["opponent"],"Lecce")
        self.assertEqual(byname["De Ketelaere"]["opponent"],"Frosinone")
        self.assertEqual(byname["Mastantuono"]["opponent"],"Inter")
    def test_mixed_shared_real_fixture(self):
        a,b=validate_pair(OWN,RIVAL,CAL)
        allplayers=a+b
        napoli_roma=[p for p in allplayers if {p["home"],p["away"]}=={"Napoli","Roma"}]
        names={p["name"] for p in napoli_roma}
        self.assertTrue({"Meret","Gollini","Svilar","Wesley","Hojlund","Molina N.","Soulè"}.issubset(names))
    def test_assessment_explicitly_blocks_predictions(self):
        a=assessment(OWN,RIVAL,CAL)
        self.assertEqual(a["prediction_status"],"BLOCKED_OPPONENT_G8_LINEUP_AND_JOINT_MODEL_MISSING")
        self.assertFalse(a["gold_lock"])
    def test_comparator_fails_closed_for_opponent_roster_only(self):
        a=analyze(OWN,CAL,CFG,[],RIVAL,None,{})
        self.assertEqual(a["status"],"BLOCKED_OPPONENT_G8_LINEUP_NOT_PROVIDED")
        self.assertEqual(a["roster_registry_matched"],25)
        self.assertFalse(a["usable_for_lineup_submission"])
    def test_duplicate_athlete_in_both_squads_blocks(self):
        x=copy.deepcopy(RIVAL)
        x["roster"][0]["id"]=OWN["roster"][0]["id"]
        with self.assertRaisesRegex(ValueError,"shared official athlete"):
            validate_pair(OWN,x,CAL)
    def test_missing_rival_player_blocks(self):
        x=copy.deepcopy(RIVAL)
        x["roster"].pop()
        with self.assertRaisesRegex(ValueError,"incomplete roster"):
            validate_pair(OWN,x,CAL)
    def test_duplicate_real_fixture_club_blocks(self):
        x=copy.deepcopy(CAL)
        x["games"][1]["home"]=x["games"][0]["home"]
        with self.assertRaisesRegex(ValueError,"duplicate or missing team"):
            validate_pair(OWN,RIVAL,x)
    def test_wrong_credit_sum_blocks(self):
        x=copy.deepcopy(RIVAL)
        x["roster"][0]["league_app_values"]["v_a_visible"]=100
        with self.assertRaisesRegex(ValueError,"budget mismatch"):
            validate_pair(OWN,x,CAL)
    def test_missing_photo_hash_blocks(self):
        x=copy.deepcopy(RIVAL)
        x["provenance"]["shots"][0]["sha256"]="xxxx"
        with self.assertRaisesRegex(ValueError,"manifest incomplete"):
            validate_pair(OWN,x,CAL)
    def test_no_magic_historical_winning_forecast(self):
        a=assessment(OWN,RIVAL,CAL)
        self.assertFalse(a["joint_real_prelock_forecasts"])
        self.assertEqual(a["G14_G15"],"NOT_VERIFIED")
if __name__=="__main__":unittest.main()
