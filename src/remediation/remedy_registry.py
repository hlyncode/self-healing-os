"""
registry de remedies para o sistema self-healing.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Remedy:
    """representa um remedy disponível no sistema."""
    
    problem_type: str
    name: str
    risk_level: float
    time_to_fix: float
    implementation: str
    success_rate: float = 0.5
    preconditions: list[str] = field(default_factory=list)
    description: str = ""
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "problem_type": self.problem_type,
            "name": self.name,
            "risk_level": self.risk_level,
            "time_to_fix": self.time_to_fix,
            "implementation": self.implementation,
            "success_rate": self.success_rate,
            "preconditions": self.preconditions,
            "description": self.description,
        }


class RemedyRegistry:
    """
    registry de remedies conhecidos.
    
    mantém base de conhecimento de problemas e suas
    possíveis soluções correspondentes.
    """
    
    def __init__(self) -> None:
        self._remedies: dict[str, list[Remedy]] = {}
        self._initialize_default_remedies()
    
    def _initialize_default_remedies(self) -> None:
        """inicializa remedies padrão do sistema."""
        
        memory_remedies = [
            Remedy(
                problem_type="MemoryPressure",
                name="ForceGC",
                risk_level=0.01,
                time_to_fix=2.0,
                implementation="jvm.forceGC()",
                success_rate=0.95,
                preconditions=["jvm_based"],
                description="forçar garbage collection",
            ),
            Remedy(
                problem_type="MemoryPressure",
                name="IncreaseHeap",
                risk_level=0.03,
                time_to_fix=0.0,
                implementation="pod.updateEnv(XMX=4G)",
                success_rate=0.88,
                preconditions=["k8s_available"],
                description="aumentar heap memory em 2gb",
            ),
            Remedy(
                problem_type="MemoryPressure",
                name="RestartPod",
                risk_level=0.05,
                time_to_fix=30.0,
                implementation="k8s.restart(pod)",
                success_rate=0.99,
                preconditions=["k8s_available"],
                description="reiniciar o pod",
            ),
        ]
        
        latency_remedies = [
            Remedy(
                problem_type="HighLatency",
                name="ScalePod",
                risk_level=0.02,
                time_to_fix=60.0,
                implementation="k8s.scale(replicas=3)",
                success_rate=0.85,
                preconditions=["k8s_available", "capacity_available"],
                description="escalar para 3 réplicas",
            ),
            Remedy(
                problem_type="HighLatency",
                name="RestartPod",
                risk_level=0.05,
                time_to_fix=30.0,
                implementation="k8s.restart(pod)",
                success_rate=0.90,
                preconditions=["k8s_available"],
                description="reiniciar o pod",
            ),
            Remedy(
                problem_type="HighLatency",
                name="CheckDatabase",
                risk_level=0.0,
                time_to_fix=0.0,
                implementation="manual: check db connections",
                success_rate=0.70,
                preconditions=["db_access"],
                description="verificar conexões do banco",
            ),
            Remedy(
                problem_type="HighLatency",
                name="CheckNetwork",
                risk_level=0.0,
                time_to_fix=0.0,
                implementation="manual: check network latency",
                success_rate=0.65,
                preconditions=["network_access"],
                description="verificar latência de rede",
            ),
        ]
        
        cpu_remedies = [
            Remedy(
                problem_type="HighCPU",
                name="ScalePod",
                risk_level=0.02,
                time_to_fix=60.0,
                implementation="k8s.scale(replicas=3)",
                success_rate=0.82,
                preconditions=["k8s_available", "capacity_available"],
                description="escalar para 3 réplicas",
            ),
            Remedy(
                problem_type="HighCPU",
                name="RestartPod",
                risk_level=0.05,
                time_to_fix=30.0,
                implementation="k8s.restart(pod)",
                success_rate=0.95,
                preconditions=["k8s_available"],
                description="reiniciar o pod",
            ),
        ]
        
        throughput_remedies = [
            Remedy(
                problem_type="LowThroughput",
                name="ScalePod",
                risk_level=0.02,
                time_to_fix=60.0,
                implementation="k8s.scale(replicas=5)",
                success_rate=0.80,
                preconditions=["k8s_available", "capacity_available"],
                description="escalar para 5 réplicas",
            ),
        ]
        
        error_remedies = [
            Remedy(
                problem_type="HighErrorRate",
                name="RestartPod",
                risk_level=0.05,
                time_to_fix=30.0,
                implementation="k8s.restart(pod)",
                success_rate=0.92,
                preconditions=["k8s_available"],
                description="reiniciar o pod",
            ),
            Remedy(
                problem_type="HighErrorRate",
                name="Rollback",
                risk_level=0.10,
                time_to_fix=120.0,
                implementation="k8s.rollback()",
                success_rate=0.88,
                preconditions=["k8s_available", "previous_version"],
                description="fazer rollback para versão anterior",
            ),
        ]
        
        self._remedies = {
            "MemoryPressure": memory_remedies,
            "HighLatency": latency_remedies,
            "HighCPU": cpu_remedies,
            "LowThroughput": throughput_remedies,
            "HighErrorRate": error_remedies,
        }
    
    def get_remedies(
        self,
        problem_type: str
    ) -> list[Remedy]:
        """
        obtém lista de remedies para um tipo de problema.
        
        Args:
            problem_type: tipo do problema
            
        Returns:
            lista de remedies disponíveis
        """
        return self._remedies.get(problem_type, [])
    
    def add_remedy(self, remedy: Remedy) -> None:
        """
        adiciona um novo remedy ao registry.
        
        Args:
            remedy: remedy a ser adicionado
        """
        if remedy.problem_type not in self._remedies:
            self._remedies[remedy.problem_type] = []
        
        self._remedies[remedy.problem_type].append(remedy)
    
    def update_success_rate(
        self,
        problem_type: str,
        remedy_name: str,
        success: bool
    ) -> None:
        """
        atualiza taxa de sucesso de um remedy.
        
        Args:
            problem_type: tipo do problema
            remedy_name: nome do remedy
            success: se o remedy funcionou
        """
        remedies = self.get_remedies(problem_type)
        
        for remedy in remedies:
            if remedy.name == remedy_name:
                if success:
                    remedy.success_rate = min(0.99, remedy.success_rate + 0.05)
                else:
                    remedy.success_rate = max(0.1, remedy.success_rate - 0.05)
                break
    
    def get_all_problem_types(self) -> list[str]:
        """retorna todos os tipos de problema registrados."""
        return list(self._remedies.keys())
