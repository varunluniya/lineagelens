"""
LineageLens -- a minimal lineage tracker that records every transformation
a piece of data passes through, and lets you trace one specific record's
history backward through the pipeline to find exactly where a bad value
was introduced.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class LineageTracker:
    records: list[dict] = field(default_factory=list)

    def log_transformation(self, source_stage: str, dest_stage: str, field_name: str,
                            formula: str, run_id: str, applicant_id: str, detail: dict):
        self.records.append({
            "source_stage": source_stage,
            "dest_stage": dest_stage,
            "field": field_name,
            "formula": formula,
            "run_id": run_id,
            "applicant_id": applicant_id,
            "detail": detail,
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="microseconds"),
        })

    def trace(self, applicant_id: str, run_id: str) -> list[dict]:
        """Full lineage trace for one specific record in one specific run,
        in pipeline order."""
        return [r for r in self.records
                if r["applicant_id"] == applicant_id and r["run_id"] == run_id]
