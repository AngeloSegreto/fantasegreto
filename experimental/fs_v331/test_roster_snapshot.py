"""G8 source-roster gate: no hidden candidate omission and no price-field pollution."""
import json
import pathlib
import unittest
from collections import Counter
from prelock_intake import verify_full_roster

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]
DATA = HERE / "data" / "mall_dealer_roster_20261019.json"

class UserRosterSnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = json.loads(DATA.read_text(encoding="utf-8"))
        cls.roster = cls.snapshot["roster"]
        cls.registry = json.loads((REPO/"registry.json").read_text(encoding="utf-8"))
        cls.by_official_id = {str(p["official_id"]):p for p in cls.registry["players"]}

    def test_exactly_25_all_roles(self):
        self.assertEqual(Counter(p["role"] for p in self.roster),Counter(P=3,D=8,C=8,A=6))
        self.assertEqual(len(self.roster),25)
        self.assertEqual(len(set(p["id"] for p in self.roster)),25)

    def test_all_25_resolve_unique_registry_identity(self):
        for p in self.roster:
            with self.subTest(p=p["name"]):
                current = self.by_official_id[p["id"]]
                self.assertEqual(p["name"],current["name"])
                self.assertEqual(p["team"],current["team"])
                self.assertEqual(p["role"],current["role"])
                self.assertEqual(p["registry_id"],current["id"])

    def test_no_shadow_roster_mutates_auction_prices(self):
        for p in self.roster:
            src=self.by_official_id[p["id"]]
            self.assertNotIn("quote",p)
            self.assertNotIn("fvm",p)
            self.assertIn("league_app_values",p)
            self.assertIsInstance(src["quote"],int)
            self.assertIsInstance(src["fvm"],int)

    def test_image_evidence_three_unique_complete_hashes(self):
        shots=self.snapshot["provenance"]["shots"]
        self.assertEqual(len(shots),3)
        self.assertEqual(len(set(x["sha256"] for x in shots)),3)
        for e in shots:
            self.assertEqual(len(e["sha256"]),64)
            self.assertEqual(len(e["file"]),12)

    def test_unfrozen_shadow_only(self):
        self.assertEqual(self.snapshot["status"],"SCREENSHOT_GROUNDED_SHADOW_ONLY")
        self.assertEqual(self.snapshot["prelock_integrity_status"],"ROSTER_IDENTIFIED_NOT_DECISION_FROZEN")
        self.assertFalse(self.snapshot["provenance"]["raw_files_archived_in_github"])

    def test_budget_snapshot_is_not_auction_budget(self):
        self.assertEqual(self.snapshot["app_display_remaining_credits"],8)
        self.assertNotIn("budget_each",self.snapshot)

    def test_complete_roster_can_enter_intake_with_valid_candidate(self):
        roles={r:[p["id"] for p in self.roster if p["role"]==r] for r in "PDCA"}
        xi=roles["P"][:1]+roles["D"][:4]+roles["C"][:4]+roles["A"][:2]
        bench=[p["id"] for p in self.roster if p["id"] not in set(xi)]
        candidate={"roster":self.roster,"starting_xi":xi,"bench":bench,"module":"4-4-2",
                   "captain":roles["A"][0],"vice":roles["C"][0]}
        self.assertEqual(len(verify_full_roster(candidate)),25)

    def test_snapshot_does_not_invent_pre_match_choice(self):
        for forbidden in ("starting_xi","bench","captain","model_probabilities"):
            self.assertNotIn(forbidden,self.snapshot)

if __name__=="__main__":
    unittest.main()
