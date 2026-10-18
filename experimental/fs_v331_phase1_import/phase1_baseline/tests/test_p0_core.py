import unittest
from pathlib import Path
from decimal import Decimal
from tempfile import TemporaryDirectory
from copy import deepcopy
from fs_p0_core import load_config, fantasy_goals, canonical_identity, sampled_uniform, verify_goal_evidence, promotion_state

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/'league_config.yaml'
SCHEMA=ROOT/'league_config.schema.json'
EVID=ROOT.parent/'evidence'

class ContractTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.c=load_config(str(CONFIG),str(SCHEMA))
 def test_source_sha256(self): self.assertTrue(verify_goal_evidence(self.c,EVID))
 def test_goal_boundaries(self):
  for score,goal in [('65.9',0),('66.0',1),('69.4',1),('69.9',1),('70.0',2),('73.99',2),('74',3),('94',8),('97.5',8),('98',9),('102',10)]:
   with self.subTest(score=score): self.assertEqual(fantasy_goals(score,self.c),goal)
 def test_no_float_binary(self):
  with self.assertRaises(TypeError): fantasy_goals(69.99999999999999,self.c)
 def test_monotonicity(self):
  prev=-1
  for i in range(0,2500):
   val=fantasy_goals(Decimal(i)/Decimal(10),self.c)
   self.assertGreaterEqual(val,prev)
   prev=val
 def test_config_validation_negative(self):
  c=deepcopy(self.c);c['rules']['fantasy_goals']['band_width']='0'
  import json, yaml
  with TemporaryDirectory() as td:
   p=Path(td)/'bad.yaml'; p.write_text(yaml.safe_dump(c))
   with self.assertRaises(ValueError): load_config(str(p),str(SCHEMA))
 def test_input_permutations_starter_invariant(self):
  a=[f'p{i}' for i in range(11)]
  self.assertEqual(canonical_identity(a,['b1','b2'],'p0','p1'),canonical_identity(a[::-1],['b1','b2'],'p0','p1'))
 def test_bench_order_preserved(self):
  a=[f'p{i}' for i in range(11)]
  self.assertNotEqual(canonical_identity(a,['b1','b2'],'p0','p1'),canonical_identity(a,['b2','b1'],'p0','p1'))
 def test_duplicate_identity_negative(self):
  with self.assertRaises(ValueError): canonical_identity(['p']*11,[],'p','p')
 def test_pcg64_per_player_per_scenario_invariant(self):
  ids=['a','b','c']
  x={pid:sampled_uniform(42,pid,11) for pid in ids}
  y={pid:sampled_uniform(42,pid,11) for pid in reversed(ids)}
  self.assertEqual(x,y)
 def test_pcg64_changes_with_scenario(self):
  self.assertNotEqual(sampled_uniform(42,'a',11),sampled_uniform(42,'a',12))
 def test_failclosed_on_missing_rules(self):
  st=promotion_state(self.c)
  self.assertEqual(st['status'],'PROVVISORIO')
  self.assertFalse(st['gold_lock'])
  self.assertIn('defense_modifier',st['not_certified'])
  self.assertIn('captain_factor',st['not_certified'])
if __name__=='__main__': unittest.main()
