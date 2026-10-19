# FS V3.3.1 — G7 Golden Replay (SHADOW, fail-closed)

## Purpose

Reproduce **both sides** of the National League G7 from already-observed official fantasy votes and **pure ratings**:

`11 starting players + same-role Traditional substitutes (max 5) + defensive modifier + captain/vice factor = total fantasy points → goals in fixed 66/4 bands`.

Compare the calculation against the independently captured final score of the **AutoMasterFanta platform**.

This is a **historic replay**, NOT a pre-lock forecast and NOT a Brier/backtest datapoint.

## Genuine partial evidence (19 October, screenshot at 06:07)

| | Mall & Dealer Sikuli | AC DENTI |
|---|---:|---:|
| Scored XI members visible | 50 | 60.5 |
| Traditional fallback | Wesley SV → Cambiaso 6 | Adzic did not play → Perrone 6 |
| Known base including substitute | **56** | **66.5** |
| Pending starting player | **Maldini** (captain) | **Simeone** |
| Pure votes for 4-player defender calculation | Not supplied | modifier does not apply (3D) |
| Pure vote of captain | Not supplied for Maldini | Not supplied for Nico Paz |
| Full official fantasy score | **NOT AVAILABLE** | **NOT AVAILABLE** |

Screenshots: `IMG_9128.jpeg`, `IMG_9129.jpeg` and league-scoring legends `IMG_9133.jpeg`, `IMG_9134.jpeg`. Their SHA256 fingerprints are referenced in `data/g7_live_partial_20261019.json`. Source images remain conversation attachments and have NOT been committed as authoritative raw bytes to GitHub.

**Do not use the previous 63–74 scenario** as a confirmed platform result.

## Running the tool

From the repository root:

```bash
python experimental/fs_v331/g7_golden_replay.py \
  --partial experimental/fs_v331/data/g7_live_partial_20261019.json \
  --config experimental/fs_v331/league_config.yaml \
  --output /tmp/fs-g7-replay-blocked.json
```

Without a final input, the command returns `BLOCKED_OFFICIAL_FINAL_NOT_PROVIDED`.

To run an actual comparison, provide `--final /path/to/g7_official_final_input.json` containing:

- `schema: FS_V331_G7_OFFICIAL_RESULT_INPUT_V1` and `matchday: 7`.
- `receipt`: exact original path to archived **final screenshot**, sha256 of the bytes, timezone-aware `observed_at`, `evidence_kind: OFFICIAL_APP_FINAL`.
- `player_updates.home` and `player_updates.away`: ID-keyed values to **resolve every pending player**, with `status` and `fantavote` for every voted player across XI and bench. A separate `pure_vote` is required **only for** the effective goalkeeper and defenders involved in the modifier, plus the nominated captain (or vice when eligible). The source must independently support the numeric transcription. Pure votes must NEVER be inferred from fantavotes.
- `platform.home_total`, `away_total`, `home_goals`, `away_goals`: final *app* output, not estimated.
- A completed original final platform receipt and separately checked pure-vote sources are required for an independent attestation, even if software parity passes.

The engine reads the original partial snapshot, applies observed updates, enforces exact Decimal arithmetic, uses the unchanged league configuration, computes both sides and compares total and goal count **without tolerances**.

Possible states:

- `BLOCKED_OFFICIAL_FINAL_NOT_PROVIDED`
- `BLOCKED_INCOMPLETE_OFFICIAL_EVIDENCE`
- `SCORING_PARITY_FAIL`
- `SCORING_PARITY_PASS_PENDING_INDEPENDENT_AUDIT`
- `SOFTWARE_TEST_ONLY`

It ALWAYS emits `gold_lock:false`, `stat_validated:false`, `golden_gate_G16:DA_VERIFICARE`. The scorer and source evidence must undergo independent review before G16 can be marked VERIFIED.

### Tests

```bash
python -m unittest discover -s experimental/fs_v331 -p 'test_*.py' -v
```

The synthetic test fixture covers a manual arithmetic example:

Mall & Dealer = 50 + Cambiaso 6 + hypothetical Maldini 10.5 + hypothetical defense bonus 1 + hypothetical captain bonus 1.5 = **69** (1 goal).

AC DENTI = 60.5 + Perrone 6 + hypothetical Simeone 6 + defense bonus 0 + hypothetical captain bonus 0 = **72.5** (2 goals).

**These are invented unit-test numbers, NOT the 7th matchday real result.** The fixture is typed `SYNTHETIC_UNIT_TEST` and cannot pass GOLDEN validation.

## Unclosed gates

- G00: authenticate full final platform and ratings sources (screenshots alone are not independently timestamped).
- G07/G09/G10: independently verify substitute precedence, modifier and captain calculation on observed cases.
- G16: replay all certified historic matchdays and compare exact platform totals.
- G14/G15: separately preregister and evaluate REAL pre-lock forecasts on an out-of-sample rolling holdout.
- G17/G18/G21: parity, physical iPhone and deterministic full-engine replay.

**Release stays SHADOW. Never auto-merge or set gold=true.**
