"""
self-healing-os: sistema auto-remendante baseado em detecção de anomalias.

Este módulo fornece capacidades de:
- coleta de métricas do sistema
- aprendizado de baseline comportamental
- detecção de anomalias em tempo real
-suggestão de ações remedidoras
"""

__version__ = "0.1.0"
__author__ = "Self-Healing OS Team"

from src.config import Settings, get_settings

__all__ = ["Settings", "get_settings", "__version__"]
