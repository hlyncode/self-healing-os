"""
configurações centralizadas do sistema self-healing-os.
"""

import os
from functools import lru_cache
from typing import Optional


class Settings:
    """configurações da aplicação."""

    def __init__(self) -> None:
        # configurações do Prometheus
        self.prometheus_url: str = os.getenv(
            "PROMETHEUS_URL", "http://localhost:9090"
        )
        self.prometheus_timeout: int = int(os.getenv("PROMETHEUS_TIMEOUT", "30"))

        # configurações do Grafana
        self.grafana_url: str = os.getenv("GRAFANA_URL", "http://localhost:3000")
        self.grafana_api_key: Optional[str] = os.getenv("GRAFANA_API_KEY")

        # configurações do Loki
        self.loki_url: str = os.getenv("LOKI_URL", "http://localhost:3100")

        # configurações de detecção de anomalias
        self.zscore_threshold: float = float(os.getenv("ZSCORE_THRESHOLD", "3.0"))
        self.isolation_contamination: float = float(
            os.getenv("ISOLATION_CONTAMINATION", "0.1")
        )

        # configurações de baseline
        self.baseline_window_size: int = int(
            os.getenv("BASELINE_WINDOW_SIZE", "1000")
        )
        self.baseline_learning_rate: float = float(
            os.getenv("BASELINE_LEARNING_RATE", "0.01")
        )

        # configurações de coleta
        self.collection_interval: int = int(
            os.getenv("COLLECTION_INTERVAL", "15")
        )
        self.metrics_retention_days: int = int(
            os.getenv("METRICS_RETENTION_DAYS", "30")
        )

        # configurações do servidor
        self.api_host: str = os.getenv("API_HOST", "0.0.0.0")
        self.api_port: int = int(os.getenv("API_PORT", "8000"))
        self.debug_mode: bool = os.getenv("DEBUG", "false").lower() == "true"


@lru_cache()
def get_settings() -> Settings:
    """retorna instância singleton das configurações."""
    return Settings()
