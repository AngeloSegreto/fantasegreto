"""FS V3.3.1: pre-lock evidence custody and fail-closed release gate. SHADOW ONLY."""
from __future__ import annotations
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import os

GATES = tuple(f"G{i:02d}" for i in range(23))
REQUIRED_RULES = ("fantasy_goals", "defense_modifier", "captain_factor", "substitution", "classic_roles", "allowed_formations", "bonus_malus")


def canonical(data):
    return (json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def digest(raw):
    return sha256(raw).hexdigest()


def parse_time(s):
    if not isinstance(s, str):
        raise ValueError("timestamp missing")
    t = datetime.fromisoformat(s)
    if t.tzinfo is None or t.utcoffset() is None:
        raise ValueError("timezone required")
    return t


def write_new(path, raw):
    with open(path, "xb") as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())


def freeze_prelock(target, *, lock_at, run_at, inputs, config, decision, source_snapshots, engine_artifacts=()):
    """Copies original source bytes; rejects reconstructed/post-lock data and overwrites.

    This records a prior real decision; it never creates predictions.
    """
    lock = parse_time(lock_at)
    # Caller-provided timestamps cannot move the actual capture into the past.
    if datetime.now(timezone.utc) > lock:
        raise ValueError('capture attempted after real lock time')
    if parse_time(run_at) > lock:
        raise ValueError("post-lock run")
    if not isinstance(inputs, dict) or not isinstance(config, dict) or not isinstance(decision, dict):
        raise ValueError("input/config/decision required")
    if decision.get("prediction_status") in ("RECONSTRUCTED", "POST_MATCH"):
        raise ValueError("reconstructed decision rejected")
    if not isinstance(source_snapshots, list) or not source_snapshots:
        raise ValueError("missing source snapshots")
    srcs = []
    seen = set()
    for s in source_snapshots:
        if not isinstance(s, dict) or not all(s.get(k) for k in ("id", "uri", "observed_at", "path", "kind")):
            raise ValueError("missing source provenance")
        sid = str(s["id"])
        if not sid.replace("-", "").replace("_", "").isalnum() or sid in seen:
            raise ValueError("invalid source id")
        seen.add(sid)
        if s["kind"] != "OBSERVED" or parse_time(s["observed_at"]) > lock:
            raise ValueError("post-lock/reconstructed source rejected")
        file = Path(s["path"])
        if not file.is_file():
            raise ValueError("missing source file")
        data = file.read_bytes()
        if not data or (s.get("sha256") and s["sha256"] != digest(data)):
            raise ValueError("source empty or hash mismatch")
        srcs.append((sid, s, data))
    artifacts = []
    for n, art in enumerate(engine_artifacts):
        f = Path(art)
        if not f.is_file():
            raise ValueError("missing engine artifact")
        artifacts.append((f"code/{n:03d}-{f.name}", f.read_bytes()))
    out = Path(target)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.mkdir(exist_ok=False)
    checksums = {}
    for name, data in [("inputs.json", canonical(inputs)),
                       ("league_config.json", canonical(config)),
                       ("decision.json", canonical(decision))] + artifacts:
        p = out / name
        p.parent.mkdir(parents=True, exist_ok=True)
        write_new(p, data)
        checksums[name] = digest(data)
    provenance = []
    for sid, source, data in sorted(srcs, key=lambda x: x[0]):
        name = f"sources/{sid}.bin"
        p = out / name
        p.parent.mkdir(parents=True, exist_ok=True)
        write_new(p, data)
        checksums[name] = digest(data)
        provenance.append({"id": sid, "uri": source["uri"], "observed_at": source["observed_at"],
                           "kind": "OBSERVED", "archive_path": name, "sha256": digest(data)})
    manifest = {"schema": "FS_V331_PRELOCK_EVIDENCE_V1", "state": "SHADOW",
                "lock_at": lock_at, "run_at": run_at,
                "files": dict(sorted(checksums.items())), "sources": provenance, "gold_lock": False}
    data = canonical(manifest)
    write_new(out / "manifest.json", data)
    write_new(out / "FINALIZED.sha256", (digest(data) + "\n").encode())
    return {"status": "SHADOW_FROZEN", "manifest_sha256": digest(data), "source_count": len(provenance)}


def verify_archive(target):
    """Hash readback is not engine replay, calibration, or independent audit."""
    out = Path(target)
    try:
        raw = (out / "manifest.json").read_bytes()
        if (out / "FINALIZED.sha256").read_text().strip() != digest(raw):
            raise ValueError("manifest checksum mismatch")
        data = json.loads(raw)
        if data.get("schema") != "FS_V331_PRELOCK_EVIDENCE_V1" or data.get("state") != "SHADOW":
            raise ValueError("invalid manifest")
        if not {"inputs.json", "league_config.json", "decision.json"}.issubset(data.get("files", {})):
            raise ValueError("incomplete manifest")
        lock = parse_time(data["lock_at"])
        if parse_time(data["run_at"]) > lock:
            raise ValueError("post-lock timestamp")
        for name, expected in data["files"].items():
            if name.startswith("/") or ".." in Path(name).parts or digest((out / name).read_bytes()) != expected:
                raise ValueError("file mismatch")
        if not data.get("sources"):
            raise ValueError("missing provenance")
        for s in data["sources"]:
            if s["kind"] != "OBSERVED" or parse_time(s["observed_at"]) > lock:
                raise ValueError("post-lock/reconstructed source")
            if data["files"][s["archive_path"]] != s["sha256"]:
                raise ValueError("provenance hash mismatch")
        return {"integrity": "PASS", "manifest_sha256": digest(raw), "replay_executed": False,
                "stat_validated": False, "gold_lock": False}
    except (OSError, ValueError, KeyError, TypeError) as e:
        return {"integrity": "FAIL", "reason": str(e), "replay_executed": False,
                "stat_validated": False, "gold_lock": False}


def promotion_gate(gates, config, backtest):
    """Diagnostic eligibility only. This function NEVER sets gold=true."""
    if not isinstance(gates, dict) or not isinstance(config, dict) or not isinstance(backtest, dict):
        raise ValueError("gate/config/backtest maps required")
    missing_gates = [g for g in GATES if not isinstance(gates.get(g), dict) or
                     gates[g].get("status") != "VERIFICATO" or not gates[g].get("evidence_sha256")]
    rules = config.get("rules", {})
    missing_rules = [r for r in REQUIRED_RULES if not isinstance(rules.get(r), dict) or
                     rules[r].get("status") != "CERTIFICATA"]
    required = ("preregistered", "rolling_origin", "out_of_sample", "observed_official",
                "baseline_comparison_pass", "independent_auditor_pass")
    enough = isinstance(backtest.get("n_real_events"), int) and isinstance(backtest.get("preregistered_min_events"), int) and backtest["n_real_events"] >= backtest["preregistered_min_events"] > 0
    statistical = (all(backtest.get(k) is True for k in required) and
                   backtest.get("has_reconstructed") is False and bool(backtest.get("evidence_sha256")) and enough)
    blockers = []
    if missing_gates:
        blockers.append("GATES_OPEN")
    if missing_rules:
        blockers.append("UNCERTIFIED_RULES")
    if not statistical:
        blockers.append("STAT_NOT_VALIDATED")
    return {"status": "SHADOW_BLOCKED" if blockers else "GOLD_ELIGIBLE_FOR_CTO_REVIEW",
            "gold_lock": False, "gold_set": False, "blockers": blockers,
            "missing_gates": missing_gates, "missing_rules": missing_rules,
            "tech_pass_evidence_complete": not missing_gates and not missing_rules,
            "stat_evidence_complete": bool(statistical)}
