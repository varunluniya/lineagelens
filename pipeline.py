"""
A simulated 4-stage dealer point-of-sale lending pipeline:

  raw_applications -> income_normalized -> risk_scored -> decisions

Each stage logs itself to a shared LineageTracker. `buggy=True` reproduces
a deliberate, specific defect: a stray unit-conversion error that shrinks
every applicant's monthly income by 100x.
"""
from __future__ import annotations

from lineage import LineageTracker

APPLICANTS = [
    {"id": "A001", "annual_income": 600000, "monthly_debt": 8000},
    {"id": "A002", "annual_income": 420000, "monthly_debt": 6000},
    {"id": "A003", "annual_income": 600000, "monthly_debt": 8000},
    {"id": "A004", "annual_income": 300000, "monthly_debt": 5000},
    {"id": "A005", "annual_income": 500000, "monthly_debt": 5000},
]


def income_normalize(annual_income: float, buggy: bool) -> tuple[float, str]:
    if buggy:
        formula = "monthly_income = annual_income / 12 / 100  [BUGGED]"
        value = annual_income / 12 / 100
    else:
        formula = "monthly_income = annual_income / 12"
        value = annual_income / 12
    return value, formula


def risk_score(monthly_debt: float, monthly_income: float) -> tuple[float, str]:
    formula = "dti_ratio = monthly_debt / monthly_income"
    return monthly_debt / monthly_income, formula


def decide(dti_ratio: float) -> tuple[str, str]:
    formula = "decision = APPROVED if dti_ratio <= 0.40 else REJECTED"
    return ("APPROVED" if dti_ratio <= 0.40 else "REJECTED"), formula


def run_pipeline(tracker: LineageTracker, run_id: str, buggy: bool) -> list[dict]:
    results = []
    for app in APPLICANTS:
        monthly_income, mi_formula = income_normalize(app["annual_income"], buggy)
        tracker.log_transformation(
            "raw_applications", "income_normalized", "monthly_income", mi_formula,
            run_id, app["id"],
            {"applicant_id": app["id"], "input_annual_income": app["annual_income"],
             "output_monthly_income": monthly_income},
        )

        dti_ratio, dti_formula = risk_score(app["monthly_debt"], monthly_income)
        tracker.log_transformation(
            "income_normalized", "risk_scored", "dti_ratio", dti_formula,
            run_id, app["id"],
            {"applicant_id": app["id"], "monthly_debt": app["monthly_debt"],
             "monthly_income": monthly_income, "dti_ratio": dti_ratio},
        )

        decision, dec_formula = decide(dti_ratio)
        tracker.log_transformation(
            "risk_scored", "decisions", "decision", dec_formula,
            run_id, app["id"],
            {"applicant_id": app["id"], "dti_ratio": dti_ratio, "decision": decision},
        )

        results.append({"id": app["id"], "dti_ratio": dti_ratio, "decision": decision})
    return results
