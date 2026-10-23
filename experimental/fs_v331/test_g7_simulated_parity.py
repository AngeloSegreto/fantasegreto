"""Observe real G7 app simulation parity only. NEVER G16/GOLD validation."""
import copy
import json
import pathlib
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from p0_core import load_config
from g7_simulated_parity import reconcile,EvidenceConflict
ROOT=pathlib.Path(__file__).resolve().parent
SNAP=json.loads((ROOT/"data"/"g7_app_simulated_20261019.json").read_text(encoding="utf-8"))
CFG=load_config(ROOT/"league_config.yaml")

class ObservedSimulatedG7(unittest.TestCase):
    def test_exact_60_74_reconciliation(self):
        r=reconcile(SNAP,CFG)
        self.assertEqual(r["home"]["platform_total"],"60")
        self.assertEqual(r["away"]["platform_total"],"74")
        self.assertEqual(r["home"]["fantagoals"],0)
        self.assertEqual(r["away"]["fantagoals"],3)
        self.assertEqual(r["status"],"APP_SIMULATED_TOTAL_DECOMPOSITION_PASS")
    def test_known_substitutions_factor_and_simeone(self):
        r=reconcile(SNAP,CFG)
        self.assertEqual(r["home"]["starter_partial"],"55")
        self.assertEqual(r["home"]["included_later_and_substitutions"],"6")
        self.assertEqual(r["home"]["captain_factor_observed"],"-1")
        self.assertEqual(r["away"]["starter_partial"],"60.5")
        self.assertEqual(r["away"]["included_later_and_substitutions"],"12")
        self.assertEqual(r["away"]["captain_factor_observed"],"1.5")
    def test_zero_modifier_is_inferred_not_certified(self):
        r=reconcile(SNAP,CFG)
        self.assertEqual(r["home"]["modifier_residual_inferred"],"0")
        self.assertEqual(r["away"]["modifier_residual_inferred"],"0")
        self.assertEqual(r["G09"],"NO_INDEPENDENT_PURE_VOTE_REPLAY")
        self.assertEqual(r["G16"],"DA_VERIFICARE")
    def test_not_official_and_never_prelock(self):
        r=reconcile(SNAP,CFG)
        self.assertFalse(r["gold_lock"])
        self.assertFalse(r["stat_validated"])
        self.assertFalse(r["g14_g15_eligible"])
        self.assertFalse(SNAP["raw_screenshots_saved_in_repo"])
    def test_all_10_sha256_attachments_referenced(self):
        ss=SNAP["screenshots"]
        self.assertEqual(len(ss),10)
        self.assertEqual(len({x["sha256"] for x in ss}),10)
        for x in ss:self.assertEqual(len(x["sha256"]),64)
    def test_goal_bands_against_platform(self):
        other=SNAP["matches"][1]["simulated_platform"]
        self.assertEqual(other["home_goals"],1)
        self.assertEqual(other["away_goals"],1)
    def test_unverified_last_fixture_not_marked_official(self):
        self.assertEqual(SNAP["matches"][2]["status"],"STARTER_PARTIAL_ONLY_NOT_OFFICIAL_FINAL")
    def test_reject_forged_final_status(self):
        x=copy.deepcopy(SNAP);x["status"]="OFFICIAL_FINAL"
        with self.assertRaises(EvidenceConflict):reconcile(x,CFG)
    def test_reject_data_leakage(self):
        x=copy.deepcopy(SNAP);x["use_as_prelock_prediction"]=True
        with self.assertRaises(EvidenceConflict):reconcile(x,CFG)
    def test_reject_tampered_home_captain(self):
        x=copy.deepcopy(SNAP);x["matches"][0]["independently_visible_components"]["home"]["captain_factor"]="0"
        with self.assertRaises(EvidenceConflict):reconcile(x,CFG)
    def test_reject_tampered_simeone_vote(self):
        x=copy.deepcopy(SNAP);x["matches"][0]["independently_visible_components"]["away"]["simeone_fantavote"]="5.5"
        with self.assertRaises(EvidenceConflict):reconcile(x,CFG)
    def test_reject_platform_wrong_goals(self):
        x=copy.deepcopy(SNAP);x["matches"][0]["simulated_platform"]["home_goals"]=1
        with self.assertRaises(EvidenceConflict):reconcile(x,CFG)
    def test_reject_platform_wrong_total(self):
        x=copy.deepcopy(SNAP);x["matches"][0]["simulated_platform"]["away_total"]="75"
        with self.assertRaises(EvidenceConflict):reconcile(x,CFG)
    def test_reject_substitute_wrong_role(self):
        x=copy.deepcopy(SNAP);x["matches"][0]["independently_visible_components"]["home"]["true_subs"][0]["role"]="C"
        with self.assertRaises(EvidenceConflict):reconcile(x,CFG)
if __name__=="__main__":unittest.main()
