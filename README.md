# LineageLens

A minimal data-lineage tracker, plus a worked incident: a simulated
4-stage dealer point-of-sale lending pipeline with a deliberately
introduced, specific bug, diagnosed using the lineage trace instead of
re-deriving the pipeline by hand.

```
raw_applications -> income_normalized -> risk_scored -> decisions
```

## The bug

A stray leftover unit conversion in the income-normalization stage:
`monthly_income = annual_income / 12 / 100` instead of
`annual_income / 12` — a 100x shrink that inflates every applicant's
debt-to-income ratio by the same 100x and pushes every applicant,
including clearly creditworthy ones, into `REJECTED`.

## The diagnostic

`diagnose_bad_output()` pulls one applicant's full lineage trace and
walks it stage by stage, checking a sanity invariant at each hop
(normalized income should land within 2x of a straightforward
annual-to-monthly conversion; a DTI ratio above a sane ceiling is itself
a red flag). The first stage whose invariant fails is reported as the
culprit — not "something's wrong," but the exact stage, the exact
formula, and the exact 100x discrepancy.

## Run it

```
python3 cli.py       # buggy run -> diagnosis -> fixed run -> verification
python3 -m pytest -q # 8 tests
```

`cli.py` runs the pipeline buggy, shows the lineage-based diagnosis
correctly naming `income_normalized` as the culprit, then runs it fixed
and verifies all 5 sample applicants' DTI/decision against a
hand-computed expectation.

## A bug caught in the diagnostic itself, before delivery

The first version of the stage-1 sanity check used a relative-difference
formula (`abs(actual - expected) / expected`) that is mathematically
incapable of exceeding 1.0 when a value is shrunk rather than inflated —
so a 100x shrink was silently missed and the diagnostic instead flagged
the *next* stage as the culprit. Fixed by checking the ratio of actual to
expected directly (flagging anything outside roughly a 2x band in either
direction), re-run, and confirmed it now correctly names
`income_normalized` as the actual source.

## Files

- `lineage.py` — `LineageTracker`: log a transformation, trace one
  applicant+run's full history.
- `pipeline.py` — the 4-stage pipeline, `buggy=True/False`.
- `diagnose.py` — `diagnose_bad_output()`, the stage-by-stage invariant
  check.
- `cli.py` — the full buggy -> diagnose -> fix -> verify demo.
- `tests/test_lineagelens.py` — 8 tests.
