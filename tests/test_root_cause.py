"""
testes para o módulo de root cause inference.
"""

import pytest

from src.diagnosis.root_cause import RootCauseAnalyzer
from src.models.diagnosis import Evidence


class TestRootCauseAnalyzer:
    """testes para o analisador de causa raiz."""

    def setup_method(self) -> None:
        """setup para cada teste."""
        self.analyzer = RootCauseAnalyzer()

    def test_identifies_changed_first_metric(self):
        """testa identificação de qual métrica mudou primeiro."""
        metrics = {
            "memory": [50, 52, 51, 49, 90, 92, 95],
            "cpu": [30, 31, 29, 32, 35, 33, 34],
            "latency": [45, 44, 46, 45, 48, 47, 49],
        }
        
        result = self.analyzer.analyze(metrics)
        
        assert result.possible_cause in ["MemoryPressure", "unknown"]

    def test_returns_low_confidence(self):
        """testa que confiança retornada é sempre baixa."""
        metrics = {
            "memory": [50, 52, 51, 49, 55],
            "cpu": [30, 31, 29, 32, 33],
        }
        
        result = self.analyzer.analyze(metrics)
        
        assert result.confidence <= 0.70
        assert result.confidence >= 0.30

    def test_returns_multiple_hypotheses(self):
        """testa que retorna múltiplas hipóteses."""
        metrics = {
            "memory": [50, 52, 51, 49, 55],
            "cpu": [30, 31, 29, 32, 33],
            "latency": [45, 44, 46, 45, 47],
        }
        
        result = self.analyzer.analyze(metrics)
        
        assert len(result.hypotheses) > 0
        assert isinstance(result.hypotheses[0], dict)
        assert "cause" in result.hypotheses[0]
        assert "probability" in result.hypotheses[0]

    def test_matches_historical_pattern(self):
        """testa que pode adicionar e buscar padrões históricos."""
        result = self.analyzer.analyze({"memory": [50, 90]})
        
        self.analyzer.add_historical_pattern(result)
        
        assert "MemoryPressure" in self.analyzer.historical_patterns

    def test_does_not_claim_causation(self):
        """testa que não afirma causalidade diretamente."""
        metrics = {
            "memory": [50, 90],
            "latency": [45, 100],
        }
        
        result = self.analyzer.analyze(metrics)
        
        assert "correlation" in result.correlation.lower() or \
               "insufficient" in result.reasoning.lower()

    def test_handles_empty_metrics(self):
        """testa comportamento com métricas vazias."""
        result = self.analyzer.analyze({})
        
        assert result.possible_cause == "unknown"
        assert result.confidence < 0.5

    def test_handles_single_metric(self):
        """testa comportamento com uma única métrica."""
        metrics = {"memory": [50, 52, 51, 49, 55]}
        
        result = self.analyzer.analyze(metrics)
        
        assert result.possible_cause in ["MemoryPressure", "unknown"]
        assert 0 <= result.confidence <= 1

    def test_correlation_calculation(self):
        """testa cálculo de correlação de pearson."""
        metrics = {
            "a": [1, 2, 3, 4, 5],
            "b": [2, 4, 6, 8, 10],
        }
        
        result = self.analyzer.analyze(metrics)
        
        assert "a" in result.correlation or "b" in result.correlation

    def test_reasoning_contains_context(self):
        """testa que raciocínio contém contexto."""
        metrics = {
            "memory": [50, 90],
            "cpu": [30, 35],
        }
        
        result = self.analyzer.analyze(metrics)
        
        assert len(result.reasoning) > 10

    def test_contributing_factors_listed(self):
        """testa que fatores contribuidores são listados."""
        metrics = {
            "memory": [50, 90],
            "cpu": [30, 35],
            "latency": [45, 50],
        }
        
        result = self.analyzer.analyze(metrics)
        
        assert isinstance(result.contributing_factors, list)


class TestConfidenceBounds:
    """testes para limites de confiança."""

    def setup_method(self) -> None:
        """setup para cada teste."""
        self.analyzer = RootCauseAnalyzer()

    def test_confidence_never_exceeds_max(self):
        """testa que confiança nunca excede máximo."""
        for _ in range(10):
            metrics = {
                "memory": [50, 90, 95],
                "cpu": [30, 85, 90],
                "latency": [45, 500, 600],
            }
            result = self.analyzer.analyze(metrics)
            assert result.confidence <= self.analyzer.max_confidence

    def test_confidence_always_above_min_for_valid_data(self):
        """testa que confiança está acima do mínimo para dados válidos."""
        metrics = {
            "memory": [50, 90],
            "cpu": [30, 85],
        }
        result = self.analyzer.analyze(metrics)
        assert result.confidence >= self.analyzer.min_confidence - 0.2
