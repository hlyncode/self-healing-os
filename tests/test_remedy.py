"""
testes para o módulo de remediação.
"""

import pytest

from src.models.diagnosis import RootCauseResult
from src.remediation.planner import RemediationPlanner
from src.remediation.remedy_registry import Remedy, RemedyRegistry


class TestRemedyRegistry:
    """testes para o registry de remedies."""
    
    def setup_method(self) -> None:
        """setup para cada teste."""
        self.registry = RemedyRegistry()
    
    def test_initializes_with_default_remedies(self):
        """testa que registry é inicializado com remedies padrão."""
        problem_types = self.registry.get_all_problem_types()
        
        assert len(problem_types) > 0
        assert "MemoryPressure" in problem_types
        assert "HighLatency" in problem_types
    
    def test_get_remedies_returns_list(self):
        """testa que get_remedies retorna lista."""
        remedies = self.registry.get_remedies("MemoryPressure")
        
        assert isinstance(remedies, list)
        assert len(remedies) > 0
    
    def test_get_remedies_for_unknown_problem(self):
        """testa comportamento para problema desconhecido."""
        remedies = self.registry.get_remedies("UnknownProblem")
        
        assert remedies == []
    
    def test_add_remedy(self):
        """testa adição de novo remedy."""
        new_remedy = Remedy(
            problem_type="CustomIssue",
            name="CustomFix",
            risk_level=0.02,
            time_to_fix=10.0,
            implementation="custom.action()",
            success_rate=0.80,
        )
        
        self.registry.add_remedy(new_remedy)
        
        remedies = self.registry.get_remedies("CustomIssue")
        
        assert len(remedies) == 1
        assert remedies[0].name == "CustomFix"
    
    def test_update_success_rate_increases(self):
        """testa que sucesso aumenta success_rate."""
        remedy = self.registry.get_remedies("MemoryPressure")[0]
        original_rate = remedy.success_rate
        
        self.registry.update_success_rate("MemoryPressure", remedy.name, True)
        
        assert remedy.success_rate >= original_rate
    
    def test_update_success_rate_decreases(self):
        """testa que falha diminui success_rate."""
        remedy = self.registry.get_remedies("MemoryPressure")[0]
        original_rate = remedy.success_rate
        
        self.registry.update_success_rate("MemoryPressure", remedy.name, False)
        
        assert remedy.success_rate <= original_rate


class TestRemediationPlanner:
    """testes para o planejador de remedies."""
    
    def setup_method(self) -> None:
        """setup para cada teste."""
        self.registry = RemedyRegistry()
        self.planner = RemediationPlanner(self.registry)
    
    def test_suggests_remedies_for_known_problem(self):
        """testa sugestão para problema conhecido."""
        diagnosis = RootCauseResult(
            possible_cause="MemoryPressure",
            confidence=0.65,
            reasoning="memory increased significantly",
            correlation="memory↑ → latency↑",
            requires_human_intervention=False,
        )
        
        suggestions = self.planner.suggest(diagnosis)
        
        assert len(suggestions) > 0
        assert suggestions[0].remedy.problem_type == "MemoryPressure"
    
    def test_suggests_lowest_risk_remedy_first(self):
        """testa que remedy de menor risco é sugerido primeiro."""
        diagnosis = RootCauseResult(
            possible_cause="MemoryPressure",
            confidence=0.65,
            reasoning="memory increased",
            correlation="memory↑",
            requires_human_intervention=False,
        )
        
        suggestions = self.planner.suggest(diagnosis)
        
        if len(suggestions) > 1:
            assert suggestions[0].remedy.risk_level <= suggestions[1].remedy.risk_level
    
    def test_returns_multiple_suggestions_ordered(self):
        """testa que retorna múltiplas sugestões ordenadas."""
        diagnosis = RootCauseResult(
            possible_cause="HighLatency",
            confidence=0.65,
            reasoning="latency spike detected",
            correlation="latency correlated with cpu",
            requires_human_intervention=False,
        )
        
        suggestions = self.planner.suggest(diagnosis)
        
        assert len(suggestions) > 1
        assert all(hasattr(s, 'priority') for s in suggestions)
    
    def test_includes_confidence_and_justification(self):
        """testa que sugestão inclui confiança e justificativa."""
        diagnosis = RootCauseResult(
            possible_cause="MemoryPressure",
            confidence=0.65,
            reasoning="memory increased",
            correlation="memory↑",
            requires_human_intervention=False,
        )
        
        suggestions = self.planner.suggest(diagnosis)
        
        assert suggestions[0].confidence > 0
        assert len(suggestions[0].justification) > 0
    
    def test_handles_no_remedy_available(self):
        """testa comportamento quando nenhum remedy disponível."""
        diagnosis = RootCauseResult(
            possible_cause="UnknownIssue",
            confidence=0.30,
            reasoning="unknown problem",
            correlation="none",
            requires_human_intervention=True,
        )
        
        suggestions = self.planner.suggest(diagnosis)
        
        assert suggestions == []
    
    def test_get_suggestion_summary(self):
        """testa geração de resumo das sugestões."""
        diagnosis = RootCauseResult(
            possible_cause="MemoryPressure",
            confidence=0.65,
            reasoning="memory increased",
            correlation="memory↑",
            requires_human_intervention=False,
        )
        
        suggestions = self.planner.suggest(diagnosis)
        summary = self.planner.get_suggestion_summary(suggestions)
        
        assert "count" in summary
        assert "requires_human" in summary
    
    def test_suggestion_contains_implementation(self):
        """testa que sugestão contém implementação."""
        diagnosis = RootCauseResult(
            possible_cause="MemoryPressure",
            confidence=0.65,
            reasoning="memory increased",
            correlation="memory↑",
            requires_human_intervention=False,
        )
        
        suggestions = self.planner.suggest(diagnosis)
        
        assert len(suggestions[0].remedy.implementation) > 0
