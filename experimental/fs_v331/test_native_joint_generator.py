"""Event coherence and fail-closed software tests; no forecast validation."""
import unittest
from native_joint_generator import generate, audit, digest, poisson
import random


def mock_data():
    clubs=['Roma','Napoli','Inter','Milan','Juventus','Bologna','Monza','Atalanta','Udinese','Parma',
           'Lazio','Cagliari','Torino','Sassuolo','Como','Fiorentina','Genoa','Lecce','Venezia','Frosinone']
    games=[{'home':clubs[i], 'away':clubs[i+1], 'kickoff':f'2030-11-{7+i//6:02d}T{15+i%4:02d}:00:00+01:00'}
           for i in range(0,len(clubs),2)]
    roster=[]; rival=[]
    for i in range(25):
        role='P' if i<3 else 'D' if i<11 else 'C' if i<19 else 'A'
        roster.append({'id':'OWN'+str(i).zfill(2),'team':clubs[i%20],'role':role,'name':'Own'+str(i)})
        rival.append({'id':'OPP'+str(i).zfill(2),'team':clubs[(i+7)%20],'role':role,'name':'Opp'+str(i)})
    cal={'matchday':11,'games':games}
    own={'roster':roster}
    opp={'roster':rival}
    pri={'schema':'FS_NATIVE_JOINT_PRIORS_V1','evidence_kind':'SYNTHETIC_UNIT_TEST',
         'players':{},'fixtures':{}}
    for p in roster+rival:
        pri['players'][p['id']]={'availability':'AVAILABLE','vote_probability':.88,
            'pure_vote_mean':6.0,'pure_vote_sd':.65,'goal_weight':.35 if p['role']=='A' else .10,
            'assist_weight':.25 if p['role']=='C' else .08,
            'yellow_probability':.17,'red_probability':.02}
    for g in games:
        pri['fixtures']['|'.join((g['home'],g['away'],g['kickoff']))] = {
           'home_xg':1.6,'away_xg':1.2,'shared_tempo_sd':.19,
           'other_goal_weight':1.4,'other_assist_weight':1.7,'assist_chance':.75}
    opts={'n':80,'seed':44,'source_cutoff_at':'2026-11-04T09:00:00+01:00',
          'generated_at':'2026-11-04T09:01:00+01:00','lock_at':'2030-11-07T14:30:00+01:00'}
    return own,opp,cal,pri,opts


class JointNativeTests(unittest.TestCase):
    def test_demo_audit_pass(self):
        own,opp,cal,pri,opts=mock_data()
        data=generate(own,opp,cal,pri,**opts)
        self.assertEqual(audit(data,own,opp,cal)['audit'],'PASS')
        self.assertEqual(len(data['scenarios']),80)
        self.assertEqual(data['evidence_kind'],'SYNTHETIC_UNIT_TEST')
        self.assertFalse(data['GOLD_LOCK'])

    def test_seed_reproducibility_and_change(self):
        own,opp,cal,pri,opts=mock_data()
        a=generate(own,opp,cal,pri,**opts)
        b=generate(own,opp,cal,pri,**opts)
        self.assertEqual(digest(a),digest(b))
        opts['seed']+=1
        c=generate(own,opp,cal,pri,**opts)
        self.assertNotEqual(digest(a),digest(c))

    def test_roster_order_no_change(self):
        own,opp,cal,pri,opts=mock_data()
        opts['n']=10
        a=generate(own,opp,cal,pri,**opts)
        own['roster'].reverse();opp['roster'].reverse()
        b=generate(own,opp,cal,pri,**opts)
        self.assertEqual(a['scenarios'],b['scenarios'])

    def test_out_zero_vote(self):
        own,opp,cal,pri,opts=mock_data()
        player=own['roster'][0]['id'];pri['players'][player]['availability']='OUT'
        pri['players'][player]['vote_probability']=0
        a=generate(own,opp,cal,pri,**opts)
        self.assertTrue(all(s['player_outcomes'][player]['status']=='DID_NOT_PLAY' for s in a['scenarios']))
        self.assertTrue(all('pure_vote' not in s['player_outcomes'][player] for s in a['scenarios']))

    def test_out_player_with_vote_probability_rejected(self):
        own,opp,cal,pri,opts=mock_data()
        player=own['roster'][0]['id'];pri['players'][player]['availability']='OUT'
        with self.assertRaisesRegex(ValueError,'OUT player'):
            generate(own,opp,cal,pri,**opts)

    def test_no_uncalibrated_claim_real_mode(self):
        own,opp,cal,pri,opts=mock_data()
        pri['evidence_kind']='PRELOCK_JOINT_MODEL_OUTPUT'
        with self.assertRaisesRegex(ValueError,'fail closed'):
            generate(own,opp,cal,pri,**opts)

    def test_time_leakage_rejected(self):
        own,opp,cal,pri,opts=mock_data()
        opts['source_cutoff_at']='2030-11-08T00:00:00+01:00'
        with self.assertRaisesRegex(ValueError,'source_cutoff'):
            generate(own,opp,cal,pri,**opts)

    def test_lock_after_first_kickoff_rejected(self):
        own,opp,cal,pri,opts=mock_data()
        opts['lock_at']='2030-11-09T00:00:00+01:00'
        with self.assertRaisesRegex(ValueError,'lock after'):
            generate(own,opp,cal,pri,**opts)

    def test_cross_club_event_tampering_rejected(self):
        own,opp,cal,pri,opts=mock_data()
        data=generate(own,opp,cal,pri,**opts)
        ev=next((e for s in data['scenarios'] for state in s['fixture_states'].values()
                 for e in state['goal_events'] if e['scorer_id'] is not None),None)
        if ev is None:self.skipTest('rare zero tracked scorer sample')
        ev['team']='Unmapped Club'
        with self.assertRaisesRegex(ValueError,'fixture score/event mismatch'):
            audit(data,own,opp,cal)

    def test_no_fixture_independence(self):
        own,opp,cal,pri,opts=mock_data()
        data=generate(own,opp,cal,pri,**opts)
        for s in data['scenarios']:
            for k,st in s['fixture_states'].items():
                self.assertEqual(len(st['goal_events']),st['home_goals']+st['away_goals'])
                self.assertTrue(st['shared_tempo']>0)

    def test_poisson_zero_intensity(self):
        self.assertEqual(poisson(random.Random(1),0),0)

    def test_input_missing_player_prior_rejected(self):
        own,opp,cal,pri,opts=mock_data()
        pri['players'].pop(next(iter(pri['players'])))
        with self.assertRaisesRegex(ValueError,'cover exactly'):
            generate(own,opp,cal,pri,**opts)

    def test_real_scenarios_require_contemporaneous_sources(self):
        own,opp,cal,pri,opts=mock_data()
        pri['players'][own['roster'][0]['id']]['vote_probability']=float('nan')
        with self.assertRaisesRegex(ValueError,'invalid numeric'):
            generate(own,opp,cal,pri,**opts)

if __name__=='__main__':unittest.main()
