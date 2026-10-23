# FS V3.3.1 | G7 Postmortem (NO FUTURE LEAKAGE)

**Evidence level: POSTMATCH HINDSIGHT / APP SIMULATED, never a prematch forecast.** Data from ten user-provided screenshots. Original image SHA256 listed in `data/g7_app_simulated_20261019.json`.

## Actual app simulated fixture
**Mall & Dealer Sikuli 60.0 - 74.0 AC DENTI**, 0-3 fantasy goals.

- Home starting voted fantasy points: **55**, including Maldini's 5.
- Home Wesley SV -> Cambiaso 6 (+6), nominated captain Maldini pure-factor shown as **-1**. `55+6-1=60`. Defense modifier inferred residual 0; raw pure votes not yet available.
- Away voted XI subtotal without Simeone: **60.5**; Simeone +6, Adzic no vote -> Perrone +6, captain Nico Paz factor **+1.5**. `60.5+6+6+1.5=74`. 3-5-2 cannot receive a 4-defender modifier.
- The app itself labels the panel **RISULTATO SIMULATO**, and displays LIVE fantasy-event sourcing. Never record the screenshot as signed final platform G16 evidence.

## Retrospective formation alternatives, deliberately hindsight-only

**Assumptions fixed for comparison:** actual listed fantasy points; Meret stays goalkeeper; Maldini retains captain and -1; same registered team; no new injuries/substitutions; four-defender defensive modifier 0 for the same effective four defenders as the app result; three-defender modules get no modifier. These are **counterfactual selections made AFTER seeing the votes**, not allowed model predictions or empirical advantages. Do not promote a strategy using these retrospectively optimized lineups.

| Structure | Chosen XI after known subs | Raw sum | Captain | Total | Goals vs AC DENTI (74) |
|---|---|---:|---:|---:|---|
| Submitted 4-3-3 | P Meret(5); D Cambiaso(6), Solet(4.5), Dimarco(6), Zortea(5.5); C Moreira(8), Ekkelenkamp(4.5), Modric(6.5); A Kolo Muani(5), Maldini(5), Geubbels(5) | 61 | -1 | **60** | **0-3** |
| Ex-post 4-4-2 | P Meret(5); D same 4 (22); C Gaetano(10), Thorstvedt(9.5), Pobega(9.5), Moreira(8); A Maldini(5), Kolo Muani(5) | 74 | -1 | **73** | **2-3** |
| Ex-post 3-5-2 | P Meret(5); D Cambiaso(6), Dimarco(6), Zortea(5.5); C Gaetano(10), Thorstvedt(9.5), Pobega(9.5), Moreira(8), Zalewski(7.5); A Maldini(5), Kolo Muani(5) | 77 | -1 | **76** | **3-3** |

The 3-5-2 equalizer is possible **in retrospect**, not evidence it had the best **pre-lock expected** win probability. Different captain or pure-vote-derived bonuses may change hypothetical scores, but those cannot be inferred without actual pure votes. Because the opponent scored 74 (three fantasy goals), reaching four fantasy goals would need 78+.

## Actionable calibration work

1. Pre-register the pre-lock decision, lineup/bench/captain and forecasts for candidate, B0 and B1; archive all source timestamps/hashes.
2. Test `4-3-3`, `4-4-2`, `3-5-2` and all certified allowable modules with the **same joint match scenarios** and proper source-governed scoring; compare E[league points], P(win), P(draw), P(loss) and uncertainty.
3. Use this G7 for **scoring replay and postmortem diagnostics only**. Never include its postlock player observations in a prematch validation holdout.
4. Close G16 only when the independently observed final real platform score and all required pure-vote evidence support the exact replay. Close GOLD only after all remaining technical and calibrated statistical gates.

**Status:** SHADOW. No change to the main engine or production promotion flags.
