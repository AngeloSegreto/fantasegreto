"""National League V3.3.1 config-driven scoring primitives. SHADOW; no promotion."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

class UncertifiedScoringCase(ValueError):
    pass

def D(v):
    if isinstance(v, bool) or isinstance(v, float) or v is None:
        raise TypeError("exact decimal string/integer/Decimal required")
    try:
        q = Decimal(str(v))
    except (InvalidOperation, ValueError) as e:
        raise ValueError("invalid decimal") from e
    if not q.is_finite():
        raise ValueError("non-finite decimal")
    return q

def rules(config, key):
    obj = config["rules"][key]
    if obj.get("status") != "CERTIFICATA":
        raise UncertifiedScoringCase("uncertified rule: " + key)
    return obj

def _is_vote(p):
    return p.get("pure_vote") is not None

def modifier(xi, config):
    """The 4-player average uses keeper plus top 3 pure-vote defenders."""
    rule = rules(config, "defense_modifier")
    if not rule["enabled"]:
        return Decimal("0")
    ds = [p for p in xi if p.get("role") == "D"]
    required = int(rule["min_defenders_after_substitutions"])
    if len(ds) < required:
        return Decimal("0")
    if len(ds) >= required and sum(_is_vote(p) for p in ds) < required:
        raise UncertifiedScoringCase("4th defender SV semantics await official replay")
    keepers = [p for p in xi if p.get("role") == "P" and _is_vote(p)]
    if len(keepers) != 1:
        raise UncertifiedScoringCase("keeper SV changes modifier eligibility")
    n = int(rule["selected_defenders"])
    best = sorted((D(p["pure_vote"]) for p in ds), reverse=True)[:n]
    if len(best) != n:
        raise UncertifiedScoringCase("not enough eligible defenders")
    values = best + ([D(keepers[0]["pure_vote"])] if rule["include_goalkeeper"] else [])
    average = sum(values) / D(len(values))
    for band in rule["bands"]:
        lower = band.get("from_inclusive")
        upper = band.get("to_exclusive")
        if (lower is None or average >= D(lower)) and (upper is None or average < D(upper)):
            return D(band["bonus"])
    raise ValueError("modifier bands missing interval for mean")

def captain_bonus(xi, captain_id, vice_id, config):
    r = rules(config, "captain_factor")
    if not r["enabled"]:
        return Decimal("0")
    by_id = {p["id"]: p for p in xi}
    if captain_id == vice_id or captain_id not in by_id or vice_id not in by_id:
        raise ValueError("invalid captain/vice identity")
    captain = by_id[ captain_id ]
    chosen = captain if _is_vote(captain) else (by_id[vice_id] if r["vice_if_captain_without_vote"] else None)
    if chosen is None or not _is_vote(chosen):
        return Decimal("0")
    vote = D(chosen["pure_vote"])
    tick = D(r["vote_tick"])
    if vote / tick != (vote/tick).to_integral_value():
        raise UncertifiedScoringCase("captain pure vote outside certified tick")
    for band in r["bands"]:
        upper_inc = band.get("upper_inclusive")
        upper_exc = band.get("to_exclusive")
        if upper_inc is not None and vote <= D(upper_inc):
            return D(band["bonus"])
        if upper_inc is None and upper_exc is not None and vote < D(upper_exc):
            return D(band["bonus"])
        if upper_inc is None and upper_exc is None:
            return D(band["bonus"])
    raise ValueError("captain vote outside config ranges")

def substitutes(starters, bench, config):
    r = rules(config, "substitution")
    if (r["mode"] != "TRADITIONAL" or not r["same_role_only"] or
        r["module_change_allowed"] or r["office_reserve_enabled"]):
        raise UncertifiedScoringCase("unsupported substitution mode")
    all_players = list(starters) + list(bench)
    ids = [p["id"] for p in all_players]
    if len(starters) != 11 or len(ids) != len(set(ids)):
        raise ValueError("invalid starters/bench identities")
    # Official tie priority for >5 simultaneous viable absences is not covered by screenshots.
    missing = [p for p in starters if not _is_vote(p)]
    eligible_count = 0
    for p in missing:
        if any(b["role"] == p["role"] and _is_vote(b) for b in bench):
            eligible_count += 1
    max_changes = int(r["max_changes"])
    if eligible_count > max_changes:
        raise UncertifiedScoringCase("five-sub priority among multiple absent roles unverified")
    used = set()
    effective = []
    replacements = []
    for p in starters:
        if _is_vote(p):
            effective.append(p)
            continue
        replacement = next((b for b in bench if b["id"] not in used and
                            b["role"] == p["role"] and _is_vote(b)), None)
        if replacement is None or len(replacements) >= max_changes:
            effective.append(p)
        else:
            effective.append(replacement)
            used.add(replacement["id"])
            replacements.append({"out": p["id"], "in": replacement["id"]})
    return {"xi": effective, "replacements": replacements,
            "without_vote": [p["id"] for p in effective if not _is_vote(p)]}

def score(starters, bench, captain_id, vice_id, config, goal_function):
    """Calculate observed T from already-provided official fantasy votes.

    It does NOT infer bonuses or make fantasy-vote predictions.
    """
    changes = substitutes(starters, bench, config)
    xi = changes["xi"]
    base = sum(D(p["fantavote"]) for p in xi if _is_vote(p))
    mod = modifier(xi, config)
    cap = captain_bonus(xi, captain_id, vice_id, config)
    total = base + mod + cap
    return {"base": str(base), "defense_modifier": str(mod),
            "captain_factor": str(cap), "total": str(total),
            "fantagoals": goal_function(total, config),
            "replacements": changes["replacements"],
            "without_vote": changes["without_vote"],
            "evidence_level": "DETERMINISTIC_SCORING_SHADOW_NOT_HISTORICAL_GOLDEN"}
