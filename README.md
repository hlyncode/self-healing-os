# Self-Healing OS

Sistema inteligente de detecção e diagnóstico automático para microserviços que observa sinais vitais, identifica anomalias, diagnostica causas raiz e sugere ações ao operador humano.

## O Problema

Imagine seu sistema distribuído rodando em produção às 2 da manhã:
- 10.000 requisições por segundo
- 5 microserviços se comunicando entre si
- De repente, latency dispara, memory sobe para 92%, tudo começa a degradar

Quem vai resolver? Você, acordando às pressas? Ou seu próprio sistema?

## A Solução

Este projeto implementa um sistema de auto-cura inteligente que:
- **Detecta anomalias** utilizando z-score e isolation forest
- **Identifica causa raiz** através de correlação temporal (nunca afirma causalidade)
- **Sugere o melhor remedy** baseado em histórico e taxa de sucesso
- **Aprende continuamente** com cada incidente registrado

O sistema **não executa automaticamente** — sugere ações ao operador humano, que decide se aprova ou não.

## Como Funciona

```
Métricas (Prometheus) → Detecção → Diagnóstico → Sugestão → Operador Decide
                                              ↓
                                    Aprendizado Contínuo
```

1. **Coleta**: Métricas chegam via Prometheus exporter
2. **Detecção**: Baseline learning + Z-Score + Isolation Forest
3. **Diagnóstico**: Root cause inference com confiança limitada (máx 70%)
4. **Ação**: Sugere o melhor remedy (não executa automaticamente)
5. **Aprendizado**: Atualiza taxa de sucesso dos remedies baseado em feedback

## Quick Start

```bash
# Instalar dependências
pip install -r requirements.txt

# Subir infraestrutura (Prometheus, Grafana, Loki)
docker-compose up -d

# Rodar testes
pytest tests/ -v
```

## Estrutura do Projeto

```
src/
├── config.py                    # Configurações centralizadas
├── collectors/                  # Coleta de métricas do sistema
├── detection/                   # Módulo de detecção de anomalias
│   ├── baseline.py              # Aprende padrões normais do sistema
│   ├── zscore.py                # Detector estatístico (z-score)
│   ├── isolation_forest.py      # ML para detecção de anomalias
│   └── multi_metric.py          # Análise multi-métrica com trend
├── diagnosis/                   # Módulo de diagnóstico
│   ├── root_cause.py            # Análise de causa raiz (correlação temporal)
│   └── confidence_scorer.py     # Cálculo de confiança (máx 70%)
├── remediation/                 # Módulo de remediação
│   ├── remedy_registry.py       # Base de conhecimento de remedies
│   ├── planner.py               # Planejador de sugestões
│   └── executor.py             # Executor em modo dry-run
├── learning/                   # Módulo de aprendizado
│   ├── engine.py                # Motor de aprendizado contínuo
│   └── threshold_adapter.py    # Adaptador dinâmico de thresholds
└── prediction/                  # Módulo de predição
    └── engine.py                # Forecasting de recursos
```

## Exemplos de Uso

### Detectando Anomalias

```python
from src.detection.zscore import ZScoreDetector

# Cria detector com threshold de 3.0 desvios padrão
detector = ZScoreDetector(threshold=3.0)

# Treina com dados normais
for _ in range(50):
    detector.detect("cpu_usage", 50.0)

# Detecta anomalia
anomaly = detector.detect("cpu_usage", 100.0)
# Result: Anomaly(metric_name='cpu_usage', severity='critical', score=7.0)
```

### Diagnóstico de Causa Raiz

```python
from src.diagnosis.root_cause import RootCauseAnalyzer

analyzer = RootCauseAnalyzer()

# Analisa métricas
metrics = {
    "cpu": [30, 32, 35, 80, 90],
    "memory": [50, 52, 55, 85, 92],
    "latency": [45, 48, 50, 200, 500]
}

diagnosis = analyzer.analyze(metrics)

# Result: possible_cause="HighCPU", confidence=0.65
# reasoning: "cpu changed first, correlated with memory"
```

### Sugestão de Remedy

```python
from src.remediation.planner import RemediationPlanner
from src.models.diagnosis import RootCauseResult

planner = RemediationPlanner()

diagnosis = RootCauseResult(
    possible_cause="MemoryPressure",
    confidence=0.65,
    reasoning="memory increased first",
    correlation="memory↑ → latency↑",
    requires_human_intervention=False
)

suggestions = planner.suggest(diagnosis)

# suggestions[0] contém o melhor remedy
# {
#   "name": "RestartPod",
#   "confidence": 0.62,
#   "risk_level": 0.05,
#   "success_rate": 0.99
# }
```

## Stack Tecnológico

- **Python 3.11+** — Linguagem principal
- **scikit-learn** — Isolation Forest para ML
- **Prometheus** — Coleta de métricas
- **Grafana** — Visualização e dashboards
- **Loki** — Agregação de logs

## Testes

```bash
pytest tests/ -v

# 82 testes passando
# Coverage: >85%
```

## API

```bash
# instalar dependências
pip install -r requirements.txt

# rodar api
python -m src.api.main
# ou
uvicorn src.api.main:app --reload

# endpoints disponíveis:
# GET  /           - informações da api
# GET  /health     - health check
# POST /detect/zscore - detecta anomalia com z-score
# POST /detect/isolation-forest - detecta com isolation forest
# POST /diagnose  - diagnostica causa raiz
# POST /suggest   - sugere remedies
# POST /learn/incident - registra incidente
# GET  /learn/stats - estatísticas de aprendizado
```

## Decisões de Design

### Modo Sugestão, Não Execução Automática
Este projeto opera em modo sugestão — detecta anomalias, diagnostica e sugere actions ao operador humano. A execução automática de remedies (como "aumentar heap" ou "restart pod") é arriscada em produção real e foi evitada intencionalmente. Este modo é mais realista para a maioria das empresas.

### Humildade Estatística
O sistema nunca afirma causalidade — apenas correlação. A confiança máxima em diagnósticos é de 70%, e quando a confiança é muito baixa, o sistema pede intervenção humana. Isso demonstra maturidade técnica e honestidade.

### Aprendizado Contínuo
O sistema aprende com cada incidente — atualiza a taxa de sucesso dos remedies, ajusta thresholds baseado em falsos positivos/negativos, e melhora continuamente suas sugestões.

## Licença

MIT License

Copyright (c) 2024

## Sobre Este Projeto

Este projeto foi desenvolvido como portfólio técnico para demonstrar expertise em:
- Sistemas distribuídos e observabilidade
- Machine Learning aplicado a problemas reais
- Arquitetura resiliente que aprende e se adapta
- Pensamento crítico em engenharia de sistemas

### stack + Ferramentas

Este projeto foi desenvolvido utilizando ferramentas de ia como assistente e otimizador de código. O conhecimento técnico, arquitetura e decisões de design foram definidos por mim, enquanto a ia foi usada como ferramenta para acelerar a implementação.