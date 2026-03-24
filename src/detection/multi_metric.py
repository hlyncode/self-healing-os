"""
detector multi-métrica para análise de anomalias em múltiplas métricas.
"""

from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Protocol, Optional

import numpy as np

from src.models.types import Anomaly, AnomalyType, Severity


class Detector(Protocol):
    """protocolo para detectores de anomalia."""

    def detect(self, metric_name: str, value: float) -> Optional[Anomaly]:
        """detecta anomalia em uma métrica."""
        ...


@dataclass
class MetricTrend:
    """armazena dados de tendência para uma métrica."""

    values: list[float] = field(default_factory=list)
    timestamps: list[datetime] = field(default_factory=list)
    window_size: int = 10

    def add(self, value: float, timestamp: datetime) -> None:
        """adiciona novo valor à série temporal."""
        self.values.append(value)
        self.timestamps.append(timestamp)

        if len(self.values) > self.window_size:
            self.values.pop(0)
            self.timestamps.pop(0)

    def is_trending_up(self, threshold: float = 0.5) -> bool:
        """detecta se a métrica está em tendência de alta."""
        if len(self.values) < 3:
            return False

        recent = self.values[-3:]
        if not all(isinstance(v, (int, float)) for v in recent):
            return False

        return recent[-1] > recent[0] * (1 + threshold)

    def is_trending_down(self, threshold: float = 0.5) -> bool:
        """detecta se a métrica está em tendência de baixa."""
        if len(self.values) < 3:
            return False

        recent = self.values[-3:]
        if not all(isinstance(v, (int, float)) for v in recent):
            return False

        return recent[-1] < recent[0] * (1 - threshold)

    def get_trend_slope(self) -> float:
        """calcula inclinação da tendência."""
        if len(self.values) < 2:
            return 0.0

        x = np.arange(len(self.values))
        y = np.array(self.values, dtype=float)

        if np.all(x == x[0]) or np.all(y == y[0]):
            return 0.0

        coeffs = np.polyfit(x, y, 1)
        return coeffs[0]


@dataclass
class AnomalyResult:
    """resultado da detecção de anomalia por métrica."""

    metric_name: str
    is_anomaly: bool
    score: float
    detector_type: str
    trend_info: Optional[str] = None


class MultiMetricDetector:
    """detector que combina múltiplos detectores para análise completa."""

    def __init__(
        self,
        detectors: dict[str, Detector],
        trend_window: int = 10,
        trend_threshold: float = 0.5,
    ) -> None:
        self.detectors = detectors
        self.trend_window = trend_window
        self.trend_threshold = trend_threshold
        self.metric_trends: dict[str, MetricTrend] = {}
        self.anomaly_history: list[dict[str, AnomalyResult]] = []

    def detect_all(self, metrics: dict[str, float]) -> dict[str, AnomalyResult]:
        """detecta anomalias em todas as métricas fornecidas."""
        results: dict[str, AnomalyResult] = {}
        timestamp = datetime.now(UTC)

        for metric_name, value in metrics.items():
            self._update_trend(metric_name, value, timestamp)

            result = self._detect_metric(metric_name, value)
            results[metric_name] = result

        self.anomaly_history.append(results)
        if len(self.anomaly_history) > 100:
            self.anomaly_history.pop(0)

        return results

    def _detect_metric(
        self, metric_name: str, value: float
    ) -> AnomalyResult:
        """detecta anomalia em uma única métrica usando múltiplos detectores."""
        is_anomaly = False
        max_score = 0.0
        detector_type = "unknown"
        trend_info: Optional[str] = None

        if metric_name in self.detectors:
            detector = self.detectors[metric_name]
            anomaly = detector.detect(metric_name, value)

            if anomaly:
                is_anomaly = True
                max_score = anomaly.score
                detector_type = "baseline"
        else:
            for name, detector in self.detectors.items():
                anomaly = detector.detect(metric_name, value)
                if anomaly and anomaly.score > max_score:
                    max_score = anomaly.score
                    is_anomaly = True
                    detector_type = name

        trend_info = self._get_trend_info(metric_name)

        return AnomalyResult(
            metric_name=metric_name,
            is_anomaly=is_anomaly,
            score=max_score,
            detector_type=detector_type,
            trend_info=trend_info,
        )

    def _update_trend(self, metric_name: str, value: float, timestamp: datetime) -> None:
        """atualiza dados de tendência para uma métrica."""
        if metric_name not in self.metric_trends:
            self.metric_trends[metric_name] = MetricTrend(window_size=self.trend_window)

        self.metric_trends[metric_name].add(value, timestamp)

    def _get_trend_info(self, metric_name: str) -> Optional[str]:
        """obtém informação de tendência para uma métrica."""
        if metric_name not in self.metric_trends:
            return None

        trend = self.metric_trends[metric_name]

        if trend.is_trending_up(self.trend_threshold):
            return "trending_up"
        if trend.is_trending_down(self.trend_threshold):
            return "trending_down"

        slope = trend.get_trend_slope()
        if abs(slope) > 0.1:
            return "stable_with_variance"

        return "stable"

    def get_overall_anomaly_score(self) -> float:
        """calcula score geral de anomalia entre todas as métricas."""
        if not self.anomaly_history:
            return 0.0

        latest = self.anomaly_history[-1]
        scores = [result.score for result in latest.values()]

        if not scores:
            return 0.0

        anomaly_count = sum(1 for r in latest.values() if r.is_anomaly)
        avg_score = np.mean(scores)
        anomaly_ratio = anomaly_count / len(latest)

        overall = avg_score * 0.6 + anomaly_ratio * 0.4

        return min(1.0, max(0.0, overall))

    def detect_trending_problems(
        self, metric_name: str
    ) -> Optional[dict[str, any]]:
        """detecta problemas de tendência em uma métrica específica."""
        if metric_name not in self.metric_trends:
            return None

        trend = self.metric_trends[metric_name]

        if trend.is_trending_up(self.trend_threshold):
            return {
                "metric_name": metric_name,
                "trend": "up",
                "severity": self._calculate_trend_severity(trend),
                "slope": trend.get_trend_slope(),
            }

        if trend.is_trending_down(self.trend_threshold):
            return {
                "metric_name": metric_name,
                "trend": "down",
                "severity": self._calculate_trend_severity(trend),
                "slope": trend.get_trend_slope(),
            }

        return None

    def _calculate_trend_severity(self, trend: MetricTrend) -> Severity:
        """calcula severidade baseada na inclinação da tendência."""
        slope = abs(trend.get_trend_slope())

        if slope > 2.0:
            return Severity.CRITICAL
        if slope > 1.0:
            return Severity.ERROR
        if slope > 0.5:
            return Severity.WARNING

        return Severity.INFO

    def reset(self) -> None:
        """reseta o detector."""
        self.metric_trends.clear()
        self.anomaly_history.clear()
