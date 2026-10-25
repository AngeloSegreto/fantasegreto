import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from fs_decision_protocol import compare_paired, append_decision_record, verify_decision_ledger

class PairedComparisonTests(unittest.TestCase):
 def test_A_significantly_superior(self):
  r=compare_paired(['V']*100,['S']*100,'PUNTI_ATTESI',.1,identity_a='a'*64,identity_b='b'*64)
  self.assertEqual(r['verdetto'],'A SUPERIORE')
  self.assertEqual(r['decisione_operativa'],'A')
 def test_B_significantly_superior(self):
  r=compare_paired(['S']*100,['V']*100,'MAX_VITTORIA',.1,identity_a='a'*64,identity_b='b'*64)
  self.assertEqual(r['verdetto'],'B SUPERIORE')
 def test_equivalent_canonical(self):
  r=compare_paired(['V','N','S']*50,['V','N','S']*50,'PUNTI_ATTESI',.05,identity_a='b'*64,identity_b='a'*64)
  self.assertEqual(r['verdetto'],'EQUIVALENTI ENTRO δ')
  self.assertEqual(r['decisione_operativa'],'B')
 def test_inconclusive_uses_primary_not_secondary(self):
  # A primary higher, despite alternate secondary interest, wide CI
  r=compare_paired(['V','S','S','S'],['N','N','S','S'],'MAX_VITTORIA',.01,identity_a='b'*64,identity_b='a'*64)
  self.assertEqual(r['verdetto'],'INCONCLUDENTE')
  self.assertEqual(r['decisione_operativa'],'A')
 def test_refuse_unpaired_inputs(self):
  with self.assertRaises(ValueError):compare_paired(['V'],['S','S'],'PUNTI_ATTESI',.1,identity_a='a',identity_b='b')
 def test_refuse_invalid_prob_outcomes(self):
  with self.assertRaises(ValueError):compare_paired(['V','X'],['S','S'],'PUNTI_ATTESI',.1,identity_a='a',identity_b='b')

class PrelockTests(unittest.TestCase):
 def test_append_and_chain(self):
  with TemporaryDirectory() as d:
   p=Path(d)/'ledger.jsonl'; t='2026-10-18T19:00:00+02:00';lock='2026-10-18T20:45:00+02:00'
   append_decision_record(p,kind='RECOMMENDATION',observed_at=t,lock_at=lock,decision_sha256='a'*64,input_sha256='b'*64,config_sha256='c'*64)
   append_decision_record(p,kind='OVERRIDE',observed_at=t,lock_at=lock,decision_sha256='a'*64,actual_decision_sha256='d'*64,input_sha256='b'*64,config_sha256='c'*64)
   self.assertTrue(verify_decision_ledger(p)['valid'])
   self.assertEqual(verify_decision_ledger(p)['count'],2)
 def test_postlock_rejected(self):
  with TemporaryDirectory() as d:
   with self.assertRaises(ValueError):append_decision_record(Path(d)/'x',kind='RECOMMENDATION',observed_at='2026-10-18T21:00:00+02:00',lock_at='2026-10-18T20:45:00+02:00',decision_sha256='a'*64,input_sha256='b'*64,config_sha256='c'*64)
 def test_tampered_detected(self):
  with TemporaryDirectory() as d:
   p=Path(d)/'ledger.jsonl'
   append_decision_record(p,kind='RECOMMENDATION',observed_at='2026-10-18T19:00:00+02:00',lock_at='2026-10-18T20:45:00+02:00',decision_sha256='a'*64,input_sha256='b'*64,config_sha256='c'*64)
   s=p.read_text();p.write_text(s.replace('RECOMMENDATION','OVERRIDE'))
   self.assertFalse(verify_decision_ledger(p)['valid'])
 def test_override_without_actual_rejected(self):
  with TemporaryDirectory() as d:
   with self.assertRaises(ValueError):append_decision_record(Path(d)/'x',kind='OVERRIDE',observed_at='2026-10-18T19:00:00+02:00',lock_at='2026-10-18T20:45:00+02:00',decision_sha256='a'*64,input_sha256='b'*64,config_sha256='c'*64)

if __name__=='__main__':unittest.main()
