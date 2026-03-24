"""execution engine com modo dry-run."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from src.models.diagnosis import RootCauseResult
from src.remediation.planner import SuggestedRemedy


@dataclass
class ExecutionResult:
    """resultado da execução de um remedy."""
    
    remedy_name: str
    status: str
    timestamp: datetime
    message: str
    metrics_before: dict[str, float] | None = None
    metrics_after: dict[str, float] | None = None
    rolled_back: bool = False
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "remedy_name": self.remedy_name,
            "status": self.status,
            "timestamp": self.timestamp.isoformat(),
            "message": self.message,
            "rolled_back": self.rolled_back,
        }


class SafeRemediationExecutor:
    """executor de remedies em modo dry-run."""
    
    def __init__(self, dry_run: bool = True) -> None:
        self.dry_run = dry_run
        self.execution_log: list[ExecutionResult] = []
    
    async def execute(
        self,
        remedy: SuggestedRemedy,
        metrics_before: dict[str, float],
    ) -> ExecutionResult:
        """executa remedy em modo dry-run."""
        
        timestamp = datetime.utcnow()
        
        if self.dry_run:
            result = ExecutionResult(
                remedy_name=remedy.remedy.name,
                status="dry_run",
                timestamp=timestamp,
                message=f"[DRY-RUN] seria executado: {remedy.remedy.implementation}",
                metrics_before=metrics_before,
                metrics_after=None,
            )
        else:
            result = await self._execute_really(remedy, metrics_before)
        
        self.execution_log.append(result)
        return result
    
    async def _execute_really(
        self,
        remedy: SuggestedRemedy,
        metrics_before: dict[str, float],
    ) -> ExecutionResult:
        """executa remedy realmente (futuro)."""
        return ExecutionResult(
            remedy_name=remedy.remedy.name,
            status="not_implemented",
            timestamp=datetime.utcnow(),
            message="execução real não implementada",
        )
    
    def get_execution_log(self) -> list[dict[str, Any]]:
        """retorna log de execuções."""
        return [r.to_dict() for r in self.execution_log]