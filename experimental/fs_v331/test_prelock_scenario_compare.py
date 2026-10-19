"""Synthetic stress tests for V3.3.1 three-module shared-scenario evaluator.

All fixtures here are SYNTHETIC_UNIT_TEST, not calibrated G8 forecasts.
"""
from copy import deepcopy
from datetime import datetime
from pathlib import Path
import json
import unittest
from p0_core import load_config,decision_hash
from prelock_scenario_compare import analyze

HERE=Path(__file__).resolve().parent
ROSTER=json.loads((HERE/"data"/"mall_dealer_roster_20261019.json").read_text())
CAL=json.loads((HERE/"fixtures"/"md08_serie_a_2026_27.json").read_text())
CFG=load_config(HERE/"league_config.yaml")

def make():
    r=ROSTER["roster"]
    grouped={role:[p["id"] for p in r if p["role"]==role] for role in "PDCA"}
    def lineup(ds,cs,attack):
        ids=[grouped["P"][1]]+grouped["D"][:ds]+grouped["C"][:cs]+grouped["A"][:attack]
        return {"starting_xi":ids,"bench":[p["id"] for p in r if p["id"] not in ids],
                "module":f"{ds}-{cs}-{attack}","captain":grouped["A"][0],"vice":grouped["C"][0]}
    cands=[lineup(4,3,3),lineup(4,4,2),lineup(3,5,2)]
    # Non-existent sample opponent, intentionally labelled SYNTHETIC_UNIT_TEST
    opp_roles=["P"]+["D"]*4+["C"]*4+["A"]*2
    teams=["Napoli","Roma","Milan","Juventus","Atalanta",
           "Lecce","Udinese","Bologna","Cagliari","Monza","Sassuolo"]
    opp_roster=[{"id":f"FAKE_O{i}","name":f"SyntheticOpponent{i}","role":role,
                 "team":teams[i]} for i,role in enumerate(opp_roles)]
    opp_lineup={"starting_xi":[p["id"] for p in opp_roster],"bench":[],
                "module":"4-4-2","captain":"FAKE_O10","vice":"FAKE_O9"}
    opponent={"evidence_kind":"SYNTHETIC_UNIT_TEST","roster":opp_roster,"lineup":opp_lineup}
    players=r+opp_roster
    fixture_states={}
    fixture_groups=[]
    for g in CAL["games"]:
        fixture_groups.append(g.copy())
        key="|".join([g["home"],g["away"],g["kickoff"]])
        fixture_states[key]={"home_goals":1,"away_goals":0}
    records=[]
    for scenario_id in range(24):
        outcomes={x["id"]:{"status":"VOTED","pure_vote":"6","fantavote":"6"} for x in players}
        # This C is not starting in 4-3-3, but becomes a starter in 4-4-2 and 3-5-2.
        outcomes[grouped["C"][3]]={"status":"VOTED","pure_vote":"6","fantavote":"12"}
        records.append({"scenario_id":scenario_id,"player_outcomes":outcomes,
                        "fixture_states":deepcopy(fixture_states)})
    scenarios={"matchday":8,"sampling_design":"IID_JOINT_MATCHDAY_SCENARIOS",
               "evidence_kind":"SYNTHETIC_UNIT_TEST",
               "generated_at":"2026-10-20T10:02:00+02:00",
               "source_cutoff_at":"2026-10-20T10:01:00+02:00",
               "lock_at":"2026-10-23T20:30:00+02:00",
               "joint_fixture_groups":fixture_groups,"scenarios":records}
    protocol={"alpha":0.05,"delta":0.05,"seed":314159,"bootstrap_reps":150,
              "profile":"PUNTI_ATTESI","preregistered_at":"2026-10-20T10:00:00+02:00"}
    return [ROSTER,CAL,CFG,cands,opponent,scenarios,protocol]

def run(c):
    return analyze(*c)

class SharedScenarioTest(unittest.TestCase):
    def setUp(self):
        self.c=make()
    def test_three_moduli_single_joint_sample(self):
        result=run(self.c)
        self.assertEqual(result["status"],"SHADOW_COMPARISON_COMPUTED_UNCALIBRATED")
        self.assertEqual(result["n_scenarios"],24)
        self.assertEqual({m["module"] for m in result["candidate_results"].values()},
                         {"4-3-3","4-4-2","3-5-2"})
        self.assertFalse(result["GOLD_LOCK"])
        self.assertFalse(result["STAT_VALIDATED"])
    def test_expected_league_points_win_bigger_than_draw(self):
        r=run(self.c)
        bymod={x["module"]:x for x in r["candidate_results"].values()}
        self.assertEqual(bymod["4-3-3"]["expected_league_points"],1)
        self.assertEqual(bymod["4-4-2"]["expected_league_points"],3)
        self.assertEqual(bymod["3-5-2"]["expected_league_points"],3)
    def test_statistical_superiority_vs_433(self):
        r=run(self.c)
        bymod={x["module"]:x for x in r["candidate_results"].values()}
        id433=bymod["4-3-3"]["decision_hash"]
        self.assertEqual(r["paired_vs_point_estimate_preferred"][id433]["verdict"],"A_SUPERIORE")
    def test_statistical_equivalence_vs_352_or_442(self):
        r=run(self.c)
        other=[k for k,v in r["candidate_results"].items()
               if v["module"] in ("3-5-2","4-4-2") and k!=r["point_estimate_preferred"]][0]
        self.assertEqual(r["paired_vs_point_estimate_preferred"][other]["verdict"],
                         "EQUIVALENTI_ENTRO_DELTA")
    def test_complete_decision_identity_respects_bench_order(self):
        r1=run(self.c)
        self.c[3][0]["bench"][0],self.c[3][0]["bench"][1]=self.c[3][0]["bench"][1],self.c[3][0]["bench"][0]
        r2=run(self.c)
        self.assertNotEqual(
            next(k for k,v in r1["candidate_results"].items() if v["module"]=="4-3-3"),
            next(k for k,v in r2["candidate_results"].items() if v["module"]=="4-3-3"))
    def test_candidate_order_stable(self):
        r1=run(self.c)
        self.c[3].reverse()
        r2=run(self.c)
        self.assertEqual(r1["candidate_results"],r2["candidate_results"])
        self.assertEqual(r1["paired_vs_point_estimate_preferred"],r2["paired_vs_point_estimate_preferred"])
    def test_scenario_order_stable(self):
        r1=run(self.c)
        self.c[5]["scenarios"].reverse()
        r2=run(self.c)
        self.assertEqual(r1["candidate_results"],r2["candidate_results"])
        self.assertEqual(r1["paired_vs_point_estimate_preferred"],r2["paired_vs_point_estimate_preferred"])
    def test_without_opponent_blocked(self):
        self.c[4]=None
        self.assertEqual(run(self.c)["status"],"BLOCKED_OPPONENT_G8_FANTASY_LINEUP_MISSING")
    def test_without_joint_scenarios_blocked(self):
        self.c[5]=None
        self.assertEqual(run(self.c)["status"],"BLOCKED_NO_PRELOCK_JOINT_SCENARIOS")
    def test_missing_scenario_player_blocks(self):
        self.c[5]["scenarios"][0]["player_outcomes"].pop("FAKE_O8")
        with self.assertRaisesRegex(ValueError,"cover every fantasy player"):
            run(self.c)
    def test_missing_fixture_state_blocks(self):
        self.c[5]["scenarios"][0]["fixture_states"].pop(next(iter(self.c[5]["scenarios"][0]["fixture_states"])))
        with self.assertRaisesRegex(ValueError,"shared fixture state"):
            run(self.c)
    def test_future_leakage_blocks(self):
        self.c[5]["source_cutoff_at"]="2026-10-25T18:00:00+01:00"
        with self.assertRaisesRegex(ValueError,"future data leakage"):
            run(self.c)
    def test_postlock_generated_blocks(self):
        self.c[5]["generated_at"]="2026-10-24T12:00:00+02:00"
        with self.assertRaisesRegex(ValueError,"post-lock"):
            run(self.c)
    def test_invalid_sum_of_fantavotes_does_not_override_probabilities(self):
        self.c[5]["scenarios"][0]["player_outcomes"]["FAKE_O1"]["fantavote"]="Infinity"
        with self.assertRaisesRegex(ValueError,"invalid vote"):
            run(self.c)
    def test_negative_fantavotes_allowed_but_not_hypothetical_source_claim(self):
        self.c[5]["scenarios"][0]["player_outcomes"]["FAKE_O1"]["fantavote"]="-0.5"
        result=run(self.c)
        self.assertEqual(result["evidence_kind"],"SYNTHETIC_UNIT_TEST")
        self.assertFalse(result["claim_external_predictive_validation"])
    def test_missing_442_is_rejected(self):
        self.c[3]=[self.c[3][0],self.c[3][2]]
        with self.assertRaisesRegex(ValueError,"all three modules"):
            run(self.c)
    def test_wrong_formation_rejected(self):
        self.c[3][1]["module"]="5-3-2"
        with self.assertRaisesRegex(ValueError,"module inconsistent"):
            run(self.c)
    def test_no_pre_match_opponent_identity_inferred(self):
        self.c[4]["roster"][0]["team"]="Unknown Team"
        with self.assertRaisesRegex(ValueError,"unmapped opponent"):
            run(self.c)
    def test_preregistration_must_precede_forecasts(self):
        self.c[6]["preregistered_at"]="2026-10-20T12:00:00+02:00"
        with self.assertRaisesRegex(ValueError,"protocol must be registered"):
            run(self.c)
    def test_profile_max_win(self):
        self.c[6]["profile"]="MAX_VITTORIA"
        r=run(self.c)
        self.assertEqual(r["profile"],"MAX_VITTORIA")
        self.assertFalse(r["gold_lock"] if "gold_lock" in r else r["GOLD_LOCK"])
    def test_continuity_only_equivalence(self):
        baseline=run(self.c)
        c352=next(k for k,v in baseline["candidate_results"].items() if v["module"]=="3-5-2")
        self.c[6]["previous_full_decision_hash"]=c352
        x=run(self.c)
        self.assertEqual(x["operational_choice"],c352)
    def test_do_not_infer_predictive_model_from_g7(self):
        r=run(self.c)
        self.assertFalse(r["G14_G15_eligible"])
        self.assertTrue(any("G7" in s for s in r["warnings"]))
if __name__=="__main__":unittest.main()
