"""MD8 fixture bridge tests based on roster screenshot and provisional calendar."""
import pathlib
import sys
import unittest
here=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(here))
from fixture_bridge import load_and_bridge,fixture_bridge,correlated_match_groups

class FixtureBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=load_and_bridge(here)
        cls.by_name={x["name"]:x for x in cls.rows}
    def test_shared_match_groups_cover_all_25_once(self):
        groups=correlated_match_groups(self.rows)
        flattened=[x for g in groups for x in g["player_ids"]]
        self.assertEqual(len(flattened),25)
        self.assertEqual(len(set(flattened)),25)
        self.assertEqual(set(flattened),{p["official_id"] for p in self.rows})

    def test_both_goalkeepers_share_one_match_draw(self):
        groups=correlated_match_groups(self.rows)
        game=[g for g in groups if {g["home"],g["away"]}=={"Napoli","Roma"}]
        self.assertEqual(len(game),1)
        self.assertTrue({"572","610","5841","7181"}.issubset(game[0]["player_ids"]))

    def test_lazio_and_juventus_group_no_duplicate(self):
        groups=correlated_match_groups(self.rows)
        game=[g for g in groups if (g["home"],g["away"])==("Lecce","Juventus")]
        self.assertEqual(len(game),1)
        self.assertIn("5951",game[0]["player_ids"])
        self.assertIn("5029",game[0]["player_ids"])

    def test_shared_groups_permutation_invariant(self):
        a=correlated_match_groups(self.rows)
        b=correlated_match_groups(self.rows[::-1])
        self.assertEqual(a,b)

    def test_shared_groups_reject_duplicate_id(self):
        with self.assertRaisesRegex(ValueError,"duplicate"):
            correlated_match_groups(self.rows+[self.rows[0]])

    def test_25_fixture_rows(self):
        self.assertEqual(len(self.rows),25)
        self.assertEqual(len({x["official_id"] for x in self.rows}),25)
    def test_meret_gollini_share_same_match(self):
        m=self.by_name["Meret"]
        g=self.by_name["Gollini"]
        self.assertEqual(m["home"],"Napoli")
        self.assertEqual(m["away"],"Roma")
        self.assertEqual(m["kickoff"],g["kickoff"])
        self.assertEqual(m["venue"],"HOME")
        self.assertEqual(g["venue"],"AWAY")
    def test_svilar_gollini_same_team(self):
        self.assertEqual(self.by_name["Svilar"]["kickoff"],self.by_name["Gollini"]["kickoff"])
        self.assertEqual(self.by_name["Svilar"]["team"],"Roma")
    def test_juventus_lecce_opposites(self):
        self.assertEqual(self.by_name["Kolo Muani"]["opponent"],"Lecce")
        self.assertEqual(self.by_name["Kolo Muani"]["venue"],"AWAY")
        self.assertEqual(self.by_name["Geubbels"]["opponent"],"Juventus")
        self.assertEqual(self.by_name["Geubbels"]["venue"],"HOME")
    def test_midfield_all_mapped(self):
        ids=[r for r in self.rows if r["role"]=="C"]
        self.assertEqual(len(ids),8)
        self.assertTrue(all(p["kickoff"] and p["opponent"] for p in ids))
    def test_no_fantapoints_leakage(self):
        for r in self.rows:
            for forbidden in ("score","predicted_vote","fantapoints","probability"):
                self.assertNotIn(forbidden,r)
    def test_deterministic_against_roster_row_permutation(self):
        import json
        rs=json.loads((here/"data"/"mall_dealer_roster_20261019.json").read_text())
        fx=json.loads((here/"fixtures"/"md08_serie_a_2026_27.json").read_text())
        first=fixture_bridge(rs,fx)
        rs["roster"].reverse()
        second=fixture_bridge(rs,fx)
        self.assertEqual({x["official_id"]:x for x in first},
                         {x["official_id"]:x for x in second})
    def test_nonexistent_team_fails_closed(self):
        import json
        rs=json.loads((here/"data"/"mall_dealer_roster_20261019.json").read_text())
        fx=json.loads((here/"fixtures"/"md08_serie_a_2026_27.json").read_text())
        rs["roster"][0]["team"]="NOT_A_SERIE_A_CLUB"
        with self.assertRaisesRegex(ValueError,"team not in"):
            fixture_bridge(rs,fx)
    def test_duplicate_club_in_fixture_fails_closed(self):
        import json
        rs=json.loads((here/"data"/"mall_dealer_roster_20261019.json").read_text())
        fx=json.loads((here/"fixtures"/"md08_serie_a_2026_27.json").read_text())
        fx["games"][0]["home"]="Napoli"
        with self.assertRaisesRegex(ValueError,"duplicate"):
            fixture_bridge(rs,fx)

if __name__=="__main__":
    unittest.main()
