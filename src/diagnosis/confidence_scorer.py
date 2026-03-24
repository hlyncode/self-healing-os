"""
módulo de cálculo de confiança para diagnósticos.
"""

from typing import Any

from src.models.diagnosis import Evidence


class ConfidenceScorer:
    """
    calcula confiança para diagnósticos.
    
    nunca retorna confiança > 75%, sempre mantém
    humildade estatística appropriate.
    """

    def __init__(
        self,
        min_confidence: float = 0.60,
        max_confidence: float = 0.75,
        human_intervention_threshold: float = 0.60,
    ) -> None:
        self.min_confidence = min_confidence
        self.max_confidence = max_confidence
        self.human_intervention_threshold = human_intervention_threshold
        self.evidence_weights: dict[str, float] = {
            "anomaly": 0.3,
            "correlation": 0.25,
            "historical_match": 0.2,
            "baseline_deviation": 0.15,
            "trend": 0.1,
        }

    def score(
        self,
        diagnosis_confidence: float,
        evidence: list[Evidence],
    ) -> float:
        """
        calcula score de confiança baseado em evidências.
        
        Args:
            diagnosis_confidence: confiança base do diagnóstico
            evidence: lista de evidências suportando o diagnóstico
            
        Returns:
            confiança final entre 0 e 1
        """
        if not evidence:
            return max(diagnosis_confidence * 0.5, 0.1)
        
        evidence_score = self._calculate_evidence_score(evidence)
        
        evidence_bonus = min(evidence_score * 0.1, 0.1)
        
        final_confidence = diagnosis_confidence + evidence_bonus
        
        final_confidence = max(
            self.min_confidence,
            min(final_confidence, self.max_confidence)
        )
        
        return round(final_confidence, 2)

    def _calculate_evidence_score(
        self,
        evidence: list[Evidence]
    ) -> float:
        """calcula score agregado das evidências."""
        total_weight = 0.0
        weighted_sum = 0.0
        
        for ev in evidence:
            weight = self.evidence_weights.get(ev.evidence_type, 0.1)
            quality = self._evaluate_evidence_quality(ev)
            
            weighted_sum += weight * quality
            total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        return weighted_sum / total_weight

    def _evaluate_evidence_quality(self, evidence: Evidence) -> float:
        """avalia qualidade de uma evidência individual."""
        if evidence.change_magnitude > 0.5:
            return 1.0
        elif evidence.change_magnitude > 0.2:
            return 0.7
        elif evidence.change_magnitude > 0.1:
            return 0.4
        else:
            return 0.2

    def requires_human_intervention(
        self,
        confidence: float
    ) -> bool:
        """
        determina se o diagnóstico requer intervenção humana.
        
        Args:
            confidence: confiança calculada
            
        Returns:
            true se confiança < threshold
        """
        return confidence < self.human_intervention_threshold

    def get_diagnosis_summary(
        self,
        confidence: float,
        evidence: list[Evidence],
    ) -> dict[str, Any]:
        """
        retorna resumo do diagnóstico com confiança.
        
        Args:
            confidence: confiança calculada
            evidence: evidências utilizadas
            
        Returns:
            dicionário com resumo
        """
        return {
            "confidence": confidence,
            "requires_human": self.requires_human_intervention(confidence),
            "evidence_count": len(evidence),
            "confidence_level": self._get_confidence_level(confidence),
            "recommendation": self._get_recommendation(confidence),
        }

    def _get_confidence_level(self, confidence: float) -> str:
        """retorna nível textual de confiança."""
        if confidence >= 0.7:
            return "high"
        elif confidence >= 0.6:
            return "moderate"
        elif confidence >= 0.4:
            return "low"
        else:
            return "very_low"

    def _get_recommendation(self, confidence: float) -> str:
        """retorna recomendação baseada na confiança."""
        if confidence >= 0.7:
            return "proceed_with_automated_action"
        elif confidence >= 0.6:
            return "suggest_remedy_require_approval"
        else:
            return "require_human_investigation"
