"""Build a traceable manifest for the already executed Primary confirmations.

This utility deliberately distinguishes a *configuration ledger* from a
prospective preregistration: the Primary split had been explored before this
project's V2 workflow.  It reconstructs only facts recorded in the frozen
protocols and run summaries, and records any missing prospective gates instead
of inventing them.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "experiments" / "primary_confirmation_manifest_post_exposure.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def main() -> None:
    q2_run_rel = "results/Q2/experiments/q2b_primary_confirmation_round1/run_summary.json"
    q2_metrics_rel = "results/Q2/experiments/q2b_primary_confirmation_round1/metrics/q2b_primary_metrics.json"
    q3_run_rel = "results/Q3/experiments/primary_confirmation_round1/run_summary.json"
    q3_metrics_rel = "results/Q3/experiments/primary_confirmation_round1/metrics/q3_primary_metrics.json"
    source_relatives = [
        "methods/Q2/q2b_primary_confirmation_protocol.md",
        "methods/Q3/q3_primary_confirmation_protocol.md",
        "methods/Q2/decisions/human_primary_confirmation_choice_20260802.md",
        "methods/Q3/decisions/human_window_choice_20260802.md",
        "methods/Q3/decisions/human_window_claim_scope_20260802.md",
        "methods/Q3/q3_round2_scope_update.md",
        "code/Q2/q2b_primary_confirmation.py",
        "code/Q3/q3_primary_confirmation.py",
        q2_run_rel,
        q2_metrics_rel,
        q3_run_rel,
        q3_metrics_rel,
    ]
    q2_run, q2_metrics = read_json(q2_run_rel), read_json(q2_metrics_rel)
    q3_run, q3_metrics = read_json(q3_run_rel), read_json(q3_metrics_rel)
    manifest = {
        "schema_version": 1,
        "artifact_type": "post_exposure_primary_confirmation_configuration_ledger",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "critical_interpretation": (
            "This is a reconstructed traceability ledger, not a claim that a "
            "prospective preregistration existed before Primary was exposed. "
            "It must not be used to relabel Primary as an independent test set."
        ),
        "primary_status": "limited_confirmation_only",
        "secondary_status": "not_read_and_reserved_for_final_pressure_test",
        "shared_partition": {
            "train_label": "Train",
            "primary_label": "Prim. Test",
            "train_cells": 41,
            "primary_cells": 43,
        },
        "q2b": {
            "candidate_id": q2_run["frozen_selection"]["method_id"],
            "parameters": q2_run["frozen_selection"]["params"],
            "features": q2_run["frozen_selection"]["features"],
            "target_transform": q2_run["target_transform"],
            "inverse_transform": q2_run["inverse_transform"],
            "seed": q2_run["random_seed"],
            "reported_primary_metrics": q2_metrics,
            "protocol": "methods/Q2/q2b_primary_confirmation_protocol.md",
            "adjudication": "observed_not_adjudicated",
        },
        "q3": {
            "candidate_id": "M2_early_feature_Ridge_with_monotone_SOH_template",
            "legacy_primary_script_label": "M3 (historical label only)",
            "round2_alignment": (
                "The Primary implementation's early features and tuning rule align "
                "with Round 2 M2, not the later M3/M4 joint candidates."
            ),
            "windows": q3_run["windows"],
            "selected_alpha_by_window": q3_metrics["selected_alpha_by_window"],
            "target_transform": q3_run["target_transform"],
            "inverse_transform": q3_run["inverse_transform"],
            "formal_soh_metric": "cell_equal_soh_rmse",
            "seed": q3_run["random_seed"],
            "reported_primary_metrics": q3_metrics,
            "protocol": "methods/Q3/q3_primary_confirmation_protocol.md",
            "adjudication": "observed_not_adjudicated",
        },
        "missing_or_not_predeclared_gates": [
            "No prospective Primary configuration file was created before the recorded run.",
            "No automatic pass/fail threshold was predeclared for the executed Q2-B confirmation.",
            "No post-Primary model, feature, window, or threshold tuning is permitted.",
            "The later M3/M4 joint candidates and low-dimensional raw-curve challenger M3R were Train-only; they did not receive a Primary confirmation and cannot be described as externally confirmed.",
        ],
        "source_sha256": {relative: sha256(ROOT / relative) for relative in source_relatives},
        "rebuild_command": ".\\.venv\\Scripts\\python.exe l1\\code\\audit\\build_primary_confirmation_manifest.py",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
