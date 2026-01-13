# Diff module - Feature #10: Diff-Aware Regeneration
from .diff_engine import (
    FileDiff,
    DiffResult,
    compute_diff,
)

__all__ = [
    "FileDiff",
    "DiffResult",
    "compute_diff",
]
