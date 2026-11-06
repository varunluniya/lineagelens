"""
Diagnostic: given a lineage trace for one applicant/run, walk it stage by
stage checking a sanity invariant at each hop, and report the first stage
whose invariant fails as the culprit.
"""
from __future__ import annotations

from lineage import LineageTracker


def diagnose_bad_output(tracker: LineageTracker, applicant_id: str, run_id: str,
                         annual_income: float, print_output: bool = True) -> dict | None:
    trace = tracker.trace(applicant_id, run_id)
    if print_output:
        print(f"--- Diagnosing applicant {applicant_id} (run {run_id}) ---")
        print("Full lineage trace for this applicant:")
        for step in trace:
            tag = " [BUGGED]" if "[BUGGED]" in step["formula"] else ""
            print(f"  {step['source_stage']:18s} -> {step['dest_stage']:18s} "
                  f"[{step['field']}]: {step['formula']}")
            print(f"      detail: {step['detail']}")

    for step in trace:
        if step["field"] == "monthly_income":
            expected = annual_income / 12
            actual = step["detail"]["output_monthly_income"]
            ratio_vs_expected = (actual / expected) if expected else float("inf")
            if actual == 0 or ratio_vs_expected < 0.5 or ratio_vs_expected > 2.0:  # more than 2x off
                ratio = expected / actual if actual else float("inf")
                if print_output:
                    print()
                    print(f"  >>> ANOMALY FOUND at stage 'income_normalized' "
                          f"({step['source_stage']} -> {step['dest_stage']}):")
                    print(f"      formula used: {step['formula']}")
                    print(f"      expected monthly_income ~= {expected:.2f} (annual_income / 12)")
                    print(f"      actual monthly_income   =  {actual:.2f}")
                    print(f"      ratio off by {ratio:.1f}x -- this is the stage that introduced the error.")
                    print()
                    print("DIAGNOSIS: the bug was introduced at stage 'income_normalized'.")
                return {"culprit_stage": "income_normalized", "ratio_off": ratio}

        if step["field"] == "dti_ratio":
            dti = step["detail"]["dti_ratio"]
            if dti > 5.0:  # sanity ceiling -- a real DTI ratio this high is implausible
                if print_output:
                    print()
                    print(f"  >>> ANOMALY FOUND at stage 'risk_scored' "
                          f"({step['source_stage']} -> {step['dest_stage']}): "
                          f"dti_ratio={dti:.4f} exceeds sanity ceiling")
                return {"culprit_stage": "risk_scored", "dti_ratio": dti}

    if print_output:
        print()
        print("No anomaly found -- all stage invariants hold for this applicant/run.")
    return None
