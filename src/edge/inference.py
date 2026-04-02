from __future__ import annotations

import random
import time
from typing import Dict


class InferenceEngine:
    """Small inference simulator for Phase 1 MVP.

    The real project will replace this with the exported edge model runtime.
    """

    def __init__(self, anomaly_threshold: float = 0.6) -> None:
        self.anomaly_threshold = anomaly_threshold

    def predict(self, sensor_value: float | None = None) -> Dict[str, float | str]:
        start = time.perf_counter()

        # If hardware input is unavailable, simulate a sensor/model score.
        score = sensor_value if sensor_value is not None else random.random()
        prediction = "anomaly" if score >= self.anomaly_threshold else "normal"
        confidence = round(abs(score - 0.5) * 2, 3)

        inference_ms = round((time.perf_counter() - start) * 1000, 3)
        return {
            "prediction": prediction,
            "confidence": confidence,
            "raw_score": round(score, 3),
            "inference_ms": inference_ms,
        }
