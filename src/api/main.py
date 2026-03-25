"""
api fastapi para o sistema self-healing os.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any

from src.detection.zscore import ZScoreDetector
from src.detection.isolation_forest import IsolationForestDetector
from src.diagnosis.root_cause import RootCauseAnalyzer
from src.remediation.planner import RemediationPlanner
from src.learning.engine import LearningEngine

app = FastAPI(
    title="Self-Healing OS API",
    description="Sistema de detecção e diagnóstico para microserviços",
    version="1.0.0"
)

detector_zscore = ZScoreDetector(threshold=3.0)
detector_if = IsolationForestDetector()
analyzer = RootCauseAnalyzer()
planner = RemediationPlanner()
learning = LearningEngine()


class MetricInput(BaseModel):
    """input para.detecção de métricas."""
    metric_name: str
    value: float


class MetricsInput(BaseModel):
    """input para análise de múltiplas métricas."""
    metrics: dict[str, list[float]]


class IncidentInput(BaseModel):
    """input para registrar incidente."""
    problem_type: str
    diagnosis: dict[str, Any]
    remedies_tried: list[str]
    remedies_successful: list[str]
    time_to_resolution: float


@app.get("/")
def root():
    """rota principal."""
    return {
        "name": "Self-Healing OS API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
def health():
    """health check."""
    return {"status": "healthy"}


@app.post("/detect/zscore")
def detect_zscore(metric: MetricInput):
    """detecta anomalia usando z-score."""
    detector_zscore.detect(metric.metric_name, metric.value)
    return {"metric": metric.metric_name, "value": metric.value}


@app.post("/detect/isolation-forest")
def detect_if(data: list[list[float]]):
    """detecta anomalias usando isolation forest."""
    if not detector_if.is_trained:
        detector_if.train(data)
    
    results = []
    for point in data:
        score = detector_if.score(point)
        is_anomaly, _ = detector_if.detect(point, threshold=-0.5)
        results.append({"score": score, "anomaly": is_anomaly})
    
    return {"results": results}


@app.post("/diagnose")
def diagnose(metrics: MetricsInput):
    """diagnostica causa raiz das métricas."""
    diagnosis = analyzer.analyze(metrics.metrics)
    return diagnosis.to_dict()


@app.post("/suggest")
def suggest(diagnosis_data: dict[str, Any]):
    """sugere remedies baseados no diagnóstico."""
    from src.models.diagnosis import RootCauseResult
    
    diagnosis = RootCauseResult(
        possible_cause=diagnosis_data.get("possible_cause", "unknown"),
        confidence=diagnosis_data.get("confidence", 0.5),
        reasoning=diagnosis_data.get("reasoning", ""),
        correlation=diagnosis_data.get("correlation", ""),
        requires_human_intervention=diagnosis_data.get("requires_human_intervention", False)
    )
    
    suggestions = planner.suggest(diagnosis)
    return planner.get_suggestion_summary(suggestions)


@app.post("/learn/incident")
def learn_incident(incident: IncidentInput):
    """registra incidente para aprendizado."""
    from src.models.diagnosis import RootCauseResult
    from src.remediation.remedy_registry import Remedy
    
    diagnosis = RootCauseResult(
        possible_cause=incident.diagnosis.get("possible_cause", "unknown"),
        confidence=incident.diagnosis.get("confidence", 0.5),
        reasoning=incident.diagnosis.get("reasoning", ""),
        correlation=incident.diagnosis.get("correlation", ""),
    )
    
    remedies = [Remedy(
        problem_type=incident.problem_type,
        name=name,
        risk_level=0.05,
        time_to_fix=30.0,
        implementation="unknown"
    ) for name in incident.remedies_tried]
    
    successful = [Remedy(
        problem_type=incident.problem_type,
        name=name,
        risk_level=0.05,
        time_to_fix=30.0,
        implementation="unknown"
    ) for name in incident.remedies_successful]
    
    learning.record_incident(
        problem_type=incident.problem_type,
        diagnosis=diagnosis,
        remedies_tried=remedies,
        remedies_successful=successful,
        time_to_resolution=incident.time_to_resolution
    )
    
    return {"status": "recorded", "total_incidents": len(learning.incidents)}


@app.get("/learn/stats")
def learn_stats():
    """retorna estatísticas de aprendizado."""
    return learning.get_statistics()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)