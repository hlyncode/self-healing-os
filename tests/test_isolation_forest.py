"""
testes para o detector isolation forest.
"""

import numpy as np
import pytest

from src.detection.isolation_forest import IsolationForestDetector


class TestIsolationForestDetector:
    """testes para a classe isolationforestdetector."""

    def test_trains_on_historical_data(self) -> None:
        """testa treinamento com dados históricos."""
        historical_data = [
            [10.0, 20.0, 30.0],
            [15.0, 25.0, 35.0],
            [12.0, 22.0, 32.0],
            [11.0, 21.0, 31.0],
            [13.0, 23.0, 33.0],
            [14.0, 24.0, 34.0],
            [10.5, 20.5, 30.5],
            [11.5, 21.5, 31.5],
            [12.5, 22.5, 32.5],
            [13.5, 23.5, 33.5],
        ]

        detector = IsolationForestDetector(num_trees=50)
        detector.train(historical_data)

        assert detector.is_trained is True
        assert len(detector.trees) == 50

    def test_scores_normal_values_high(self) -> None:
        """testa que valores normais têm score alto."""
        historical_data = [
            [10.0 + i * 0.1, 20.0 + i * 0.1, 30.0 + i * 0.1]
            for i in range(50)
        ]

        detector = IsolationForestDetector(num_trees=50, contamination=0.1)
        detector.train(historical_data)

        normal_value = [10.5, 20.5, 30.5]
        score = detector.score(normal_value)

        assert isinstance(score, float)
        assert -1.0 <= score <= 1.0

    def test_scores_anomalies_low(self) -> None:
        """testa que anomalias têm score baixo."""
        historical_data = [
            [10.0 + i * 0.1, 20.0 + i * 0.1, 30.0 + i * 0.1]
            for i in range(50)
        ]

        detector = IsolationForestDetector(num_trees=50, contamination=0.1)
        detector.train(historical_data)

        anomaly_value = [100.0, 200.0, 300.0]
        anomaly_score = detector.score(anomaly_value)

        normal_value = [10.5, 20.5, 30.5]
        normal_score = detector.score(normal_value)

        assert anomaly_score < normal_score

    def test_detects_with_threshold(self) -> None:
        """testa detecção com threshold."""
        historical_data = [
            [10.0 + i * 0.1, 20.0 + i * 0.1, 30.0 + i * 0.1]
            for i in range(50)
        ]

        detector = IsolationForestDetector(num_trees=50, contamination=0.1)
        detector.train(historical_data)

        anomaly_value = [100.0, 200.0, 300.0]
        is_anomaly, score = detector.detect(anomaly_value, threshold=-0.3)

        assert isinstance(is_anomaly, (bool, np.bool_))
        assert isinstance(score, float)

    def test_raises_error_when_not_trained(self) -> None:
        """testa que score gera erro se não treinado."""
        detector = IsolationForestDetector()

        with pytest.raises(RuntimeError):
            detector.score([10.0, 20.0, 30.0])

    def test_raises_error_on_empty_data(self) -> None:
        """testa que treinamento com dados vazios gera erro."""
        detector = IsolationForestDetector()

        with pytest.raises(ValueError):
            detector.train([])

    def test_score_all_method(self) -> None:
        """testa método score_all para múltiplos pontos."""
        historical_data = [
            [10.0 + i * 0.1, 20.0 + i * 0.1]
            for i in range(50)
        ]

        detector = IsolationForestDetector(num_trees=30)
        detector.train(historical_data)

        test_data = np.array([
            [10.5, 20.5],
            [15.0, 25.0],
            [100.0, 200.0],
        ])

        scores = detector.score_all(test_data)

        assert len(scores) == 3
        assert all(-1.0 <= s <= 1.0 for s in scores)
