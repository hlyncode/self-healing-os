"""
testes para o modelo de baseline learning.
"""

import numpy as np
import pytest

from src.detection.baseline import BaselineModel


class TestBaselineModel:
    """testes para a classe BaselineModel."""

    @pytest.fixture
    def baseline_model(self) -> BaselineModel:
        """cria uma instância do modelo de baseline."""
        return BaselineModel(window_size=100)

    def test_initialization(self, baseline_model: BaselineModel) -> None:
        """testa inicialização do modelo."""
        assert baseline_model.window_size == 100
        assert baseline_model.learning_rate > 0
        assert baseline_model._history == {}

    def test_update_single_value(self, baseline_model: BaselineModel) -> None:
        """testa atualização com um único valor."""
        baseline_model.update("cpu_usage", 50.0)

        assert "cpu_usage" in baseline_model._history
        assert len(baseline_model._history["cpu_usage"]) == 1
        assert baseline_model._history["cpu_usage"][0] == 50.0

    def test_statistics_after_updates(self, baseline_model: BaselineModel) -> None:
        """testa cálculo de estatísticas após múltiplas atualizações."""
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        for value in values:
            baseline_model.update("cpu_usage", value)

        stats = baseline_model.get_statistics("cpu_usage")

        assert stats["mean"] == pytest.approx(30.0, rel=0.01)
        assert stats["sample_count"] == 5
        assert stats["std"] > 0

    def test_anomaly_score_normal_value(self, baseline_model: BaselineModel) -> None:
        """testa score para valor próximo à média."""
        for _ in range(50):
            baseline_model.update("cpu_usage", 50.0)
        
        score = baseline_model.get_anomaly_score("cpu_usage", 51.0)
        # valores muito próximos não devem ter score muito alto
        assert score < 10.0

    def test_anomaly_score_outlier(self, baseline_model: BaselineModel) -> None:
        """testa score de anomalia para outlier."""
        for _ in range(50):
            baseline_model.update("cpu_usage", 50.0)

        score = baseline_model.get_anomaly_score("cpu_usage", 100.0)

        assert score > 3.0

    def test_is_anomaly_detection(self, baseline_model: BaselineModel) -> None:
        """testa detecção de anomalia com threshold."""
        for _ in range(50):
            baseline_model.update("cpu_usage", 50.0)
        
        # threshold 3.0 detecta outliers claros
        is_anomaly = baseline_model.is_anomaly("cpu_usage", 100.0, threshold=3.0)
        assert is_anomaly is True

    def test_expected_value(self, baseline_model: BaselineModel) -> None:
        """testa retorno de valor esperado."""
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        for value in values:
            baseline_model.update("cpu_usage", value)

        expected = baseline_model.get_expected_value("cpu_usage")

        assert expected == pytest.approx(30.0, rel=0.1)

    def test_window_size_limit(self, baseline_model: BaselineModel) -> None:
        """testa limite de janela de valores."""
        window = baseline_model.window_size

        for i in range(window + 50):
            baseline_model.update("cpu_usage", float(i))

        assert len(baseline_model._history["cpu_usage"]) == window

    def test_multiple_metrics(self, baseline_model: BaselineModel) -> None:
        """testa uso com múltiplas métricas."""
        baseline_model.update("cpu_usage", 50.0)
        baseline_model.update("memory_usage", 70.0)
        baseline_model.update("cpu_usage", 60.0)

        assert len(baseline_model._history["cpu_usage"]) == 2
        assert len(baseline_model._history["memory_usage"]) == 1

    def test_reset_single_metric(self, baseline_model: BaselineModel) -> None:
        """testa reset de uma métrica específica."""
        baseline_model.update("cpu_usage", 50.0)
        baseline_model.update("cpu_usage", 60.0)

        baseline_model.reset("cpu_usage")

        assert "cpu_usage" not in baseline_model._history
        assert baseline_model._means.get("cpu_usage") is None

    def test_reset_all_metrics(self, baseline_model: BaselineModel) -> None:
        """testa reset de todas as métricas."""
        baseline_model.update("cpu_usage", 50.0)
        baseline_model.update("memory_usage", 70.0)

        baseline_model.reset()

        assert baseline_model._history == {}
        assert baseline_model._means == {}

    def test_empty_metric_statistics(self, baseline_model: BaselineModel) -> None:
        """testa estatísticas para métrica inexistente."""
        stats = baseline_model.get_statistics("unknown_metric")

        assert stats["mean"] == 0.0
        assert stats["std"] == 0.0
        assert stats["sample_count"] == 0

    def test_seasonal_pattern_detection(self, baseline_model: BaselineModel) -> None:
        """testa detecção de padrão sazonal."""
        base_value = 50.0
        period = 24

        for i in range(period * 2):
            value = base_value + np.sin(2 * np.pi * i / period) * 10
            baseline_model.update("cpu_usage", value)

        has_pattern = baseline_model.get_statistics("cpu_usage")["has_seasonal_pattern"]

        assert has_pattern is True

    def test_anomaly_score_zero_std(self, baseline_model: BaselineModel) -> None:
        """testa score com desvio padrão zero."""
        baseline_model.update("cpu_usage", 50.0)

        score = baseline_model.get_anomaly_score("cpu_usage", 50.0)

        assert score == 0.0
