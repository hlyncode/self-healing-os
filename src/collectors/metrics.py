"""
coletor de métricas base para o sistema self-healing-os.
"""

import asyncio
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from datetime import datetime, UTC, UTC
from typing import Any, Optional

import psutil

from src.config import get_settings
from src.models.types import Metric, MetricType


class MetricsCollector(ABC):
    """classe base abstrata para coletores de métricas."""

    def __init__(self) -> None:
        self.settings = get_settings()

    @abstractmethod
    async def collect(self) -> list[Metric]:
        """coleta métricas do sistema."""
        pass

    @abstractmethod
    async def collect_metric(self, metric_name: str) -> Optional[Metric]:
        """coleta uma métrica específica."""
        pass


class SystemMetricsCollector(MetricsCollector):
    """coletor de métricas do sistema operacional."""

    def __init__(self) -> None:
        super().__init__()
        self._running = False
        self._collection_task: Optional[asyncio.Task] = None

    async def collect(self) -> list[Metric]:
        """coleta todas as métricas do sistema."""
        metrics: list[Metric] = []

        cpu_metric = await self.collect_cpu_usage()
        if cpu_metric:
            metrics.append(cpu_metric)

        memory_metric = await self.collect_memory_usage()
        if memory_metric:
            metrics.append(memory_metric)

        disk_metric = await self.collect_disk_io()
        if disk_metric:
            metrics.append(disk_metric)

        network_metric = await self.collect_network_io()
        if network_metric:
            metrics.append(network_metric)

        return metrics

    async def collect_cpu_usage(self) -> Optional[Metric]:
        """coleta uso de cpu."""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        return Metric(
            name="system_cpu_usage_percent",
            value=cpu_percent,
            metric_type=MetricType.CPU_USAGE,
            timestamp=datetime.utcnow(),
            unit="percent",
        )

    async def collect_memory_usage(self) -> Optional[Metric]:
        """coleta uso de memória."""
        memory = psutil.virtual_memory()
        return Metric(
            name="system_memory_usage_percent",
            value=memory.percent,
            metric_type=MetricType.MEMORY_USAGE,
            timestamp=datetime.utcnow(),
            unit="percent",
        )

    async def collect_disk_io(self) -> Optional[Metric]:
        """coleta i/o de disco."""
        disk_io = psutil.disk_io_counters()
        if disk_io:
            return Metric(
                name="system_disk_io_bytes",
                value=disk_io._asdict().get("read_bytes", 0),
                metric_type=MetricType.DISK_IO,
                timestamp=datetime.utcnow(),
                unit="bytes",
            )
        return None

    async def collect_network_io(self) -> Optional[Metric]:
        """coleta i/o de rede."""
        net_io = psutil.net_io_counters()
        if net_io:
            return Metric(
                name="system_network_io_bytes",
                value=net_io._asdict().get("bytes_sent", 0),
                metric_type=MetricType.NETWORK_IO,
                timestamp=datetime.utcnow(),
                unit="bytes",
            )
        return None

    async def collect_metric(self, metric_name: str) -> Optional[Metric]:
        """coleta uma métrica específica por nome."""
        metric_map: dict[str, Any] = {
            "system_cpu_usage_percent": self.collect_cpu_usage,
            "system_memory_usage_percent": self.collect_memory_usage,
            "system_disk_io_bytes": self.collect_disk_io,
            "system_network_io_bytes": self.collect_network_io,
        }
        collector = metric_map.get(metric_name)
        if collector:
            return await collector()
        return None

    async def stream_metrics(self, interval: int = 15) -> AsyncIterator[list[Metric]]:
        """stream contínuo de métricas."""
        self._running = True
        while self._running:
            metrics = await self.collect()
            yield metrics
            await asyncio.sleep(interval)

    def stop_collection(self) -> None:
        """para a coleta contínua de métricas."""
        self._running = False
        if self._collection_task:
            self._collection_task.cancel()
