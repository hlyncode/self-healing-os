"""
definições de tipos de dados do sistema self-healing-os.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class MetricType(Enum):
    """tipos de métricas suportadas pelo sistema."""

    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DISK_IO = "disk_io"
    NETWORK_IO = "network_io"
    REQUEST_LATENCY = "request_latency"
    ERROR_RATE = "error_rate"
    CUSTOM = "custom"


class Severity(Enum):
    """níveis de severidade de incidentes."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Status(Enum):
    """status de incidentes e diagnósticos."""

    ACTIVE = "active"
    RESOLVED = "resolved"
    PENDING = "pending"
    CONFIRMED = "confirmed"


class AnomalyType(Enum):
    """tipos de anomalias detectadas."""

    SPIKE = "spike"
    DROPOUT = "dropout"
    DRIFT = "drift"
    SEASONAL = "seasonal"
    TREND = "trend"
    OUTLIER = "outlier"


class RemedyType(Enum):
    """tipos de ações remedidoras."""

    RESTART_SERVICE = "restart_service"
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    CLEAR_CACHE = "clear_cache"
    RESTART_POD = "restart_pod"
    ADJUST_THRESHOLDS = "adjust_thresholds"
    NOTIFY_TEAM = "notify_team"
    MANUAL_INTERVENTION = "manual_intervention"


@dataclass
class Metric:
    """representa uma métrica coletada do sistema."""

    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime = field(default_factory=datetime.utcnow)
    labels: dict[str, str] = field(default_factory=dict)
    unit: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """converte métrica para dicionário."""
        return {
            "name": self.name,
            "value": self.value,
            "metric_type": self.metric_type.value,
            "timestamp": self.timestamp.isoformat(),
            "labels": self.labels,
            "unit": self.unit,
        }


@dataclass
class Anomaly:
    """representa uma anomalia detectada no sistema."""

    metric_name: str
    anomaly_type: AnomalyType
    timestamp: datetime = field(default_factory=datetime.utcnow)
    severity: Severity = Severity.WARNING
    score: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)
    expected_value: Optional[float] = None
    actual_value: Optional[float] = None

    def to_dict(self) -> dict[str, Any]:
        """converte anomalia para dicionário."""
        return {
            "metric_name": self.metric_name,
            "anomaly_type": self.anomaly_type.value,
            "timestamp": self.timestamp.isoformat(),
            "severity": self.severity.value,
            "score": self.score,
            "details": self.details,
            "expected_value": self.expected_value,
            "actual_value": self.actual_value,
        }


@dataclass
class Diagnosis:
    """resultado do diagnóstico de uma anomalia."""

    anomaly: Anomaly
    possible_causes: list[str] = field(default_factory=list)
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    related_metrics: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """converte diagnóstico para dicionário."""
        return {
            "anomaly": self.anomaly.to_dict(),
            "possible_causes": self.possible_causes,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
            "related_metrics": self.related_metrics,
        }


@dataclass
class Remedy:
    """ação remedidora recomendada."""

    remedy_type: RemedyType
    description: str
    target: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    estimated_impact: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """converte remediação para dicionário."""
        return {
            "remedy_type": self.remedy_type.value,
            "description": self.description,
            "target": self.target,
            "parameters": self.parameters,
            "estimated_impact": self.estimated_impact,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class Incident:
    """representa um incidente completo no sistema."""

    incident_id: str
    title: str
    status: Status = Status.ACTIVE
    severity: Severity = Severity.WARNING
    anomalies: list[Anomaly] = field(default_factory=list)
    diagnoses: list[Diagnosis] = field(default_factory=list)
    remedies: list[Remedy] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """converte incidente para dicionário."""
        return {
            "incident_id": self.incident_id,
            "title": self.title,
            "status": self.status.value,
            "severity": self.severity.value,
            "anomalies": [a.to_dict() for a in self.anomalies],
            "diagnoses": [d.to_dict() for d in self.diagnoses],
            "remedies": [r.to_dict() for r in self.remedies],
            "created_at": self.created_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "metadata": self.metadata,
        }
