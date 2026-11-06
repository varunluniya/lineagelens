import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from diagnose import diagnose_bad_output
from lineage import LineageTracker
from pipeline import APPLICANTS, run_pipeline


def main():
    print("=" * 70)
    print("RUN 1 -- buggy pipeline")
    print("=" * 70)
    tracker = LineageTracker()
    buggy_results = run_pipeline(tracker, "run_buggy_001", buggy=True)
    for r in buggy_results:
        print(f"{r['id']}: DTI={r['dti_ratio']:.4f}  decision={r['decision']}")

    print()
    print("A001 (annual income Rs.600,000, monthly debt only Rs.8,000) getting")
    print("REJECTED is the visibly wrong output a reviewer would flag.")
    print()
    print("=" * 70)
    print("DIAGNOSIS -- tracing applicant A001's lineage")
    print("=" * 70)
    result = diagnose_bad_output(tracker, "A001", "run_buggy_001", annual_income=600000)
    assert result is not None and result["culprit_stage"] == "income_normalized"

    print()
    print("=" * 70)
    print("RUN 2 -- fixed pipeline")
    print("=" * 70)
    fixed_tracker = LineageTracker()
    fixed_results = run_pipeline(fixed_tracker, "run_fixed_001", buggy=False)
    for r in fixed_results:
        print(f"{r['id']}: DTI={r['dti_ratio']:.4f}  decision={r['decision']}")

    print()
    print("Re-running the diagnostic against A001 on the fixed run:")
    no_anomaly = diagnose_bad_output(fixed_tracker, "A001", "run_fixed_001", annual_income=600000)
    assert no_anomaly is None

    print()
    print("=" * 70)
    print("VERIFICATION -- every applicant's fixed-run DTI/decision vs. hand-computed expectation")
    print("=" * 70)
    all_match = True
    for app, result in zip(APPLICANTS, fixed_results):
        expected_dti = app["monthly_debt"] / (app["annual_income"] / 12)
        expected_decision = "APPROVED" if expected_dti <= 0.40 else "REJECTED"
        match = (abs(expected_dti - result["dti_ratio"]) < 1e-9
                 and expected_decision == result["decision"])
        all_match = all_match and match
        print(f"{app['id']}: expected_dti={expected_dti:.4f} expected_decision={expected_decision} | "
              f"pipeline_dti={result['dti_ratio']:.4f} pipeline_decision={result['decision']} | "
              f"{'OK' if match else 'MISMATCH'}")
    print()
    print(f"All {len(APPLICANTS)} applicants match hand-computed expectation: {all_match}")
    assert all_match


if __name__ == "__main__":
    main()
