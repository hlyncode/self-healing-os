"""
testes para o detector multi-métrica.
"""

from datetime import datetime, timedelta
from typing import Optional

import pytest

from src.detection.multi_metric import (
    MultiMetricDetector,
    MetricTrend,
    AnomalyResult,
)
from src.models.types import Anomaly, AnomalyType, Severity


class MockDetector:
    """mock detector para testes."""

    def __init__(self, should_detect: bool = False) -> None:
        self.should_detect = should_detect
        self.last_metric_name = ""
        self.last_value = 0.0

    def detect(self, metric_name: str, value: float) -> Optional[Anomaly]:
        """detecta anomalia simulada."""
        self.last_metric_name = metric_name
        self.last_value = value

        if self.should_detect:
            return Anomaly(
                metric_name=metric_name,
                anomaly_type=AnomalyType.OUTLIER,
                timestamp=datetime.utcnow(),
                severity=Severity.WARNING,
                score=0.8,
                actual_value=value,
            )

        return None


class TestMetricTrend:
    """testes para a classe metrictrend."""

    def test_add_and_check_trend(self) -> None:
        """testa adicionar valores e verificar tendência."""
        trend = MetricTrend(window_size=5)
        now = datetime.utcnow()

        trend.add(10.0, now)
        trend.add(11.0, now + timedelta(minutes=1))
        trend.add(12.0, now + timedelta(minutes=2))

        assert len(trend.values) == 3
        assert trend.is_trending_up(threshold=0.1) is True

    def test_trending_down(self) -> None:
        """testa detecção de tendência de queda."""
        trend = MetricTrend(window_size=5)
        now = datetime.utcnow()

        trend.add(12.0, now)
        trend.add(11.0, now + timedelta(minutes=1))
        trend.add(10.0, now + timedelta(minutes=2))

        assert trend.is_trending_down(threshold=0.1) is True

    def test_stable_trend(self) -> None:
        """testa que valores estáveis não são tendência."""
        trend = MetricTrend(window_size=5)
        now = datetime.utcnow()

        trend.add(10.0, now)
        trend.add(10.1, now + timedelta(minutes=1))
        trend.add(10.05, now + timedelta(minutes=2))

        assert trend.is_trending_up(threshold=0.1) is False
        assert trend.is_trending_down(threshold=0.1) is False

    def test_get_trend_slope(self) -> None:
        """testa cálculo de inclinação de tendência."""
        trend = MetricTrend(window_size=5)
        now = datetime.utcnow()

        trend.add(10.0, now)
        trend.add(20.0, now + timedelta(minutes=1))
        trend.add(30.0, now + timedelta(minutes=2))

        slope = trend.get_trend_slope()
        assert slope > 0


class TestMultiMetricDetector:
    """testes para a classe multimetricdetector."""

    def test_detects_anomaly_in_single_metric(self) -> None:
        """testa detecção de anomalia em métrica única."""
        detectors = {
            "cpu": MockDetector(should_detect=True),
        }

        multi_detector = MultiMetricDetector(detectors)

        metrics = {"cpu": 95.0}
        results = multi_detector.detect_all(metrics)

        assert "cpu" in results
        assert results["cpu"].is_anomaly is True

    def test_detects_anomalies_in_multiple_metrics(self) -> None:
        """testa detecção em múltiplas métricas."""
        detectors = {
            "cpu": MockDetector(should_detect=True),
            "memory": MockDetector(should_detect=False),
            "disk": MockDetector(should_detect=True),
        }

        multi_detector = MultiMetricDetector(detectors)

        metrics = {
            "cpu": 95.0,
            "memory": 50.0,
            "disk": 90.0,
        }

        results = multi_detector.detect_all(metrics)

        assert results["cpu"].is_anomaly is True
        assert results["memory"].is_anomaly is False
        assert results["disk"].is_anomaly is True

    def test_calculates_overall_score(self) -> None:
        """testa cálculo de score geral de anomalia."""
        detectors = {
            "cpu": MockDetector(should_detect=True),
            "memory": MockDetector(should_detect=False),
        }

        multi_detector = MultiMetricDetector(detectors)

        metrics = {"cpu": 95.0, "memory": 50.0}
        multi_detector.detect_all(metrics)

        overall_score = multi_detector.get_overall_anomaly_score()

        assert 0.0 <= overall_score <= 1.0

    def test_detects_trending_problems(self) -> None:
        """testa detecção de problemas de tendência."""
        detectors = {"cpu": MockDetector()}

        multi_detector = MultiMetricDetector(detectors, trend_threshold=0.1)

        now = datetime.utcnow()
        for i in range(10):
            multi_detector._update_trend("cpu", 50.0 + i * 5, now + timedelta(minutes=i))

        trend_problem = multi_detector.detect_trending_problems("cpu")

        assert trend_problem is not None
        assert trend_problem["trend"] == "up"

    def test_trend_update_over_time(self) -> None:
        """testa atualização de tendência ao longo do tempo."""
        detectors = {"latency": MockDetector()}

        multi_detector = MultiMetricDetector(detectors)

        now = datetime.utcnow()
        multi_detector._update_trend("latency", 10.0, now)
        multi_detector._update_trend("latency", 100.0, now + timedelta(minutes=1))

        results = multi_detector.detect_all({"latency": 100.0})

        assert results["latency"].trend_info is not None

    def test_empty_metrics(self) -> None:
        """testa com dicionário de métricas vazio."""
        detectors = {"cpu": MockDetector()}

        multi_detector = MultiMetricDetector(detectors)

        results = multi_detector.detect_all({})

        assert len(results) == 0

    def test_reset_clears_state(self) -> None:
        """testa que reset limpa o estado."""
        detectors = {"cpu": MockDetector(should_detect=True)}

        multi_detector = MultiMetricDetector(detectors)

        multi_detector.detect_all({"cpu": 95.0})
        assert len(multi_detector.anomaly_history) > 0

        multi_detector.reset()

        assert len(multi_detector.anomaly_history) == 0
        assert len(multi_detector.metric_trends) == 0
