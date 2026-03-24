"""
dataclasses para sistema de diagnóstico e root cause inference.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class CorrelationResult:
    """resultado da correlação entre duas métricas."""

    metric_a: str
    metric_b: str
    pearson_r: float
    timestamp_diff_seconds: Optional[float] = None
    is_positive: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_a": self.metric_a,
            "metric_b": self.metric_b,
            "pearson_r": self.pearson_r,
            "timestamp_diff_seconds": self.timestamp_diff_seconds,
            "is_positive": self.is_positive,
        }


@dataclass
class Evidence:
    """evidência para suportar uma hipótese de causa raiz."""

    metric_name: str
    metric_value: float
    baseline_value: float
    change_magnitude: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    evidence_type: str = "anomaly"

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "baseline_value": self.baseline_value,
            "change_magnitude": self.change_magnitude,
            "timestamp": self.timestamp.isoformat(),
            "evidence_type": self.evidence_type,
        }


@dataclass
class RootCauseResult:
    """resultado da análise de causa raiz."""

    possible_cause: str
    confidence: float
    reasoning: str
    correlation: str
    contributing_factors: list[str] = field(default_factory=list)
    hypotheses: list[dict[str, Any]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    requires_human_intervention: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "possible_cause": self.possible_cause,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "correlation": self.correlation,
            "contributing_factors": self.contributing_factors,
            "hypotheses": self.hypotheses,
            "timestamp": self.timestamp.isoformat(),
            "requires_human_intervention": self.requires_human_intervention,
        }
