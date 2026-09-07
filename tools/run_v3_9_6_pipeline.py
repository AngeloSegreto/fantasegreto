#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def run(*cmd):
    print("+", " ".join(map(str,cmd)))
    subprocess.run([str(x) for x in cmd], cwd=ROOT, check=True)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--snapshot")
    ap.add_argument("--baseline")
    ap.add_argument("--strict", action="store_true")
    args=ap.parse_args()
    state=json.loads((ROOT/"FS_V3_9_6_PIPELINE_STATE_20260907.json").read_text())
    print("FS V3.9.6 pipeline", state["engine"])
    if not args.snapshot:
        msg="BLOCK S02: official Fantacalcio XLSX snapshot is required"
        print(msg)
        if args.strict: raise SystemExit(2)
        return
    snap=Path(args.snapshot).resolve()
    if not snap.exists(): raise SystemExit(f"snapshot not found: {snap}")
    candidate=ROOT/"data/listone_ufficiale_2026_27.candidate.json"
    receipt=ROOT/"audit/source/fantacalcio/2026-09-07/import_receipt.json"
    run(sys.executable,"tools/importa_listone_ufficiale.py",snap,"--output",candidate,"--receipt",receipt)
    if not args.baseline:
        msg="BLOCK S05: full V3.9.5 canonical baseline file is required for official-Id diff"
        print(msg)
        if args.strict: raise SystemExit(3)
        return
    baseline=Path(args.baseline).resolve()
    diff=ROOT/"audit/registry_diff_v3_9_5__v3_9_6.json"
    run(sys.executable,"tools/reconcile_registry.py","--old",baseline,"--new",candidate,"--output",diff)
    print("PASS through S05. Downstream calibration remains gated until transfers, injuries, tactical and Matchday 3 are reconciled.")

if __name__=="__main__":
    main()
