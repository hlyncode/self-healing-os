"""
detector de anomalias usando isolation forest.
"""

import random
from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class AnomalyResult:
    """resultado da detecção de anomalia."""

    is_anomaly: bool
    score: float


class IsolationTreeNode:
    """nó da árvore de isolation forest."""

    def __init__(
        self,
        left: Optional["IsolationTreeNode"],
        right: Optional["IsolationTreeNode"],
        split_feature: Optional[int],
        split_value: Optional[float],
    ) -> None:
        self.left = left
        self.right = right
        self.split_feature = split_feature
        self.split_value = split_value
        self.size = 0


class IsolationTree:
    """árvore de isolamento para detecção de anomalias."""

    def __init__(self, height_limit: int) -> None:
        self.height_limit = height_limit
        self.root: Optional[IsolationTreeNode] = None

    def build(self, data: np.ndarray, current_height: int = 0) -> None:
        """constrói a árvore de isolamento."""
        if current_height >= self.height_limit or len(data) <= 1:
            self.root = IsolationTreeNode(None, None, None, None)
            self.root.size = len(data)
            return

        feature_count = data.shape[1]
        split_feature = random.randint(0, feature_count - 1)

        values = data[:, split_feature]
        min_value, max_value = values.min(), values.max()

        if min_value == max_value:
            self.root = IsolationTreeNode(None, None, None, None)
            self.root.size = len(data)
            return

        split_value = random.uniform(min_value, max_value)

        left_data = data[data[:, split_feature] < split_value]
        right_data = data[data[:, split_feature] >= split_value]

        left_tree = IsolationTree(self.height_limit)
        right_tree = IsolationTree(self.height_limit)

        left_tree.build(left_data, current_height + 1)
        right_tree.build(right_data, current_height + 1)

        self.root = IsolationTreeNode(
            left_tree.root, right_tree.root, split_feature, split_value
        )
        self.root.size = len(data)

    def path_length(self, point: np.ndarray) -> int:
        """calcula o comprimento do caminho para um ponto."""
        node = self.root

        if node is None or node.split_feature is None:
            return current_height_to_eof(node)

        current_height = 0
        while node.left is not None and node.right is not None:
            split_feature = node.split_feature
            split_value = node.split_value

            if point[split_feature] < split_value:
                node = node.left
            else:
                node = node.right
            current_height += 1

        return current_height + estimated_path_length(node.size)


def current_height_to_eof(node: Optional[IsolationTreeNode]) -> int:
    """calcula altura estimada até nó externo."""
    if node is None:
        return 0
    return 2 * (np.log(node.size - 1) + 0.5772156649) if node.size > 1 else 0


def estimated_path_length(size: int) -> float:
    """calcula comprimento estimado de caminho."""
    if size <= 1:
        return 0
    return 2 * (np.log(size - 1) + 0.5772156649)


class IsolationForestDetector:
    """detector de anomalias usando isolation forest."""

    def __init__(
        self,
        num_trees: int = 100,
        sample_size: Optional[int] = None,
        contamination: float = 0.1,
    ) -> None:
        self.num_trees = num_trees
        self.sample_size = sample_size
        self.contamination = contamination
        self.trees: list[IsolationTree] = []
        self.is_trained = False
        self.threshold: Optional[float] = None

    def train(self, historical_data: list[list[float]]) -> None:
        """treina o modelo com dados históricos."""
        if not historical_data:
            raise ValueError("historical_data cannot be empty")

        data = np.array(historical_data)
        sample_size = self.sample_size or min(256, len(data))
        height_limit = int(np.ceil(np.log2(sample_size)))

        self.trees = []
        for _ in range(self.num_trees):
            indices = random.choices(range(len(data)), k=sample_size)
            sample = data[indices]

            tree = IsolationTree(height_limit)
            tree.build(sample)
            self.trees.append(tree)

        self._calculate_threshold(data)
        self.is_trained = True

    def _calculate_threshold(self, data: np.ndarray) -> None:
        """calcula threshold baseado em dados de treinamento."""
        scores = self.score_all(data)
        sorted_scores = np.sort(scores)
        index = int(len(sorted_scores) * (1 - self.contamination))
        self.threshold = sorted_scores[index] if index < len(sorted_scores) else 0.5

    def score(self, current_value: list[float]) -> float:
        """retorna score de anomalia (-1 a 1)."""
        if not self.is_trained:
            raise RuntimeError("model must be trained before scoring")

        point = np.array(current_value)
        avg_path_length = self._average_path_length(point)

        c = self._average_path_length_synthetic()
        score = 2 ** (-avg_path_length / c)

        normalized = (score - 0.5) * 2
        normalized = max(-1.0, min(1.0, normalized))

        return -normalized

    def score_all(self, data: np.ndarray) -> np.ndarray:
        """calcula scores para múltiplos pontos."""
        scores = []
        for point in data:
            avg_path = self._average_path_length(point)
            c = self._average_path_length_synthetic()
            score = 2 ** (-avg_path / c)
            scores.append(score)
        return np.array(scores)

    def _average_path_length(self, point: np.ndarray) -> float:
        """calcula caminho médio em todas as árvores."""
        total = 0.0
        for tree in self.trees:
            total += tree.path_length(point)
        return total / len(self.trees)

    def _average_path_length_synthetic(self) -> float:
        """calcula comprimento médio de caminho para dados sintéticos."""
        n = self.sample_size or 256
        if n <= 1:
            return 1.0
        return 2 * (np.log(n - 1) + 0.5772156649) - (2 * (n - 1) / n)

    def detect(
        self, current_value: list[float], threshold: float = 0.0
    ) -> tuple[bool, float]:
        """detecta se o valor é anômalo."""
        score = self.score(current_value)
        is_anomaly = score < threshold or (self.threshold and score < self.threshold)
        return (is_anomaly, score)
