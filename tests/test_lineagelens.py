import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from diagnose import diagnose_bad_output
from lineage import LineageTracker
from pipeline import APPLICANTS, run_pipeline


def test_buggy_pipeline_rejects_everyone_including_creditworthy_applicant():
    tracker = LineageTracker()
    results = run_pipeline(tracker, "r1", buggy=True)
    assert all(r["decision"] == "REJECTED" for r in results)


def test_fixed_pipeline_approves_all_sample_applicants():
    tracker = LineageTracker()
    results = run_pipeline(tracker, "r1", buggy=False)
    assert all(r["decision"] == "APPROVED" for r in results)


def test_fixed_pipeline_dti_matches_hand_computation():
    tracker = LineageTracker()
    results = run_pipeline(tracker, "r1", buggy=False)
    for app, result in zip(APPLICANTS, results):
        expected = app["monthly_debt"] / (app["annual_income"] / 12)
        assert abs(expected - result["dti_ratio"]) < 1e-9


def test_trace_returns_steps_in_pipeline_order_for_one_applicant():
    tracker = LineageTracker()
    run_pipeline(tracker, "r1", buggy=True)
    trace = tracker.trace("A001", "r1")
    assert [s["field"] for s in trace] == ["monthly_income", "dti_ratio", "decision"]


def test_trace_is_scoped_to_one_applicant_and_run_only():
    tracker = LineageTracker()
    run_pipeline(tracker, "r1", buggy=True)
    run_pipeline(tracker, "r2", buggy=False)
    trace_a1_r1 = tracker.trace("A001", "r1")
    trace_a1_r2 = tracker.trace("A001", "r2")
    trace_a2_r1 = tracker.trace("A002", "r1")
    assert all(s["applicant_id"] == "A001" and s["run_id"] == "r1" for s in trace_a1_r1)
    assert all(s["applicant_id"] == "A001" and s["run_id"] == "r2" for s in trace_a1_r2)
    assert all(s["applicant_id"] == "A002" and s["run_id"] == "r1" for s in trace_a2_r1)
    assert trace_a1_r1[0]["detail"] != trace_a1_r2[0]["detail"]  # buggy vs fixed differ


def test_diagnose_identifies_income_normalized_as_culprit_on_buggy_run():
    tracker = LineageTracker()
    run_pipeline(tracker, "r1", buggy=True)
    result = diagnose_bad_output(tracker, "A001", "r1", annual_income=600000, print_output=False)
    assert result is not None
    assert result["culprit_stage"] == "income_normalized"
    assert abs(result["ratio_off"] - 100.0) < 1e-6


def test_diagnose_finds_no_anomaly_on_fixed_run():
    tracker = LineageTracker()
    run_pipeline(tracker, "r1", buggy=False)
    result = diagnose_bad_output(tracker, "A001", "r1", annual_income=600000, print_output=False)
    assert result is None


def test_diagnose_scoped_to_the_specific_run_requested():
    """A tracker holding both a buggy and a fixed run must diagnose each
    run independently -- asking about the fixed run should not surface
    the buggy run's anomaly."""
    tracker = LineageTracker()
    run_pipeline(tracker, "buggy_run", buggy=True)
    run_pipeline(tracker, "fixed_run", buggy=False)
    assert diagnose_bad_output(tracker, "A001", "buggy_run", 600000, print_output=False) is not None
    assert diagnose_bad_output(tracker, "A001", "fixed_run", 600000, print_output=False) is None
