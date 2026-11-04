"""End-to-end schema bridge test: native joint generator -> V3.3.1 scorer.

Synthetic fixture/test dates only. This does NOT assert real pre-lock provenance
or production prediction calibration.
"""
import unittest

from native_joint_generator import generate, audit
from test_prelock_scenario_compare import make, run


class NativeJointComparatorBridgeTest(unittest.TestCase):
    def test_generated_scenarios_feed_existing_g8_comparator(self):
        args=make()
        own,cal,_cfg,_candidates,opponent,_legacy_synthetic,_protocol=args
        roster=own['roster']+opponent['roster']
        priors={'schema':'FS_NATIVE_JOINT_PRIORS_V1','evidence_kind':'SYNTHETIC_UNIT_TEST',
                'players':{},'fixtures':{}}
        for p in roster:
            priors['players'][p['id']]={
                'availability':'AVAILABLE','vote_probability':1.0,
                'pure_vote_mean':6.0,'pure_vote_sd':.4,
                'goal_weight':.45 if p['role']=='A' else .15,
                'assist_weight':.35 if p['role']=='C' else .12,
                'yellow_probability':.08,'red_probability':.002}
        for f in cal['games']:
            key='|'.join((f['home'],f['away'],f['kickoff']))
            priors['fixtures'][key]={'home_xg':1.4,'away_xg':1.1,
                'shared_tempo_sd':.16,'other_goal_weight':1.4,
                'other_assist_weight':1.6,'assist_chance':.72}
        generated=generate(own,opponent,cal,priors,n=24,seed=1337,
                           source_cutoff_at='2026-10-20T10:01:00+02:00',
                           generated_at='2026-10-20T10:02:00+02:00',
                           lock_at='2026-10-23T20:30:00+02:00')
        self.assertEqual(audit(generated,own,opponent,cal)['audit'],'PASS')
        args[5]=generated
        result=run(args)
        self.assertEqual(result['status'],'SHADOW_COMPARISON_COMPUTED_UNCALIBRATED')
        self.assertEqual(result['n_scenarios'],24)
        self.assertEqual({x['module'] for x in result['candidate_results'].values()},
                         {'4-3-3','4-4-2','3-5-2'})
        self.assertFalse(result['GOLD_LOCK'])
        self.assertFalse(result['STAT_VALIDATED'])
        self.assertFalse(result['claim_external_predictive_validation'])

    def test_matchday_11_generic_calendar_bridge(self):
        from test_native_joint_generator import mock_data
        from p0_core import load_config
        from prelock_scenario_compare import analyze
        from pathlib import Path
        own,opp,cal,pri,opts=mock_data()
        own['status']='SCREENSHOT_GROUNDED_SHADOW_ONLY'
        for x in pri['players'].values():x['vote_probability']=1.0
        def line(roster,d,c,a):
            grouped={role:[p['id'] for p in roster if p['role']==role] for role in 'PDCA'}
            ids=[grouped['P'][0]]+grouped['D'][:d]+grouped['C'][:c]+grouped['A'][:a]
            return {'starting_xi':ids,'bench':[p['id'] for p in roster if p['id'] not in ids],
                    'module':f'{d}-{c}-{a}','captain':grouped['A'][0],'vice':grouped['C'][0]}
        cands=[line(own['roster'],4,3,3),line(own['roster'],4,4,2),line(own['roster'],3,5,2)]
        opp.update(evidence_kind='SYNTHETIC_UNIT_TEST',lineup=line(opp['roster'],4,4,2))
        opts.update(n=24,seed=4411,source_cutoff_at='2030-11-07T12:00:00+01:00',
                    generated_at='2030-11-07T12:01:00+01:00')
        bundle=generate(own,opp,cal,pri,**opts)
        self.assertEqual(audit(bundle,own,opp,cal)['audit'],'PASS')
        cfg=load_config(Path(__file__).resolve().parent/'league_config.yaml')
        protocol={'alpha':.05,'delta':.05,'seed':4411,'bootstrap_reps':100,
                  'profile':'PUNTI_ATTESI','preregistered_at':'2030-11-07T11:59:00+01:00'}
        result=analyze(own,cal,cfg,cands,opp,bundle,protocol)
        self.assertEqual(result['status'],'SHADOW_COMPARISON_COMPUTED_UNCALIBRATED')
        self.assertEqual(result['n_scenarios'],24)
        self.assertFalse(result['GOLD_LOCK'])
        self.assertEqual({x['module'] for x in result['candidate_results'].values()},
                         {'3-5-2','4-4-2','4-3-3'})

if __name__=='__main__':unittest.main()
