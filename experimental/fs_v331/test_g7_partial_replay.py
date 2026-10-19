"""G7 live partial replay tests: prevent postmatch/prelock data leakage."""
import copy
import json
from pathlib import Path
import unittest
from g7_partial_replay import reconcile, reconcile_side

PATH=Path(__file__).resolve().parent/"data"/"g7_live_partial_20261019.json"

class G7LiveReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot=json.loads(PATH.read_text(encoding="utf8"))

    def test_partial_scoreboard_exact(self):
        o=reconcile(self.snapshot)
        self.assertEqual(o["home"]["voted_titulars_sum"],"50")
        self.assertEqual(o["away"]["voted_titulars_sum"],"60.5")

    def test_wesley_replaced_by_cambiaso(self):
        o=reconcile(self.snapshot)
        self.assertEqual(o["home"]["known_substituted_sum"],"56")
        self.assertEqual(o["home"]["substitutions"],[{"out":"Wesley","in":"Cambiaso","fantavote":"6"}])

    def test_adzic_replaced_by_perrone(self):
        o=reconcile(self.snapshot)
        self.assertEqual(o["away"]["known_substituted_sum"],"66.5")
        self.assertEqual(o["away"]["substitutions"],[{"out":"Adzic","in":"Perrone","fantavote":"6"}])

    def test_maldini_not_replaced_while_pending(self):
        o=reconcile(self.snapshot)
        self.assertEqual(o["home"]["pending_starters"],["Maldini"])
        self.assertNotIn("Maldini",[x["out"] for x in o["home"]["substitutions"]])

    def test_simeone_not_replaced_while_pending(self):
        o=reconcile(self.snapshot)
        self.assertEqual(o["away"]["pending_starters"],["Simeone"])

    def test_no_final_replay_certified(self):
        o=reconcile(self.snapshot)
        self.assertEqual(o["release_status"],"SHADOW_LIVE_PARTIAL_ONLY")
        self.assertFalse(o["gold_lock"])
        self.assertFalse(o["stat_validated"])
        self.assertFalse(o["prematch_prediction"])

    def test_historical_screen_never_prelock_forecast(self):
        s=copy.deepcopy(self.snapshot)
        s["strict_context"]["prelock_evidence"]=True
        with self.assertRaisesRegex(ValueError,"historical snapshot"):
            reconcile(s)

    def test_player_state_not_invented(self):
        for side in ("home","away"):
            players=self.snapshot[side]["starters"]+self.snapshot[side]["bench"]
            self.assertTrue(all(x["status"] in ("SV","DID_NOT_PLAY","PENDING_MATCH","VOTED") for x in players))
            self.assertTrue(all("fantavote" not in x for x in players if x["status"]!="VOTED"))

    def test_tampered_scoreboard_rejected(self):
        s=copy.deepcopy(self.snapshot)
        s["scoreboard"]["home_partial_titulars_fantavotes"]="52"
        with self.assertRaisesRegex(ValueError,"scoreboard mismatch"):
            reconcile(s)

    def test_cannot_count_missing_pending_as_vote(self):
        s=copy.deepcopy(self.snapshot)
        s["home"]["starters"][9]["status"]="SV"
        o=reconcile(s)
        self.assertNotIn("Maldini",o["home"]["pending_starters"])

if __name__=="__main__":
    unittest.main()
