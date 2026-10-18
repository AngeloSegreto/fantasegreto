# FS V3.3.1 — SHADOW Evidence Custody (candidate)

This directory contains a **P0 evidence-custody candidate**, based on the canonical FS V3.3.1 specification dated 18 Oct 2026. It does not replace the incumbent, does not set gold=true, and never claims prediction accuracy.

Files added on the isolated `fs-v331-evidence-custody-phase1` branch:

- `shadow_evidence.py`: archived pre-lock input snapshots, immutable archive claim, source time/provenance check, SHA-256 manifest and readback, separate fail-closed promotion checklist. The latter returns at most `GOLD_ELIGIBLE_FOR_CTO_REVIEW` and **never** changes release flags.
- `test_shadow_evidence.py`: 13 unit tests with **synthetic** fixtures covering tampering, timestamps, empty/missing sources, overwrite protection, deterministic manifests, and refusal of automatic promotion.

Run locally from project root (requires Python standard library only):

```sh
python -m unittest discover -s experimental/fs_v331 -p 'test_shadow_evidence.py' -v
```

Example API usage must supply an **already-produced real pre-lock** decision, an explicit lock timestamp and copied, independently archived source bytes. This library does not obtain sources or run the match simulation by itself.

## Evidence and scope

- Local precursor package used the same algorithm family and passed 13/13 isolated tests. This **GitHub branch has not yet been re-executed on a checked-out clone**, so no remote `TECH PASS` is claimed.
- `verify_archive` provides byte-integrity readback only. Full deterministic **re-execution**, OS/dependency lock and independent scoring audit are still absent, therefore G21 is not `VERIFICATO`.
- `promotion_gate` inspects attestations supplied by a caller; it does not authenticate them. External independent audit and signed original receipts remain mandatory; this is not an authority to promote.

### Remaining blockers

- G00/G12: automatic real before-lock capture and trusted timestamps.
- G09/G10: certified defense modifier and captain factor.
- G14/G15: real out-of-sample preregistered Brier/calibration/rolling-origin comparison versus B0/B1.
- G16: historical Golden official score exact reproduction.
- G17/G18: Excel/PWA parity and physical iPhone gate.
- G21/G22: full engine replay and concurrent append-only register.

**Release state**: `SHADOW_BLOCKED` / `TECH PASS: NO` / `STAT VALIDATED: NO` / `GOLD LOCK: NO`.

Costs: no paid services, only local execution and GitHub branch. No automatic merge or deploy.
