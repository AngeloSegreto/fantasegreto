"""G8 intake software tests use synthetic objects; they are NOT pre-match predictions."""
import unittest
from datetime import datetime, timedelta, timezone
from prelock_intake import verify_fixture_calendar, verify_full_roster, validate_probabilities, prepare_intake
from p0_core import decision_hash as canonical_decision_hash

def case():
    now = datetime.now(timezone.utc)
    kick = now + timedelta(days=5)
    games = [{'home': 'T'+str(i), 'away': 'X'+str(i), 'kickoff': kick.isoformat()} for i in range(10)]
    cal = {'league': 'SERIE_A_2026_27', 'matchday': 8,
           'source_url': 'https://www.legaseriea.it/', 'games': games}
    roster = [{'id': role+str(i), 'role': role}
              for role,n in (('P',3),('D',8),('C',8),('A',6)) for i in range(n)]
    xi = ['P0']+[f'D{i}' for i in range(4)]+[f'C{i}' for i in range(4)]+['A0','A1']
    inputs = {'roster': roster, 'starting_xi': xi, 'bench': ['P1','D4','C4','A2'],
              'captain':'A0','vice':'C0','module':'4-4-2','matchday':8,
              'lock_at':(now+timedelta(days=4)).isoformat()}
    decision = {'prediction_status':'SHADOW_PRELOCK','engine_version':'TEST_NOT_REAL',
                'engine_commit_sha':'a'*40,
                'decision_hash':canonical_decision_hash(xi, inputs['bench'], 'A0', 'C0'),
                'snapshot_source':'REAL_ENGINE_OUTPUT',
                'generated_at':(now-timedelta(minutes=1)).isoformat(),
                'model_probabilities':{m:{'V':'0.40','N':'0.20','S':'0.40'}
                                       for m in ('candidate','B0','B1')}}
    config = {'league_id':'NATIONAL_LEAGUE_2026_27',
              'rules':{'allowed_formations':{'values':['4-4-2','3-5-2','4-3-3']}}}
    sources = [{'id':x,'kind':'OBSERVED','observed_at':(now-timedelta(hours=1)).isoformat()}
               for x in ('official-fixture','league-app')]
    return cal,inputs,config,decision,sources,now

class IntakeTest(unittest.TestCase):
    def verify(self, c):
        return prepare_intake(calendar=c[0],inputs=c[1],config=c[2],
                              decision=c[3],sources=c[4],now=c[5])
    def test_valid_structure_without_freeze(self):
        self.assertTrue(self.verify(case()))
    def test_duplicate_team(self):
        c=list(case()); c[0]['games'][1]['home']=c[0]['games'][0]['home']
        with self.assertRaisesRegex(ValueError,'duplicate team'):
            verify_fixture_calendar(c[0])
    def test_lock_after_first_game(self):
        c=list(case()); c[1]['lock_at']=(c[5]+timedelta(days=6)).isoformat()
        with self.assertRaisesRegex(ValueError,'pre-lock'):
            self.verify(c)
    def test_actual_postlock(self):
        c=list(case()); c[1]['lock_at']=(c[5]-timedelta(seconds=1)).isoformat()
        with self.assertRaisesRegex(ValueError,'pre-lock'):
            self.verify(c)
    def test_model_probabilities_mandatory(self):
        c=list(case()); c[3]['model_probabilities'].pop('B1')
        with self.assertRaisesRegex(ValueError,'B0/B1'):
            self.verify(c)
    def test_no_fake_forecast(self):
        c=list(case()); c[3]['snapshot_source']='SYNTHETIC'
        with self.assertRaisesRegex(ValueError,'synthetic'):
            self.verify(c)
    def test_missing_roster_players(self):
        c=list(case()); c[1]['roster'].pop()
        with self.assertRaisesRegex(ValueError,'25 registered'):
            verify_full_roster(c[1])
    def test_duplicate_starter_bench(self):
        c=list(case()); c[1]['bench'].append('P0')
        with self.assertRaisesRegex(ValueError,'duplicate'):
            verify_full_roster(c[1])
    def test_wrong_module(self):
        c=list(case()); c[1]['module']='4-3-3'
        with self.assertRaisesRegex(ValueError,'formation'):
            verify_full_roster(c[1])
    def test_decision_hash_mismatch(self):
        c=list(case()); c[3]['decision_hash']='0'*64
        with self.assertRaisesRegex(ValueError,'identity hash'):
            self.verify(c)
    def test_module_not_allowed(self):
        c=list(case()); c[2]['rules']['allowed_formations']['values']=['3-5-2']
        with self.assertRaisesRegex(ValueError,'allowed formations'):
            self.verify(c)
    def test_future_source(self):
        c=list(case()); c[4][0]['observed_at']=(c[5]+timedelta(seconds=5)).isoformat()
        with self.assertRaisesRegex(ValueError,'future source'):
            self.verify(c)
    def test_unchecked_probabilities(self):
        c=list(case()); c[3]['model_probabilities']['candidate']={'V':'0.6','N':'0.6','S':'-0.2'}
        with self.assertRaisesRegex(ValueError,'probability'):
            validate_probabilities(c[3]['model_probabilities'])
    def test_fractional_valid(self):
        validate_probabilities({k:{'V':'0.45','N':'0.15','S':'0.40'}
                                for k in ('candidate','B0','B1')})

if __name__=='__main__':
    unittest.main()
