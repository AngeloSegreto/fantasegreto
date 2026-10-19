"""Smoke the executable prelock comparator: missing real evidence is NOT success."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from test_prelock_scenario_compare import make

ROOT=Path(__file__).resolve().parent
APP=ROOT/"prelock_scenario_compare.py"

class FailClosedCLITests(unittest.TestCase):
    def test_no_opponent_exits_nonzero_and_writes_valid_json(self):
        payload=make()
        with tempfile.TemporaryDirectory() as d:
            d=Path(d)
            fields={"roster":payload[0],"calendar":payload[1],
                    "candidates":payload[3],"protocol":payload[6]}
            for k,v in fields.items():
                (d/(k+".json")).write_text(json.dumps(v),encoding="utf-8")
            output=d/"report.json"
            args=[sys.executable,str(APP)]
            for k in fields:
                args.extend(["--"+k,str(d/(k+".json"))])
            args.extend(["--config",str(ROOT/"league_config.yaml"),
                         "--output",str(output)])
            p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            self.assertEqual(p.returncode,3,p.stderr)
            result=json.loads(output.read_text())
            self.assertEqual(result["status"],"BLOCKED_OPPONENT_G8_FANTASY_LINEUP_MISSING")
            self.assertFalse(result["GOLD_LOCK"])
            self.assertFalse(result["usable_for_lineup_submission"])
    def test_missing_scenarios_exits_nonzero(self):
        payload=make()
        with tempfile.TemporaryDirectory() as d:
            d=Path(d)
            fields={"roster":payload[0],"calendar":payload[1],
                    "candidates":payload[3],"protocol":payload[6],
                    "opponent":payload[4]}
            args=[sys.executable,str(APP)]
            for k,v in fields.items():
                p=d/(k+".json")
                p.write_text(json.dumps(v),encoding="utf-8")
                args.extend(["--"+k,str(p)])
            args.extend(["--config",str(ROOT/"league_config.yaml")])
            p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            self.assertEqual(p.returncode,3,p.stderr)
            self.assertEqual(json.loads(p.stdout)["status"],"BLOCKED_NO_PRELOCK_JOINT_SCENARIOS")
if __name__=="__main__":
    unittest.main()
