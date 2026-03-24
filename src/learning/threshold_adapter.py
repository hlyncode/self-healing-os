"""
adaptador dinâmico de thresholds.
"""

from typing import Any


class ThresholdAdapter:
    """
    adapta thresholds dinamicamente baseado em feedback.
    
    se muitos falsos positivos: aumentar threshold (menos sensível)
    se muitos falsos negativos: diminuir threshold (mais sensível)
    """
    
    def __init__(
        self,
        default_thresholds: dict[str, float],
        min_threshold: float = 0.5,
        max_threshold: float = 5.0,
    ) -> None:
        self.default_thresholds = default_thresholds
        self.current_thresholds = default_thresholds.copy()
        self.min_threshold = min_threshold
        self.max_threshold = max_threshold
        self.false_positive_counts: dict[str, int] = {}
        self.false_negative_counts: dict[str, int] = {}
    
    def adjust_threshold(
        self,
        metric_name: str,
        is_false_positive: bool
    ) -> float:
        """
        ajusta threshold baseado em feedback.
        
        Args:
            metric_name: nome da métrica
            is_false_positive: true se foi falso positivo
            
        Returns:
            novo threshold
        """
        if metric_name not in self.current_thresholds:
            default = self.default_thresholds.get(metric_name, 3.0)
            self.current_thresholds[metric_name] = default
        
        if metric_name not in self.false_positive_counts:
            self.false_positive_counts[metric_name] = 0
        if metric_name not in self.false_negative_counts:
            self.false_negative_counts[metric_name] = 0
        
        current = self.current_thresholds[metric_name]
        
        adjustment = 0.1
        
        if is_false_positive:
            self.false_positive_counts[metric_name] += 1
            new_threshold = current + adjustment
        else:
            self.false_negative_counts[metric_name] += 1
            new_threshold = current - adjustment
        
        new_threshold = max(
            self.min_threshold,
            min(new_threshold, self.max_threshold)
        )
        
        self.current_thresholds[metric_name] = new_threshold
        
        return new_threshold
    
    def get_threshold(self, metric_name: str) -> float:
        """
        obtém threshold atual para uma métrica.
        
        Args:
            metric_name: nome da métrica
            
        Returns:
            threshold atual
        """
        return self.current_thresholds.get(
            metric_name,
            self.default_thresholds.get(metric_name, 3.0)
        )
    
    def reset_threshold(self, metric_name: str) -> float:
        """
        reseta threshold para valor padrão.
        
        Args:
            metric_name: nome da métrica
            
        Returns:
            threshold resetado
        """
        default = self.default_thresholds.get(metric_name, 3.0)
        self.current_thresholds[metric_name] = default
        self.false_positive_counts[metric_name] = 0
        self.false_negative_counts[metric_name] = 0
        
        return default
    
    def get_statistics(self) -> dict[str, Any]:
        """
        obtém estatísticas de adaptação.
        
        Returns:
            dicionário com estatísticas
        """
        return {
            "current_thresholds": self.current_thresholds,
            "false_positive_counts": self.false_positive_counts,
            "false_negative_counts": self.false_negative_counts,
        }
    
    def calculate_sensitivity(
        self,
        metric_name: str
    ) -> str:
        """
        calcula sensibilidade atual do threshold.
        
        Args:
            metric_name: nome da métrica
            
        Returns:
            nível de sensibilidade
        """
        current = self.get_threshold(metric_name)
        default = self.default_thresholds.get(metric_name, 3.0)
        
        ratio = current / default if default > 0 else 1.0
        
        if ratio > 1.3:
            return "low"
        elif ratio > 0.7:
            return "normal"
        else:
            return "high"
