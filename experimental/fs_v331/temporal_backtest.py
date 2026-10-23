"""V3.3.1 G14/G15 candidate evaluator. Never certifies GOLD or invents observations."""
from collections import defaultdict
from datetime import datetime
from hashlib import sha256
import json
import math
import random
import re

LABELS = ("V", "N", "S")
SHA = re.compile(r"^[0-9a-f]{64}$")


def instant(value):
    d = datetime.fromisoformat(value)
    if d.tzinfo is None or d.utcoffset() is None:
        raise ValueError("timezone required")
    return d


def source_digest(s):
    if not isinstance(s, str) or not SHA.fullmatch(s):
        raise ValueError("source evidence sha256 required")
    return s


def brier(p, label):
    return sum((float(p[k]) - (1.0 if k == label else 0.0)) ** 2 for k in LABELS)


def valid_probs(p):
    if not isinstance(p, dict) or set(p) != set(LABELS):
        raise ValueError("V/N/S distribution required")
    a = list(p.values())
    if not all(isinstance(x, (float, int)) and not isinstance(x, bool)
               and math.isfinite(x) and 0 <= x <= 1 for x in a):
        raise ValueError("invalid probability")
    if abs(sum(a) - 1) > 1e-9:
        raise ValueError("probabilities must sum to 1")


def validate_row(r, prereg_time):
    for k in ("fixture_id", "matchday", "lock_at", "predicted_at", "observed_at",
              "outcome", "source_kind", "prelock_archive_sha256", "official_result_sha256",
              "training_through_matchday", "models"):
        if k not in r:
            raise ValueError("missing event field " + k)
    if r["source_kind"] != "OFFICIAL":
        raise ValueError("reconstructed/synthetic outcome not accepted")
    source_digest(r["official_result_sha256"])
    source_digest(r["prelock_archive_sha256"])
    if not isinstance(r["matchday"], int) or r["matchday"] < 1:
        raise ValueError("invalid matchday")
    if not isinstance(r["training_through_matchday"], int) or not 0 <= r["training_through_matchday"] < r["matchday"]:
        raise ValueError("future training leakage")
    prediction = instant(r["predicted_at"])
    lock = instant(r["lock_at"])
    observed = instant(r["observed_at"])
    if not prereg_time <= prediction <= lock < observed:
        raise ValueError("temporal leakage")
    if r["outcome"] not in LABELS:
        raise ValueError("invalid observed outcome")
    if set(r["models"]) != {"candidate", "B0", "B1"}:
        raise ValueError("candidate and B0/B1 required")
    for p in r["models"].values():
        valid_probs(p)


def evaluate(rows, prereg, *, synthetic_tests=False):
    """Paired rolling-origin Brier evaluation. Attestation is external.

    synthetic_tests bypasses *only* source_kind rejection in unit tests and never returns validation.
    """
    if not isinstance(rows, list) or not isinstance(prereg, dict):
        raise ValueError("rows and prereg required")
    ptime = instant(prereg["registered_at"])
    if prereg.get("metric") != "brier_multiclass_0_2":
        raise ValueError("metric not preregistered")
    for name in ("alpha", "practical_gain"):
        if not isinstance(prereg.get(name), (int, float)) or not math.isfinite(prereg[name]):
            raise ValueError("invalid preregistration " + name)
    alpha = float(prereg["alpha"])
    gain = float(prereg["practical_gain"])
    if not 0 < alpha < 0.5 or not 0 <= gain < 2:
        raise ValueError("invalid confidence or gain")
    reps = prereg.get("bootstrap_reps")
    if not isinstance(reps, int) or not 100 <= reps <= 100000:
        raise ValueError("invalid replications")
    seed = prereg.get("seed")
    if not isinstance(seed, int):
        raise ValueError("seed required")
    event_min = prereg.get("min_events")
    day_min = prereg.get("min_matchdays")
    if not isinstance(event_min, int) or not isinstance(day_min, int) or event_min < 1 or day_min < 2:
        raise ValueError("minimum sample size missing")
    if not rows:
        return {"status": "BLOCKED_NO_REAL_OBSERVATIONS", "G14": "DA_VERIFICARE",
                "G15": "DA_VERIFICARE", "gold_lock": False, "n_events": 0}
    seen = set()
    groups = defaultdict(list)
    for r in rows:
        if synthetic_tests and r.get("source_kind") == "SYNTHETIC":
            r = {**r, "source_kind": "OFFICIAL"}
        validate_row(r, ptime)
        key = (r["matchday"], r["fixture_id"])
        if key in seen:
            raise ValueError("duplicated fixture")
        seen.add(key)
        groups[r["matchday"]].append(r)
    if len(rows) < event_min or len(groups) < day_min:
        return {"status": "BLOCKED_INSUFFICIENT_SAMPLE", "G14": "DA_VERIFICARE",
                "G15": "DA_VERIFICARE", "gold_lock": False,
                "n_events": len(rows), "n_matchdays": len(groups)}
    ordered = [groups[k] for k in sorted(groups)]
    observed = [r for batch in ordered for r in batch]
    scores = {key: sum(brier(r["models"][key], r["outcome"]) for r in observed) / len(observed)
              for key in ("candidate", "B0", "B1")}
    rng = random.Random(seed)
    bounds = {}
    for baseline in ("B0", "B1"):
        differences = [brier(r["models"]["candidate"], r["outcome"]) -
                       brier(r["models"][baseline], r["outcome"]) for r in observed]
        by_day = [[brier(r["models"]["candidate"], r["outcome"]) -
                   brier(r["models"][baseline], r["outcome"]) for r in day] for day in ordered]
        bootstrap = []
        for _ in range(reps):
            sample = [by_day[rng.randrange(len(by_day))] for _ in by_day]
            all_vals = [v for day in sample for v in day]
            bootstrap.append(sum(all_vals) / len(all_vals))
        bootstrap.sort()
        upper = bootstrap[min(len(bootstrap) - 1, math.ceil((1 - alpha) * len(bootstrap)) - 1)]
        bounds[baseline] = {"paired_mean_delta": sum(differences) / len(differences),
                            "one_sided_upper": upper, "improvement_beyond_practical_gain": upper < -gain}
    evidence_complete = bool(prereg.get("ct o_ratified".replace(" ", "")) is True and
                             prereg.get("independent_auditor_pass") is True and
                             prereg.get("snapshot_hashes_verified") is True and
                             not synthetic_tests)
    passes = all(v["improvement_beyond_practical_gain"] for v in bounds.values())
    status = ("EVIDENCE_REVIEW_REQUIRED" if passes else "NOT_VALIDATED_BASELINE_NOT_BEATEN")
    if not evidence_complete:
        status = "PENDING_RATIFICATION_AND_INDEPENDENT_AUDIT" if passes else status
    return {"status": status, "n_events": len(rows), "n_matchdays": len(groups),
            "brier_multiclass_0_2": scores, "paired": bounds,
            "bootstrap_alpha": alpha, "G14": "DA_VERIFICARE", "G15": "DA_VERIFICARE",
            "candidate_statistically_promising": passes, "independent_evidence_complete": evidence_complete,
            "gold_lock": False, "synthetic": bool(synthetic_tests)}
