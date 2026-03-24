"""
motor de aprendizado do sistema self-healing.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.models.diagnosis import RootCauseResult
from src.remediation.remedy_registry import Remedy


@dataclass
class Incident:
    """representa um incidente registrado no sistema."""
    
    id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    problem_type: str = ""
    diagnosis: RootCauseResult | None = None
    remedies_tried: list[Remedy] = field(default_factory=list)
    remedies_successful: list[Remedy] = field(default_factory=list)
    time_to_resolution: float = 0.0
    resolved: bool = False
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "problem_type": self.problem_type,
            "diagnosis": self.diagnosis.to_dict() if self.diagnosis else None,
            "remedies_tried": [r.name for r in self.remedies_tried],
            "remedies_successful": [r.name for r in self.remedies_successful],
            "time_to_resolution": self.time_to_resolution,
            "resolved": self.resolved,
        }


class LearningEngine:
    """
    motor de aprendizado que melhora continuamente.
    
    registra incidentes, atualiza base de conhecimento,
    e adapta thresholds baseado em feedback.
    """
    
    def __init__(self) -> None:
        self.incidents: list[Incident] = []
        self.incident_counter: int = 0
        self.success_history: dict[str, list[bool]] = {}
        self.threshold_adjustments: dict[str, float] = {}
    
    def record_incident(
        self,
        problem_type: str,
        diagnosis: RootCauseResult,
        remedies_tried: list[Remedy],
        remedies_successful: list[Remedy],
        time_to_resolution: float,
    ) -> Incident:
        """
        registra um incidente para aprendizado.
        
        Args:
            problem_type: tipo do problema
            diagnosis: diagnóstico realizado
            remedies_tried: remedies tentados
            remedies_successful: remedies que funcionaram
            time_to_resolution: tempo para resolução
            
        Returns:
            incidente registrado
        """
        self.incident_counter += 1
        incident = Incident(
            id=f"incident_{self.incident_counter}",
            problem_type=problem_type,
            diagnosis=diagnosis,
            remedies_tried=remedies_tried,
            remedies_successful=remedies_successful,
            time_to_resolution=time_to_resolution,
            resolved=True,
        )
        
        self.incidents.append(incident)
        
        self._update_success_history(problem_type, remedies_tried, remedies_successful)
        
        return incident
    
    def _update_success_history(
        self,
        problem_type: str,
        remedies_tried: list[Remedy],
        remedies_successful: list[Remedy]
    ) -> None:
        """atualiza histórico de sucesso."""
        for remedy in remedies_tried:
            key = f"{problem_type}:{remedy.name}"
            
            if key not in self.success_history:
                self.success_history[key] = []
            
            success = remedy in remedies_successful
            self.success_history[key].append(success)
            
            if len(self.success_history[key]) > 100:
                self.success_history[key] = self.success_history[key][-100:]
    
    def get_remedy_success_rate(
        self,
        problem_type: str,
        remedy_name: str
    ) -> float:
        """
        obtém taxa de sucesso de um remedy.
        
        Args:
            problem_type: tipo do problema
            remedy_name: nome do remedy
            
        Returns:
            taxa de sucesso (0 a 1)
        """
        key = f"{problem_type}:{remedy_name}"
        
        if key not in self.success_history:
            return 0.5
        
        history = self.success_history[key]
        
        if not history:
            return 0.5
        
        return sum(history) / len(history)
    
    def get_best_remedy_order(
        self,
        problem_type: str,
        available_remedies: list[Remedy]
    ) -> list[Remedy]:
        """
        retorna remedies ordenados por taxa de sucesso.
        
        Args:
            problem_type: tipo do problema
            available_remedies: remedies disponíveis
            
        Returns:
            lista ordenada de remedies
        """
        scored_remedies = []
        
        for remedy in available_remedies:
            success_rate = self.get_remedy_success_rate(
                problem_type,
                remedy.name
            )
            scored_remedies.append((remedy, success_rate))
        
        scored_remedies.sort(key=lambda x: x[1], reverse=True)
        
        return [remedy for remedy, _ in scored_remedies]
    
    def record_false_positive(
        self,
        metric_name: str
    ) -> None:
        """
        registra falso positivo para ajustar threshold.
        
        Args:
            metric_name: nome da métrica
        """
        if metric_name not in self.threshold_adjustments:
            self.threshold_adjustments[metric_name] = 0.0
        
        self.threshold_adjustments[metric_name] += 0.05
    
    def record_false_negative(
        self,
        metric_name: str
    ) -> None:
        """
        registra falso negativo para ajustar threshold.
        
        Args:
            metric_name: nome da métrica
        """
        if metric_name not in self.threshold_adjustments:
            self.threshold_adjustments[metric_name] = 0.0
        
        self.threshold_adjustments[metric_name] -= 0.05
    
    def get_threshold_adjustment(
        self,
        metric_name: str
    ) -> float:
        """
        obtém ajuste de threshold para uma métrica.
        
        Args:
            metric_name: nome da métrica
            
        Returns:
            ajuste a ser aplicado ao threshold
        """
        return self.threshold_adjustments.get(metric_name, 0.0)
    
    def get_statistics(self) -> dict[str, Any]:
        """
        obtém estatísticas de aprendizado.
        
        Returns:
            dicionário com estatísticas
        """
        return {
            "total_incidents": len(self.incidents),
            "problem_types": list(set(i.problem_type for i in self.incidents)),
            "remedy_history_keys": list(self.success_history.keys()),
            "threshold_adjustments": self.threshold_adjustments,
            "average_resolution_time": self._calculate_average_resolution_time(),
        }
    
    def _calculate_average_resolution_time(self) -> float:
        """calcula tempo médio de resolução."""
        if not self.incidents:
            return 0.0
        
        resolved_incidents = [i for i in self.incidents if i.resolved]
        
        if not resolved_incidents:
            return 0.0
        
        total_time = sum(i.time_to_resolution for i in resolved_incidents)
        
        return total_time / len(resolved_incidents)
