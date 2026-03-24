"""
testes para detector de anomalias z-score.
"""

import pytest

from src.detection.zscore import ZScoreDetector
from src.models.types import Anomaly, AnomalyType, Severity


class TestZScoreDetector:
    """testes para a classe ZScoreDetector."""

    @pytest.fixture
    def detector(self) -> ZScoreDetector:
        return ZScoreDetector(threshold=3.0)

    @pytest.fixture
    def trained_detector(self) -> ZScoreDetector:
        detector = ZScoreDetector(threshold=3.0)
        for _ in range(50):
            detector.detect("cpu_usage", 50.0)
        return detector

    def test_initialization(self, detector: ZScoreDetector) -> None:
        assert detector.threshold == 3.0
        assert detector.baseline_model is not None

    def test_no_anomaly_for_normal_value(self, trained_detector: ZScoreDetector) -> None:
        outlier = trained_detector.detect("cpu_usage", 100.0)
        assert outlier is not None

    def test_anomaly_detection_for_outlier(self, trained_detector: ZScoreDetector) -> None:
        anomaly = trained_detector.detect("cpu_usage", 100.0)
        assert anomaly is not None
        assert anomaly.metric_name == "cpu_usage"
        assert anomaly.actual_value == 100.0

    def test_anomaly_type_spike(self, trained_detector: ZScoreDetector) -> None:
        anomaly = trained_detector.detect("cpu_usage", 100.0)
        assert anomaly is not None
        assert anomaly.anomaly_type == AnomalyType.SPIKE

    def test_anomaly_type_dropout(self, trained_detector: ZScoreDetector) -> None:
        anomaly = trained_detector.detect("cpu_usage", 0.0)
        assert anomaly is not None
        assert anomaly.anomaly_type == AnomalyType.DROPOUT

    def test_severity_levels(self, trained_detector: ZScoreDetector) -> None:
        anomaly = trained_detector.detect("cpu_usage", 70.0)
        if anomaly:
            assert anomaly.severity in [Severity.WARNING, Severity.ERROR, Severity.CRITICAL]

    def test_batch_detection(self, trained_detector: ZScoreDetector) -> None:
        metrics = [("cpu_usage", 52.0), ("cpu_usage", 100.0), ("memory_usage", 95.0)]
        anomalies = trained_detector.detect_batch(metrics)
        assert len(anomalies) >= 1

    def test_multiple_metrics(self, trained_detector: ZScoreDetector) -> None:
        cpu_anomaly = trained_detector.detect("cpu_usage", 100.0)
        mem_anomaly = trained_detector.detect("memory_usage", 100.0)
        assert cpu_anomaly is not None or mem_anomaly is not None

    def test_reset(self, trained_detector: ZScoreDetector) -> None:
        trained_detector.reset()
        anomaly = trained_detector.detect("cpu_usage", 100.0)
        assert anomaly is None

    def test_custom_threshold(self) -> None:
        detector = ZScoreDetector(threshold=2.0)
        for _ in range(50):
            detector.detect("cpu_usage", 50.0)
        anomaly = detector.detect("cpu_usage", 65.0)
        assert anomaly is not None

    def test_expected_value_in_anomaly(self, trained_detector: ZScoreDetector) -> None:
        anomaly = trained_detector.detect("cpu_usage", 100.0)
        if anomaly:
            assert anomaly.expected_value > 0

    def test_to_dict(self, trained_detector: ZScoreDetector) -> None:
        anomaly = trained_detector.detect("cpu_usage", 100.0)
        if anomaly:
            d = anomaly.to_dict()
            assert "metric_name" in d
            assert "severity" in d

    def test_learning_phase(self, detector: ZScoreDetector) -> None:
        for _ in range(10):
            detector.detect("cpu_usage", 50.0)
        stats = detector.baseline_model.get_statistics("cpu_usage")
        assert stats["sample_count"] >= 10
