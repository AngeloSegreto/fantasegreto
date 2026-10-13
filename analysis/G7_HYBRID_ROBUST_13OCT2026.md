# FantaSegreto PRO — G7 Hybrid ROBUST (13 ottobre 2026)

Status: **EXPERIMENTAL / NOT GOLD / NOT PROMOTED**. This document is an analytical overlay only. The canonical listone, Golden optimizer, BUY/MAX and deployed dashboard are not changed by this commit.

## Operating invariant

> Una formazione affidabile non è quella con undici titolari sicuri, ma quella che mantiene undici voti validi anche quando qualcosa va storto.

Objective: maximize expected fantasy score subject to estimated probability of fewer than eleven valid votes **after substitutions** <= 20%. This is a full-lineup constraint, not a per-player constraint.

## G7 — Mall & Dealer Sikuli against AC DENTI

Known G6 Mall & Dealer reference XI (not verified G7 XI): Meret; Zortea, Dimarco, Solet, Wesley; Moreira, Modric, Ekkelenkamp, Thorstvedt; Kolo Muani, Maldini.

Bench reference: Gollini, Svilar; Cambiaso, Zanoli, Spence; Pobega, Gaetano, Zalewski, Thuram K.; Geubbels, Ngonge, Boga.

League substitutions: maximum 5, same-role, fixed formation. Verify actual platform bench order and all league-specific exceptional handling before claiming a certified result. Calculate shortage across **all four roles jointly**. Defensive modifier and captain rules require separate checks.

## Defensive candidate comparison

Source: user-provided Quotazioni_Fantacalcio_Stagione_2026_27 2.xlsx (club / quote / FVM from chat reading). These are **not** goal probabilities.

| Player | Club | Quote | FVM | G7 fixture | Home/away |
|---|---|---:|---:|---|---|
| Zortea | Bologna | 6 | 19 | Bologna–Inter | Home |
| Cambiaso | Juventus | 7 | 11 | Juventus–Lazio | Home |
| Spence | Inter | 10 | 14 | Bologna–Inter | Away |
| Zanoli | Udinese | 5 | 10 | Udinese–Lecce | Home |

Fixtures are working assumptions from the G7 discussion, to revalidate against the official match schedule before lock.

Historical 2024/25 + 2025/26 goals/assists quoted in the conversation (NOT independently reconciled by homogeneous competition/source and thus NOT canonical): Zortea 6G+4A, Cambiaso 5G+7A, Spence 1G+2A, Zanoli 2G+2A. Spence includes Premier League history. Historical goal/assist totals cannot be treated as G7 event probabilities.

Former experimental Monte Carlo proxy numbers were cited in chat (Cambiaso 67.237, Zortea 67.185, Zanoli 67.141, Spence 67.124; incompleteness risk approx 15.56%–15.79%). **Do not publish these as verified performance forecasts or proof of the 20% constraint**. Reproduction, parameter calibration, correct substitutions, opponent and venue features, availability, goal/assist probabilities and replay are pending.

## Operational gate

- Expected fantasy points must include vote, goal/assist events, clean sheets, cards, defensive modifier, captain and correlations.
- Track observed availability vs estimates and source timestamps.
- Scenario-robust test across all four roles and bench order, including shared disruptions and 5-substitution cap.
- Mark G7 lineup as **PROVISIONAL** until match-specific sources and model replay are available.
- No mutation to Golden optimizer, official registry, auction thresholds or live deployment from this note.
