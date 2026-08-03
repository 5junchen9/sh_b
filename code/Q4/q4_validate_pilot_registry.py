"""Validate the frozen 3-strategy x 3-cell Q4 pilot registry before Q3 processing."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


SCRIPT = Path(__file__).resolve()
ROOT = SCRIPT.parents[2]
DEFAULT_REGISTRY = ROOT / "results" / "Q4" / "experiments" / "pilot_design_round1" / "tables" / "q4_k100_pilot_allocation_template.csv"
REPRESENTATIVES = ROOT / "results" / "Q4" / "experiments" / "pilot_design_round1" / "tables" / "q4_k100_pilot_representatives.csv"
PROTOCOL = ROOT / "methods" / "Q4" / "q4_k100_pilot_protocol.md"
OUT = ROOT / "results" / "Q4" / "experiments" / "pilot_registry_preflight_round1"
TABLES, METRICS, LOGS = (OUT / x for x in ("tables", "metrics", "logs"))
REPLICATES_PER_STRATEGY = 3
EXPECTED_SLOTS = 9
STATUS = {"planned", "running", "incomplete", "Q3_confirmed", "Q3_not_confirmed"}
K5_STATUS = {"not_due", "complete_no_alert", "complete_alert", "incomplete"}
REQUIRED = ["pilot_id", "barcode", "C1", "Q1_percent", "C2", "q", "single_stage_0_80", "tau_0_80_min", "candidate_source", "status", "cycle_5_complete", "k5_screen_status", "cycle_100_complete", "raw_data_path", "p0_compatible_view_path", "notes"]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bool_series(series: pd.Series, name: str) -> pd.Series:
    values = series.astype(str).str.strip().str.lower()
    mapping = {"true": True, "false": False, "1": True, "0": False}
    if not values.isin(mapping).all():
        bad = sorted(values.loc[~values.isin(mapping)].unique())
        raise RuntimeError(f"{name} contains invalid boolean values: {bad}")
    return values.map(mapping).astype(bool)


def stable_key(frame: pd.DataFrame) -> pd.Series:
    return frame[["C1", "Q1_percent", "C2"]].astype(float).round(8).astype(str).agg("|".join, axis=1)


def validate(registry: pd.DataFrame, representatives: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    missing = set(REQUIRED).difference(registry.columns)
    if missing:
        raise RuntimeError(f"Registry missing required columns: {sorted(missing)}")
    if len(registry) != EXPECTED_SLOTS:
        raise RuntimeError(f"Frozen pilot batch must have exactly {EXPECTED_SLOTS} slots, got {len(registry)}.")
    if registry.pilot_id.astype(str).str.strip().eq("").any() or registry.pilot_id.duplicated().any():
        raise RuntimeError("pilot_id must be non-empty and unique.")
    registry = registry.copy()
    registry["cycle_5_complete"] = bool_series(registry["cycle_5_complete"], "cycle_5_complete")
    registry["cycle_100_complete"] = bool_series(registry["cycle_100_complete"], "cycle_100_complete")
    if not set(registry.status).issubset(STATUS):
        raise RuntimeError(f"Invalid status: {sorted(set(registry.status).difference(STATUS))}")
    if not set(registry.k5_screen_status).issubset(K5_STATUS):
        raise RuntimeError(f"Invalid k5_screen_status: {sorted(set(registry.k5_screen_status).difference(K5_STATUS))}")
    registry["strategy_key"] = stable_key(registry)
    representatives = representatives.copy()
    representatives["strategy_key"] = stable_key(representatives)
    if set(registry.strategy_key) != set(representatives.strategy_key):
        raise RuntimeError("Registry strategies differ from the three frozen representative strategies.")
    if not (registry.groupby("strategy_key").size() == REPLICATES_PER_STRATEGY).all():
        raise RuntimeError("Each frozen strategy must occupy exactly three physical-cell slots.")
    issues: list[str] = []
    barcode = registry.barcode.astype(str).str.strip()
    assigned = barcode.ne("")
    if barcode.loc[assigned].duplicated().any():
        raise RuntimeError("Assigned physical barcodes must be unique across all nine slots.")
    for i, row in registry.iterrows():
        issue = []
        is_assigned = bool(assigned.loc[i])
        if row.status != "planned" and not is_assigned:
            issue.append("非 planned 状态必须填写 barcode")
        if row.cycle_5_complete and row.k5_screen_status == "not_due":
            issue.append("cycle_5_complete=True 时 k5_screen_status 不能为 not_due")
        if row.k5_screen_status != "not_due" and not row.cycle_5_complete:
            issue.append("已有 k=5 状态时必须完成第 5 循环")
        if row.cycle_100_complete and not row.cycle_5_complete:
            issue.append("完成第 100 循环前必须完成第 5 循环")
        if row.status == "Q3_confirmed":
            if not row.cycle_100_complete:
                issue.append("Q3_confirmed 必须完成第 100 循环")
            if not str(row.raw_data_path).strip() or not str(row.p0_compatible_view_path).strip():
                issue.append("Q3_confirmed 必须保存原始数据路径和 P0 兼容长表路径")
        issues.append("；".join(issue) if issue else "通过")
    registry["validation"] = issues
    if any(x != "通过" for x in issues):
        raise RuntimeError("Registry state conflicts: " + " | ".join(x for x in issues if x != "通过"))
    return registry, ["all_slots_unassigned"] if not assigned.any() else ["assigned_or_running"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY, help="Pilot registry CSV; defaults to the generated 9-slot allocation template.")
    args = parser.parse_args()
    for directory in (TABLES, METRICS, LOGS):
        directory.mkdir(parents=True, exist_ok=True)
    registry_path = args.registry.resolve()
    if not registry_path.exists() or not REPRESENTATIVES.exists() or not PROTOCOL.exists():
        raise RuntimeError("Registry, frozen representatives, or pilot protocol is missing.")
    registry = pd.read_csv(registry_path, keep_default_na=False)
    representatives = pd.read_csv(REPRESENTATIVES)
    checked, state = validate(registry, representatives)
    checked.to_csv(TABLES / "q4_pilot_registry_validation.csv", index=False, encoding="utf-8-sig")
    summary = {
        "question": "Q4",
        "round": "pilot_registry_preflight_round1",
        "status": "registry_preflight_passed",
        "registry_state": state,
        "scope": "Schema and frozen-batch validation only; this does not run Q3, create pilot observations, or produce a recommendation.",
        "slot_count": int(len(checked)),
        "assigned_barcode_count": int(checked.barcode.astype(str).str.strip().ne("").sum()),
        "strategy_count": int(checked.strategy_key.nunique()),
        "input_sha256": {"registry": sha(registry_path), "q4_k100_pilot_representatives.csv": sha(REPRESENTATIVES), "q4_k100_pilot_protocol.md": sha(PROTOCOL)},
        "script_sha256": sha(SCRIPT),
        "environment": {"python": sys.version, "platform": platform.platform(), "pandas": pd.__version__},
        "outputs": ["tables/q4_pilot_registry_validation.csv"],
        "execution_timestamp": datetime.now(timezone.utc).isoformat(),
    }
    payload = json.dumps(summary, ensure_ascii=False, indent=2)
    (METRICS / "q4_pilot_registry_preflight_summary.json").write_text(payload, encoding="utf-8")
    (OUT / "run_summary.json").write_text(payload, encoding="utf-8")
    (LOGS / "run.log").write_text(payload + "\n", encoding="utf-8")
    print(json.dumps({"status": summary["status"], "registry_state": state, "assigned_barcode_count": summary["assigned_barcode_count"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
