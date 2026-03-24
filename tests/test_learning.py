"""
testes para o módulo de aprendizado.
"""

import pytest
from datetime import datetime

from src.learning.engine import Incident, LearningEngine
from src.learning.threshold_adapter import ThresholdAdapter
from src.models.diagnosis import RootCauseResult
from src.remediation.remedy_registry import Remedy


class TestLearningEngine:
    """testes para o motor de aprendizado."""
    
    def setup_method(self) -> None:
        """setup para cada teste."""
        self.engine = LearningEngine()
    
    def test_records_incident(self):
        """testa registro de incidente."""
        diagnosis = RootCauseResult(
            possible_cause="MemoryPressure",
            confidence=0.65,
            reasoning="memory increased",
            correlation="memory↑",
        )
        
        remedy = Remedy(
            problem_type="MemoryPressure",
            name="RestartPod",
            risk_level=0.05,
            time_to_fix=30.0,
            implementation="k8s.restart()",
            success_rate=0.95,
        )
        
        incident = self.engine.record_incident(
            problem_type="MemoryPressure",
            diagnosis=diagnosis,
            remedies_tried=[remedy],
            remedies_successful=[remedy],
            time_to_resolution=45.0,
        )
        
        assert incident.id == "incident_1"
        assert incident.problem_type == "MemoryPressure"
        assert incident.resolved is True
    
    def test_increases_success_rate_of_effective_remedies(self):
        """testa que taxa de sucesso aumenta para remedies eficazes."""
        remedy = Remedy(
            problem_type="MemoryPressure",
            name="RestartPod",
            risk_level=0.05,
            time_to_fix=30.0,
            implementation="k8s.restart()",
            success_rate=0.5,
        )
        
        self.engine.record_incident(
            problem_type="MemoryPressure",
            diagnosis=RootCauseResult(
                possible_cause="MemoryPressure",
                confidence=0.65,
                reasoning="test",
                correlation="test",
            ),
            remedies_tried=[remedy],
            remedies_successful=[remedy],
            time_to_resolution=30.0,
        )
        
        success_rate = self.engine.get_remedy_success_rate(
            "MemoryPressure",
            "RestartPod"
        )
        
        assert success_rate > 0.5
    
    def test_decreases_success_rate_of_failed_remedies(self):
        """testa que taxa de sucesso diminui para remedies falhados."""
        remedy = Remedy(
            problem_type="MemoryPressure",
            name="RestartPod",
            risk_level=0.05,
            time_to_fix=30.0,
            implementation="k8s.restart()",
            success_rate=0.5,
        )
        
        self.engine.record_incident(
            problem_type="MemoryPressure",
            diagnosis=RootCauseResult(
                possible_cause="MemoryPressure",
                confidence=0.65,
                reasoning="test",
                correlation="test",
            ),
            remedies_tried=[remedy],
            remedies_successful=[],
            time_to_resolution=30.0,
        )
        
        success_rate = self.engine.get_remedy_success_rate(
            "MemoryPressure",
            "RestartPod"
        )
        
        assert success_rate < 0.5
    
    def test_reorders_remedy_list(self):
        """testa reordenação de lista de remedies."""
        remedy1 = Remedy(
            problem_type="MemoryPressure",
            name="ForceGC",
            risk_level=0.01,
            time_to_fix=2.0,
            implementation="jvm.forceGC()",
            success_rate=0.5,
        )
        
        remedy2 = Remedy(
            problem_type="MemoryPressure",
            name="RestartPod",
            risk_level=0.05,
            time_to_fix=30.0,
            implementation="k8s.restart()",
            success_rate=0.5,
        )
        
        self.engine.record_incident(
            problem_type="MemoryPressure",
            diagnosis=RootCauseResult(
                possible_cause="MemoryPressure",
                confidence=0.65,
                reasoning="test",
                correlation="test",
            ),
            remedies_tried=[remedy1, remedy2],
            remedies_successful=[remedy1],
            time_to_resolution=30.0,
        )
        
        ordered = self.engine.get_best_remedy_order(
            "MemoryPressure",
            [remedy1, remedy2]
        )
        
        assert ordered[0].name == "ForceGC"
    
    def test_adapts_thresholds_dynamically(self):
        """testa adaptação dinâmica de thresholds."""
        self.engine.record_false_positive("memory")
        
        adjustment = self.engine.get_threshold_adjustment("memory")
        
        assert adjustment > 0
    
    def test_false_negative_adjustment(self):
        """testa ajuste para falso negativo."""
        self.engine.record_false_negative("memory")
        
        adjustment = self.engine.get_threshold_adjustment("memory")
        
        assert adjustment < 0


class TestThresholdAdapter:
    """testes para o adaptador de thresholds."""
    
    def setup_method(self) -> None:
        """setup para cada teste."""
        self.adapter = ThresholdAdapter(
            default_thresholds={"memory": 3.0, "cpu": 3.0},
            min_threshold=1.0,
            max_threshold=5.0,
        )
    
    def test_adjusts_threshold_for_false_positive(self):
        """testa ajuste para falso positivo."""
        new_threshold = self.adapter.adjust_threshold(
            "memory",
            is_false_positive=True
        )
        
        assert new_threshold > 3.0
    
    def test_adjusts_threshold_for_false_negative(self):
        """testa ajuste para falso negativo."""
        new_threshold = self.adapter.adjust_threshold(
            "memory",
            is_false_positive=False
        )
        
        assert new_threshold < 3.0
    
    def test_respects_min_threshold(self):
        """testa que não ultrapassa threshold mínimo."""
        for _ in range(50):
            self.adapter.adjust_threshold("memory", is_false_positive=False)
        
        threshold = self.adapter.get_threshold("memory")
        
        assert threshold >= 1.0
    
    def test_respects_max_threshold(self):
        """testa que não ultrapassa threshold máximo."""
        for _ in range(50):
            self.adapter.adjust_threshold("memory", is_false_positive=True)
        
        threshold = self.adapter.get_threshold("memory")
        
        assert threshold <= 5.0
    
    def test_reset_threshold(self):
        """testa reset de threshold."""
        self.adapter.adjust_threshold("memory", is_false_positive=True)
        
        default = self.adapter.reset_threshold("memory")
        
        assert default == 3.0
        assert self.adapter.get_threshold("memory") == 3.0
    
    def test_calculates_sensitivity(self):
        """testa cálculo de sensibilidade."""
        sensitivity = self.adapter.calculate_sensitivity("memory")
        
        assert sensitivity in ["low", "normal", "high"]
