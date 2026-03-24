"""prediction engine para forecasting."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any


@dataclass
class Prediction:
    """resultado de uma predição."""
    
    metric_name: str
    hours_ahead: int
    predicted_value: float
    confidence: float
    trend: str
    recommendation: str
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "hours_ahead": self.hours_ahead,
            "predicted_value": round(self.predicted_value, 2),
            "confidence": round(self.confidence, 2),
            "trend": self.trend,
            "recommendation": self.recommendation,
        }


class CapacityPredictor:
    """preditor de capacidade e forecasting."""
    
    def __init__(self) -> None:
        self.thresholds: dict[str, float] = {
            "memory": 85.0,
            "cpu": 80.0,
            "disk": 90.0,
        }
    
    def predict_exhaustion(
        self,
        metric_name: str,
        historical_values: list[float],
        hours_ahead: int = 8,
    ) -> Prediction:
        """prevê quando um recurso vai se esgotar."""
        
        if len(historical_values) < 3:
            return Prediction(
                metric_name=metric_name,
                hours_ahead=hours_ahead,
                predicted_value=0.0,
                confidence=0.0,
                trend="unknown",
                recommendation="insufficient data",
            )
        
        recent = historical_values[-10:]
        growth_rate = self._calculate_growth_rate(recent)
        predicted = recent[-1] + (growth_rate * hours_ahead)
        
        threshold = self.thresholds.get(metric_name, 80.0)
        hours_until_exhaustion = (threshold - recent[-1]) / growth_rate if growth_rate > 0 else float('inf')
        
        trend = "increasing" if growth_rate > 0.1 else "stable" if growth_rate > -0.1 else "decreasing"
        
        confidence = min(0.7, len(recent) / 20.0)
        
        if hours_until_exhaustion < hours_ahead:
            recommendation = f"atenção: {metric_name} pode atingir limite em {hours_until_exhaustion:.1f}h"
        elif trend == "increasing":
            recommendation = f"monitorar {metric_name}: tendência de crescimento"
        else:
            recommendation = f"{metric_name} dentro dos padrões"
        
        return Prediction(
            metric_name=metric_name,
            hours_ahead=hours_ahead,
            predicted_value=predicted,
            confidence=confidence,
            trend=trend,
            recommendation=recommendation,
        )
    
    def _calculate_growth_rate(self, values: list[float]) -> float:
        """calcula taxa de crescimento."""
        if len(values) < 2:
            return 0.0
        
        n = len(values)
        x = list(range(n))
        
        sum_x = sum(x)
        sum_y = sum(values)
        sum_xy = sum(x[i] * values[i] for i in range(n))
        sum_x2 = sum(xi * xi for xi in x)
        
        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            return 0.0
        
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        
        avg = sum(values) / n
        return slope / avg if avg > 0 else 0.0
    
    def detect_seasonal_pattern(
        self,
        values: list[float],
        expected_peak_hour: int,
        current_hour: int,
    ) -> str:
        """detecta padrão sazonal."""
        
        if len(values) < 24:
            return "insufficient_data"
        
        recent_daily = values[-24:]
        peak_value = max(recent_daily)
        current_value = recent_daily[current_hour % 24]
        
        if current_value > peak_value * 0.8:
            return "peak_time"
        
        if abs(current_hour - expected_peak_hour) < 3:
            return "approaching_peak"
        
        return "normal"
    
    def forecast_batch(
        self,
        metrics: dict[str, list[float]],
        hours_ahead: int = 8,
    ) -> dict[str, Prediction]:
        """faz predição para múltiplas métricas."""
        
        predictions = {}
        
        for metric_name, values in metrics.items():
            predictions[metric_name] = self.predict_exhaustion(
                metric_name,
                values,
                hours_ahead,
            )
        
        return predictions