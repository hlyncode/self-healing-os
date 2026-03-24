"""
módulo de remediação do sistema self-healing.
"""

from src.remediation.planner import RemediationPlanner, SuggestedRemedy
from src.remediation.remedy_registry import Remedy, RemedyRegistry

__all__ = [
    "Remedy",
    "RemedyRegistry",
    "RemediationPlanner",
    "SuggestedRemedy",
]
