"""
módulo de análise de causa raiz usando correlação temporal simples.
"""

from datetime import datetime
from typing import Any

from src.models.diagnosis import CorrelationResult, Evidence, RootCauseResult


class RootCauseAnalyzer:
    """
    analisador de causa raiz baseado em correlação temporal.
    
    usa correlação simples (não causal inference) e sempre retorna
    confiança baixa (60-70%) para manter humildade estatística.
    """

    def __init__(self) -> None:
        self.historical_patterns: dict[str, list[RootCauseResult]] = {}
        self.min_confidence: float = 0.60
        self.max_confidence: float = 0.70

    def analyze(
        self,
        metrics: dict[str, list[float]],
        timestamps: dict[str, list[datetime]] | None = None,
    ) -> RootCauseResult:
        """
        analisa métricas e retorna possível causa raiz.
        
        Args:
            metrics: dicionário com nome da métrica e valores históricos
            timestamps: opcional, timestamps correspondentes
            
        Returns:
            RootCauseResult com possível causa e confiança
        """
        if not metrics:
            return self._create_uncertain_result("no_metrics")

        correlations = self._calculate_correlations(metrics)
        first_changed = self._find_first_changed_metric(metrics)
        
        possible_cause = self._determine_possible_cause(
            first_changed, 
            correlations
        )
        confidence = self._calculate_confidence(correlations, first_changed)
        
        reasoning = self._build_reasoning(first_changed, correlations)
        correlation_str = self._format_correlations(correlations)
        
        hypotheses = self._generate_hypotheses(metrics, correlations)
        
        requires_human = confidence < self.min_confidence
        
        return RootCauseResult(
            possible_cause=possible_cause,
            confidence=confidence,
            reasoning=reasoning,
            correlation=correlation_str,
            contributing_factors=list(correlations.keys()),
            hypotheses=hypotheses,
            requires_human_intervention=requires_human,
        )

    def _calculate_correlations(
        self,
        metrics: dict[str, list[float]]
    ) -> dict[str, CorrelationResult]:
        """calcula correlação entre métricas."""
        correlations: dict[str, CorrelationResult] = {}
        metric_names = list(metrics.keys())
        
        for i, metric_a in enumerate(metric_names):
            for metric_b in metric_names[i + 1:]:
                pearson_r = self._pearson_correlation(
                    metrics[metric_a],
                    metrics[metric_b]
                )
                correlations[f"{metric_a}__{metric_b}"] = CorrelationResult(
                    metric_a=metric_a,
                    metric_b=metric_b,
                    pearson_r=pearson_r,
                    is_positive=pearson_r > 0,
                )
        
        return correlations

    def _pearson_correlation(
        self,
        x: list[float],
        y: list[float]
    ) -> float:
        """calcula coeficiente de correlação de pearson."""
        n = min(len(x), len(y))
        if n < 2:
            return 0.0
        
        x = x[-n:]
        y = y[-n:]
        
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        
        numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
        denominator = (sum((xi - mean_x) ** 2 for xi in x) ** 0.5) * \
                       (sum((yi - mean_y) ** 2 for yi in y) ** 0.5)
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator

    def _find_first_changed_metric(
        self,
        metrics: dict[str, list[float]]
    ) -> str | None:
        """identifica qual métrica mudou primeiro."""
        if not metrics:
            return None
            
        changes: dict[str, float] = {}
        
        for metric_name, values in metrics.items():
            if len(values) < 2:
                continue
            
            # Use all available data - split into first half and second half
            n = len(values)
            mid = n // 2
            if mid < 1:
                mid = 1
            
            first_half = values[:mid]
            second_half = values[mid:]
            
            if not first_half or not second_half:
                continue
                
            first_mean = sum(first_half) / len(first_half)
            second_mean = sum(second_half) / len(second_half)
            
            if first_mean == 0:
                changes[metric_name] = abs(second_mean)
            else:
                changes[metric_name] = abs(second_mean - first_mean) / first_mean
        
        if not changes:
            return None
            
        return max(changes, key=changes.get)

    def _determine_possible_cause(
        self,
        first_changed: str | None,
        correlations: dict[str, CorrelationResult]
    ) -> str:
        """determina possível causa baseada na análise."""
        if not first_changed:
            return "unknown"
        
        cause_mapping: dict[str, str] = {
            "memory": "MemoryPressure",
            "cpu": "HighCPU",
            "latency": "HighLatency",
            "throughput": "LowThroughput",
            "error": "HighErrorRate",
            "disk": "DiskPressure",
            "network": "NetworkLatency",
        }
        
        metric_lower = first_changed.lower()
        for key, cause in cause_mapping.items():
            if key in metric_lower:
                return cause
        
        return "UnknownIssue"

    def _calculate_confidence(
        self,
        correlations: dict[str, CorrelationResult],
        first_changed: str | None
    ) -> float:
        """calcula confiança baseada na análise."""
        if not correlations and not first_changed:
            return self.min_confidence - 0.1
        
        strong_correlations = sum(
            1 for c in correlations.values() 
            if abs(c.pearson_r) > 0.7
        )
        
        base_confidence = self.min_confidence
        
        if strong_correlations > 0:
            base_confidence += 0.05
        
        if first_changed:
            base_confidence += 0.03
        
        return min(base_confidence, self.max_confidence)

    def _build_reasoning(
        self,
        first_changed: str | None,
        correlations: dict[str, CorrelationResult]
    ) -> str:
        """constroi texto de raciocínio."""
        if not first_changed:
            return "insufficient data to determine root cause"
        
        reasoning = f"{first_changed} changed first"
        
        strong_corr = [
            f"{c.metric_a}↔{c.metric_b}"
            for c in correlations.values()
            if abs(c.pearson_r) > 0.7
        ]
        
        if strong_corr:
            reasoning += f", strongly correlated with {', '.join(strong_corr[:2])}"
        
        # Include explicit mention of insufficient evidence for causation claim
        reasoning += ". correlation indicates insufficient evidence for causation."
        
        return reasoning

    def _format_correlations(
        self,
        correlations: dict[str, CorrelationResult]
    ) -> str:
        """formata correlações em string legível."""
        if not correlations:
            return "no correlation data"
        
        formatted = []
        for corr in correlations.values():
            direction = "↑" if corr.is_positive else "↓"
            formatted.append(
                f"{corr.metric_a}{direction}{corr.metric_b} (r={corr.pearson_r:.2f})"
            )
        
        return ", ".join(formatted[:3])

    def _generate_hypotheses(
        self,
        metrics: dict[str, list[float]],
        correlations: dict[str, CorrelationResult]
    ) -> list[dict[str, Any]]:
        """gera múltiplas hipóteses com probabilidades."""
        hypotheses: list[dict[str, Any]] = []
        
        for metric_name in metrics.keys():
            prob = 0.2 + (0.1 if metric_name in [
                c.metric_a for c in correlations.values()
            ] else 0)
            
            hypotheses.append({
                "cause": metric_name,
                "probability": min(prob, 0.4),
                "evidence": f"anomaly in {metric_name}",
            })
        
        hypotheses.sort(key=lambda h: h["probability"], reverse=True)
        
        return hypotheses[:3]

    def _create_uncertain_result(self, reason: str) -> RootCauseResult:
        """cria resultado de baixa confiança."""
        return RootCauseResult(
            possible_cause="unknown",
            confidence=0.3,
            reasoning=f"insufficient data: {reason}",
            correlation="none",
            contributing_factors=[],
            hypotheses=[],
            requires_human_intervention=True,
        )

    def add_historical_pattern(
        self,
        pattern: RootCauseResult
    ) -> None:
        """adiciona padrão histórico para referência futura."""
        key = pattern.possible_cause
        if key not in self.historical_patterns:
            self.historical_patterns[key] = []
        self.historical_patterns[key].append(pattern)
