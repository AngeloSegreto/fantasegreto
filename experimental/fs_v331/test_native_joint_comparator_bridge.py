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

if __name__=='__main__':unittest.main()
