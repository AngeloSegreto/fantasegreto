"""Offline synthetic example for the event-consistent native generator."""
import argparse
import json
from pathlib import Path
from native_joint_generator import generate,audit
from test_native_joint_generator import mock_data


def main():
    parser=argparse.ArgumentParser(description='SHADOW ONLY synthetic demo; zero network')
    parser.add_argument('--output-dir',default='native_joint_demo')
    parser.add_argument('--n',type=int,default=200)
    parser.add_argument('--seed',type=int,default=3301)
    args=parser.parse_args()
    own,opp,cal,prior,opts=mock_data()
    opts.update(n=args.n,seed=args.seed,
        source_cutoff_at='2030-11-07T12:00:00+01:00',
        generated_at='2030-11-07T12:01:00+01:00')
    result=generate(own,opp,cal,prior,**opts)
    receipt=audit(result,own,opp,cal)
    receipt.update(engine=result['engine'],
                   evidence_kind=result['evidence_kind'],
                   calibrated=False, status='SYNTHETIC_DEMO_ONLY')
    dest=Path(args.output_dir)
    dest.mkdir(parents=True,exist_ok=True)
    for name,data in [('own_roster.json',own),('opponent_roster.json',opp),
                      ('calendar.json',cal),('synthetic_priors.json',prior),
                      ('synthetic_joint_scenarios.json',result),('audit.json',receipt)]:
        (dest/name).write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({'status':'SHADOW_SYNTHETIC_DEMO_GENERATED',
        'n':len(result['scenarios']),'audit':receipt['audit'],
        'output_directory':str(dest)},indent=2))

if __name__=='__main__':main()
