"""
planejador de remedies - sugere ações ao operador humano.
"""

from dataclasses import dataclass
from typing import Any

from src.models.diagnosis import RootCauseResult
from src.remediation.remedy_registry import Remedy, RemedyRegistry


@dataclass
class SuggestedRemedy:
    """representa um remedy sugerido ao operador."""
    
    remedy: Remedy
    confidence: float
    justification: str
    priority: int
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.remedy.name,
            "description": self.remedy.description,
            "implementation": self.remedy.implementation,
            "risk_level": self.remedy.risk_level,
            "success_rate": self.remedy.success_rate,
            "time_to_fix": self.remedy.time_to_fix,
            "confidence": self.confidence,
            "justification": self.justification,
            "priority": self.priority,
        }


class RemediationPlanner:
    """
    planejador de remedies - sugere melhores ações ao operador.
    
   working in suggestion mode only - não executa automaticamente,
    apenas recomenda ações ao operador humano.
    """
    
    def __init__(
        self,
        registry: RemedyRegistry | None = None
    ) -> None:
        self.registry = registry or RemedyRegistry()
    
    def suggest(
        self,
        diagnosis: RootCauseResult
    ) -> list[SuggestedRemedy]:
        """
        sugere remedies baseados no diagnóstico.
        
        Args:
            diagnosis: resultado do diagnóstico
            
        Returns:
            lista de remedies sugeridos, ordenada por prioridade
        """
        problem_type = diagnosis.possible_cause
        
        if diagnosis.requires_human_intervention:
            return []
        
        available_remedies = self.registry.get_remedies(problem_type)
        
        if not available_remedies:
            available_remedies = self._get_generic_remedies()
        
        suggestions = self._rank_remedies(
            available_remedies,
            diagnosis.confidence
        )
        
        return suggestions
    
    def _rank_remedies(
        self,
        remedies: list[Remedy],
        diagnosis_confidence: float
    ) -> list[SuggestedRemedy]:
        """
        ordena remedies por prioridade.
        
        utiliza fórmula: priority = success_rate * (1 - risk_level) * confidence
        """
        suggestions: list[SuggestedRemedy] = []
        
        for idx, remedy in enumerate(remedies):
            priority_score = remedy.success_rate * (1 - remedy.risk_level)
            confidence = min(diagnosis_confidence * remedy.success_rate, 0.85)
            
            justification = self._build_justification(
                remedy,
                diagnosis_confidence,
                priority_score
            )
            
            suggestion = SuggestedRemedy(
                remedy=remedy,
                confidence=round(confidence, 2),
                justification=justification,
                priority=idx + 1,
            )
            suggestions.append(suggestion)
        
        suggestions.sort(
            key=lambda s: s.remedy.success_rate * (1 - s.remedy.risk_level),
            reverse=True
        )
        
        for idx, suggestion in enumerate(suggestions):
            suggestion.priority = idx + 1
        
        return suggestions
    
    def _build_justification(
        self,
        remedy: Remedy,
        diagnosis_confidence: float,
        priority_score: float
    ) -> str:
        """constroi justificativa para o remedy."""
        confidence_pct = int(diagnosis_confidence * 100)
        risk_pct = int(remedy.risk_level * 100)
        
        justification = f"confiança de {confidence_pct}% no diagnóstico. "
        justification += f"este remedy tem {int(remedy.success_rate * 100)}% de taxa de sucesso "
        justification += f"e risco de {risk_pct}%. "
        
        if remedy.risk_level < 0.03:
            justification += "opção de baixo risco. "
        elif remedy.risk_level < 0.07:
            justification += "opção de risco moderado. "
        else:
            justification += "opção de risco mais elevado. "
        
        return justification
    
    def _get_generic_remedies(self) -> list[Remedy]:
        """retorna remedies genéricos quando específico não encontrado."""
        return [
            Remedy(
                problem_type="UnknownIssue",
                name="RestartPod",
                risk_level=0.05,
                time_to_fix=30.0,
                implementation="k8s.restart(pod)",
                success_rate=0.75,
                preconditions=["k8s_available"],
                description="reiniciar o pod como medida genérica",
            ),
            Remedy(
                problem_type="UnknownIssue",
                name="CollectLogs",
                risk_level=0.0,
                time_to_fix=0.0,
                implementation="manual: collect logs for analysis",
                success_rate=0.5,
                preconditions=[],
                description="coletar logs para análise manual",
            ),
        ]
    
    def get_suggestion_summary(
        self,
        suggestions: list[SuggestedRemedy]
    ) -> dict[str, Any]:
        """
        retorna resumo das sugestões.
        
        Args:
            suggestions: lista de sugestões
            
        Returns:
            dicionário com resumo
        """
        if not suggestions:
            return {
                "count": 0,
                "requires_human": True,
                "message": "nenhum remedy automático disponível",
            }
        
        return {
            "count": len(suggestions),
            "requires_human": False,
            "best_option": suggestions[0].to_dict(),
            "all_options": [s.to_dict() for s in suggestions],
            "message": f"{len(suggestions)} options available",
        }
