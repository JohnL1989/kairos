"""
RL Weight Optimizer — 余弦学习率衰减 + epsilon-greedy 探索

用于 instinct 置信度更新，替代 ad-hoc 加减法公式。
"""
import math
import random


class RLWeightOptimizer:
    """Instinct 置信度 RL 优化器"""

    def __init__(self, base_lr: float = 0.1, epsilon: float = 0.05, total_epochs: int = 100):
        self.epoch = 0
        self.base_lr = base_lr
        self.epsilon = epsilon
        self.total_epochs = total_epochs

    def cosine_lr(self) -> float:
        """余弦学习率衰减：初期快收敛，后期慢微调"""
        if self.epoch >= self.total_epochs:
            return self.base_lr * 0.01  # 最低学习率
        return 0.5 * self.base_lr * (1 + math.cos(self.epoch * math.pi / self.total_epochs))

    def update(self, confidence: float, direction: str) -> float:
        """
        更新置信度。

        参数:
            confidence: 当前置信度 (0.0-1.0)
            direction: "positive" | "negative" | "explore"
        返回:
            更新后的置信度
        """
        self.epoch += 1
        lr = self.cosine_lr()

        # epsilon-greedy 探索
        if random.random() < self.epsilon:
            return max(0.1, min(0.95, confidence + random.uniform(-0.05, 0.05)))

        if direction == "positive":
            return confidence + lr * (1 - confidence)
        elif direction == "negative":
            # 负向反馈影响更大（2x lr）
            return confidence - 2 * lr * confidence
        else:  # neutral / explore
            return confidence
