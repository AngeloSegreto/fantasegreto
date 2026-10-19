"""Run from repo root: python -m unittest discover -s experimental/fs_v331 -p 'test_*.py'."""
import unittest, pathlib, sys
from decimal import Decimal
here=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(here))
from p0_core import load_config, fantagol, decision_hash, uniform, promotion_state

class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=load_config(here/'league_config.yaml')
    def test_threshold_boundary_table(self):
        for x,y in [('65.9',0),('66.0',1),('69.4',1),('70.0',2),('94.0',8),('98.0',9)]:
            with self.subTest(x=x):
                self.assertEqual(fantagol(x,self.cfg),y)
    def test_float_rejected(self):
        with self.assertRaises(TypeError):fantagol(70.0,self.cfg)
    def test_monotonic(self):
        f=[fantagol(Decimal(i)/10,self.cfg) for i in range(600,1011)]
        self.assertEqual(f,sorted(f))
    def test_identity_bench_order(self):
        a=['p'+str(i) for i in range(11)]
        x=decision_hash(a,['b1','b2'],'p0','p1')
        self.assertEqual(x,decision_hash(a[::-1],['b1','b2'],'p0','p1'))
        self.assertNotEqual(x,decision_hash(a,['b2','b1'],'p0','p1'))
    def test_pcg64_input_permutation(self):
        a={k:uniform(42,k,13) for k in 'abc'}
        b={k:uniform(42,k,13) for k in 'cba'}
        self.assertEqual(a,b)
    def test_failclosed_certification_transition(self):
        import copy
        baseline = promotion_state(self.cfg)
        self.assertEqual(set(baseline['uncertified']), set())
        self.assertNotIn('captain_factor', baseline['uncertified'])
        self.assertEqual(baseline['status'], 'RULES_VERIFIED_ONLY')
        self.assertFalse(baseline['TECH_PASS'])
        self.assertFalse(baseline['STAT_VALIDATED'])
        self.assertFalse(baseline['GOLD_LOCK'])
        degraded = copy.deepcopy(self.cfg)
        degraded['rules']['captain_factor']['status'] = 'MANCANTE'
        result = promotion_state(degraded)
        self.assertIn('captain_factor', result['uncertified'])
        self.assertEqual(result['status'], 'PROVVISORIO')
        self.assertFalse(result['TECH_PASS'])
        self.assertFalse(result['STAT_VALIDATED'])
        self.assertFalse(result['GOLD_LOCK'])
        for rule in ('classic_roles', 'allowed_formations'):
            degraded_rule = copy.deepcopy(self.cfg)
            degraded_rule['rules'][rule]['status'] = 'PROVVISORIA'
            gated = promotion_state(degraded_rule)
            self.assertIn(rule, gated['uncertified'])
            self.assertFalse(gated['GOLD_LOCK'])
    def test_failclosed(self):
        s=promotion_state(self.cfg)
        self.assertEqual(s['status'],'RULES_VERIFIED_ONLY')
        self.assertNotIn('allowed_formations',s['uncertified'])
        self.assertNotIn('bonus_malus',s['uncertified'])
        self.assertNotIn('classic_roles',s['uncertified'])
        self.assertNotIn('captain_factor',s['uncertified'])
        self.assertNotIn('defense_modifier',s['uncertified'])
        self.assertFalse(s['GOLD_LOCK'])
if __name__=='__main__':unittest.main()
