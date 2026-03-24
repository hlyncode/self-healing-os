"""
detector de anomalias usando z-score.
"""

from datetime import datetime, UTC
from typing import Optional

import numpy as np

from src.config import get_settings
from src.detection.baseline import BaselineModel
from src.models.types import Anomaly, AnomalyType, MetricType, Severity


class ZScoreDetector:
    """detector de anomalias baseado em z-score."""

    def __init__(self, threshold: Optional[float] = None) -> None:
        self.settings = get_settings()
        self.threshold = threshold or self.settings.zscore_threshold
        self.baseline_model = BaselineModel()

    def detect(self, metric_name: str, value: float) -> Optional[Anomaly]:
        """detecta anomalia em um valor de métrica."""
        self.baseline_model.update(metric_name, value)

        # Check if we have enough data for this metric to make a reliable detection
        stats = self.baseline_model.get_statistics(metric_name)
        if stats["sample_count"] < 10:
            # Not enough historical data to detect anomalies reliably
            return None

        score = self.baseline_model.get_anomaly_score(metric_name, value)

        if score <= self.threshold:
            return None

        expected = self.baseline_model.get_expected_value(metric_name)
        anomaly_type = self._classify_anomaly(value, expected)

        severity = self._calculate_severity(score)

        return Anomaly(
            metric_name=metric_name,
            anomaly_type=anomaly_type,
            timestamp=datetime.now(UTC),
            severity=severity,
            score=score,
            expected_value=expected,
            actual_value=value,
        )

    def _classify_anomaly(
        self, actual: Optional[float], expected: Optional[float]
    ) -> AnomalyType:
        """classifica o tipo de anomalia."""
        if expected is None or actual is None:
            return AnomalyType.OUTLIER

        if actual > expected:
            return AnomalyType.SPIKE

        if actual < expected:
            return AnomalyType.DROPOUT

        return AnomalyType.OUTLIER

    def _calculate_severity(self, score: float) -> Severity:
        """calcula severidade baseada no score."""
        # Use absolute thresholds for severity based on z-score values
        if score > 10.0:
            return Severity.CRITICAL
        if score > 6.0:
            return Severity.CRITICAL
        if score > 4.0:
            return Severity.ERROR
        if score > 3.0:
            return Severity.WARNING
        return Severity.INFO

    def detect_batch(
        self, metrics: list[tuple[str, float]]
    ) -> list[Anomaly]:
        """detecta anomalias em múltiplas métricas."""
        anomalies = []
        for metric_name, value in metrics:
            anomaly = self.detect(metric_name, value)
            if anomaly:
                anomalies.append(anomaly)
        return anomalies

    def reset(self) -> None:
        """reseta o detector."""
        self.baseline_model.reset()
