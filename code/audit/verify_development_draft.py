"""Verify that the Chinese development manuscript repeats only current result values.

This script is deliberately a *read-only source check*: it never opens
Secondary, refits a model, or changes upstream results.  It checks selected
numbers that appear in the manuscript against the authoritative P0/Q2/Q3/Q4
machine-readable artifacts and writes a traceable verification record.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANUSCRIPT = ROOT / "paper" / "开发证据稿_全篇_非最终.md"
OUT_JSON = ROOT / "paper" / "audits" / "development_draft_numeric_verification.json"
OUT_MD = ROOT / "paper" / "audits" / "development_draft_numeric_verification.md"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def find_row(rows: list[dict[str, str]], **criteria: str) -> dict[str, str]:
    selected = [row for row in rows if all(row[key] == value for key, value in criteria.items())]
    if len(selected) != 1:
        raise AssertionError(f"{criteria} expected one row, found {len(selected)}")
    return selected[0]


def require_text(text: str, fragment: str, source: str, checks: list[dict[str, str]]) -> None:
    if fragment not in text:
        raise AssertionError(f"Manuscript missing {fragment!r} from {source}")
    checks.append({"check": fragment, "source": source, "status": "PASS"})


def main() -> None:
    manuscript = MANUSCRIPT.read_text(encoding="utf-8")
    checks: list[dict[str, str]] = []

    p0 = json.loads((ROOT / "data" / "processed" / "p0_summary.json").read_text(encoding="utf-8"))
    assert p0["p0_status"] == "pass" and p0["output_files"]["cycle_model_view"]["rows"] == 99279
    require_text(manuscript, "124 枚电芯和 99,279 行", "data/processed/p0_summary.json", checks)
    require_text(manuscript, "字段—循环掩码", "data/processed/p0_summary.json", checks)

    labels = read_csv(ROOT / "data" / "processed" / "cell_labels.csv")
    life = sorted(float(row["cycle_life_table9"]) for row in labels)
    assert len(life) == 124
    q1 = life[30] + 0.75 * (life[31] - life[30])
    median = (life[61] + life[62]) / 2
    q3 = life[92] + 0.25 * (life[93] - life[92])
    assert round(sum(life) / len(life), 2) == 801.64 and q1 == 498.75 and median == 736.5 and q3 == 946.5
    require_text(manuscript, "801.64 cycle", "data/processed/cell_labels.csv", checks)
    require_text(manuscript, "498.75 / 946.50", "data/processed/cell_labels.csv", checks)

    q2 = json.loads((ROOT / "results" / "Q2" / "experiments" / "round1" / "metrics" / "comparison_metrics.json").read_text(encoding="utf-8"))
    assert round(q2["M1"]["rmse_log"], 5) == 0.37169 and round(q2["M2"]["mae_log"], 5) == 0.25102
    require_text(manuscript, "0.37169", "results/Q2/experiments/round1/metrics/comparison_metrics.json", checks)
    require_text(manuscript, "0.25102", "results/Q2/experiments/round1/metrics/comparison_metrics.json", checks)
    q2b = json.loads((ROOT / "robustness" / "Q2" / "metrics" / "q2_bootstrap_summary.json").read_text(encoding="utf-8"))
    assert q2b["requested_gate_facts"]["mae_ci_upper_lt_zero"] is False
    require_text(manuscript, "[−0.07245, 0.02620]", "robustness/Q2/metrics/q2_bootstrap_summary.json", checks)

    m3r = find_row(read_csv(ROOT / "results" / "Q3" / "experiments" / "round3_raw_curve_challenger" / "tables" / "m3r_raw_curve_window_metrics.csv"), model_id="M3R", k="5")
    assert round(float(m3r["rmse_log"]), 5) == 0.24070 and round(float(m3r["cell_equal_soh_rmse"]), 5) == 0.03299
    require_text(manuscript, "RMSE_log=0.24070", "results/Q3/experiments/round3_raw_curve_challenger/tables/m3r_raw_curve_window_metrics.csv", checks)
    m2 = find_row(read_csv(ROOT / "results" / "Q3" / "experiments" / "round2_joint" / "tables" / "joint_window_metrics.csv"), model_id="M2", k="100")
    assert round(float(m2["rmse_log"]), 5) == 0.23174 and round(float(m2["cell_equal_soh_rmse"]), 5) == 0.03475
    require_text(manuscript, "RMSE_log=0.23174", "results/Q3/experiments/round2_joint/tables/joint_window_metrics.csv", checks)

    flow = {row["stage"]: int(row["count"]) for row in read_csv(ROOT / "results" / "Q4" / "experiments" / "train_dry_run_round1" / "tables" / "q4_candidate_flow.csv")}
    assert flow["候选格点总数"] == 3653 and flow["双空间且支持率≥80%（Q2 暂定候选）"] == 1775
    require_text(manuscript, "3,653", "results/Q4/experiments/train_dry_run_round1/tables/q4_candidate_flow.csv", checks)
    require_text(manuscript, "1,775", "results/Q4/experiments/train_dry_run_round1/tables/q4_candidate_flow.csv", checks)
    q4 = json.loads((ROOT / "results" / "Q4" / "experiments" / "existing_policy_round2_m2k100" / "metrics" / "q4_existing_policy_summary.json").read_text(encoding="utf-8"))
    assert q4["policy_count"] == 60 and q4["multi_cell_policy_count"] == 19 and q4["development_pareto_count"] == 4 and q4["secondary_read"] is False
    require_text(manuscript, "60 个已有策略", "results/Q4/experiments/existing_policy_round2_m2k100/metrics/q4_existing_policy_summary.json", checks)
    require_text(manuscript, "4 个开发池非支配案例", "results/Q4/experiments/existing_policy_round2_m2k100/metrics/q4_existing_policy_summary.json", checks)

    payload = {"status": "PASS", "manuscript": str(MANUSCRIPT), "checks": checks, "secondary_read": False}
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rows = "\n".join(f"| {item['check']} | `{item['source']}` | {item['status']} |" for item in checks)
    OUT_MD.write_text(
        "# 开发证据稿核心数字自动回查\n\n"
        "> 状态：**PASS**。脚本只读现有结果，不读取 Secondary、不重新拟合模型。\n\n"
        "| 文稿片段/数值 | 机器可读来源 | 状态 |\n|---|---|---|\n"
        + rows
        + "\n\n所有检查通过后，文稿中的数值仍仅代表开发期证据；本审计不替代 Q3 人工裁决或 Secondary 最终压力测试。\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "PASS", "checks": len(checks), "secondary_read": False}, ensure_ascii=False))


if __name__ == "__main__":
    main()
