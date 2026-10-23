"""Configuration-first Fantasy scoring tests using user-supplied league settings."""
import pathlib
import sys
import unittest
from decimal import Decimal
here = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(here))
from p0_core import load_config, fantagol
from league_scoring_v331 import modifier, captain_bonus, substitutes, score, UncertifiedScoringCase, D

def player(id, role, pure='6.5', fantasy=None):
    return {'id': id, 'role': role, 'pure_vote': pure,
            'fantavote': fantasy if fantasy is not None else pure}

def xi(v='6.5'):
    return ([player('P0','P',v)] +
            [player(f'D{i}','D',v) for i in range(4)] +
            [player(f'C{i}','C',v) for i in range(4)] +
            [player(f'A{i}','A',v) for i in range(2)])

class OfficialConfigScoring(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = load_config(here/'league_config.yaml')
    def test_all_five_receipts_sha_present(self):
        e = self.cfg['evidence_receipts']
        for name in ('substitution','bonus_malus','defensive_modifier','captain_factor','defensive_modifier_info'):
            self.assertEqual(len(e[name]['sha256']),64)
    def test_substitutions_certified(self):
        r = self.cfg['rules']['substitution']
        self.assertEqual(r['status'],'CERTIFICATA')
        self.assertEqual(r['mode'],'TRADITIONAL')
        self.assertEqual(r['max_changes'],5)
        self.assertFalse(r['office_reserve_enabled'])
        self.assertFalse(r['module_change_allowed'])
    def test_defense_bands(self):
        for val, expected in [('5.9','0'),('6','0'),('6.24','0'),('6.25','0.5'),
                              ('6.49','0.5'),('6.5','1'),('6.74','1'),
                              ('6.75','1.5'),('6.99','1.5'),('7','2'),('7.5','2')]:
            with self.subTest(val=val):
                self.assertEqual(modifier(xi(val),self.cfg), D(expected))
    def test_best_three_and_goalkeeper_not_fantavote(self):
        x = xi('6.5')
        x[0]['pure_vote'] = '7'
        x[0]['fantavote'] = '10'
        x[4]['pure_vote'] = '3'
        x[1]['fantavote'] = '9'
        # top 3 Ds each 6.5, GK 7 => 6.625 -> +1
        self.assertEqual(modifier(x,self.cfg),Decimal('1'))
    def test_three_defenders_no_modifier(self):
        x = [p for p in xi('7') if p['id']!='D3']
        self.assertEqual(modifier(x,self.cfg),Decimal('0'))
    def test_fourth_defender_sv_fail_closed(self):
        x=xi();x[4]['pure_vote']=None
        with self.assertRaises(UncertifiedScoringCase):
            modifier(x,self.cfg)
    def test_goalkeeper_sv_fail_closed(self):
        x=xi();x[0]['pure_vote']=None
        with self.assertRaises(UncertifiedScoringCase):
            modifier(x,self.cfg)
    def test_captain_bands(self):
        for vote, bonus in [('4','-1.5'),('4.5','-1.5'),('5','-1'),
                            ('5.5','0'),('6','0'),('6.5','0'),('7','1'),
                            ('7.5','1.5'),('8','1.5')]:
            with self.subTest(vote=vote):
                x=xi();x[-1]['pure_vote']=vote
                self.assertEqual(captain_bonus(x,'A1','C0',self.cfg),D(bonus))
    def test_captain_non_tick_fails(self):
        x=xi();x[-1]['pure_vote']='7.25'
        with self.assertRaises(UncertifiedScoringCase):
            captain_bonus(x,'A1','C0',self.cfg)
    def test_captain_sv_to_vice(self):
        x=xi();x[-1]['pure_vote']=None
        x[-3]['pure_vote']='7.5'
        self.assertEqual(captain_bonus(x,'A1','C3',self.cfg),Decimal('1.5'))
    def test_captain_and_vice_sv_zero(self):
        x=xi();x[-1]['pure_vote']=None;x[-3]['pure_vote']=None
        self.assertEqual(captain_bonus(x,'A1','C3',self.cfg),Decimal('0'))
    def test_traditional_same_role_preserves_module(self):
        x=xi();x[5]['pure_vote']=None
        b=[player('A2','A','10'),player('C4','C','9.5'),player('C5','C','8')]
        r=substitutes(x,b,self.cfg)
        self.assertEqual(r['replacements'],[{'out':'C0','in':'C4'}])
        self.assertEqual(sum(p['role']=='C' for p in r['xi']),4)
    def test_no_reserve_if_no_eligible_same_role(self):
        x=xi();x[5]['pure_vote']=None
        r=substitutes(x,[player('A2','A','10')],self.cfg)
        self.assertEqual(r['replacements'],[])
        self.assertEqual(r['without_vote'],['C0'])
    def test_bench_priority_first_eligible_vote(self):
        x=xi();x[5]['pure_vote']=None
        b=[player('C5','C',None),player('C6','C','8'),player('C7','C','10')]
        r=substitutes(x,b,self.cfg)
        self.assertEqual(r['replacements'][0]['in'],'C6')
    def test_more_than_five_same_role_absences_failclosed(self):
        x=xi()
        for p in x[1:7]:p['pure_vote']=None
        b=[player('D'+str(i),'D','6') for i in range(4,8)]+[player('C'+str(i),'C','6') for i in range(4,8)]
        with self.assertRaises(UncertifiedScoringCase):
            substitutes(x,b,self.cfg)
    def test_full_score_uses_fantavotes_once(self):
        x=xi('6.5');x[10]['fantavote']='9.5'
        z=score(x,[],'A1','C0',self.cfg,fantagol)
        self.assertEqual(z['base'],str(Decimal('6.5')*11+3))
        self.assertEqual(z['defense_modifier'],'1')
        self.assertEqual(z['captain_factor'],'0')
        self.assertEqual(z['total'],'75.5')
        self.assertEqual(z['fantagoals'],3)
    def test_captain_substitute_does_not_inherit_band(self):
        x=xi('6.5')
        x[-1]['pure_vote']=None;x[-1]['fantavote']=None
        x[5]['pure_vote']='7'
        b=[player('A2','A','7.5')]
        z=score(x,b,'A1','C0',self.cfg,fantagol)
        self.assertEqual(z['captain_factor'],'1')
    def test_float_rejected(self):
        with self.assertRaises(TypeError):
            D(7.0)

if __name__=='__main__':
    unittest.main()
