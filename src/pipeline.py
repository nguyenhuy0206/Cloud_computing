from __future__ import annotations

from datetime import datetime, timezone
import time
from typing import Dict, List

from src.cloud.telemetry_client import MockTelemetryClient, create_telemetry_client
from src.edge.inference import InferenceEngine
from src.shared.config import AppConfig


def build_telemetry_payload(device_id: str, inference_result: Dict[str, object]) -> Dict[str, object]:
    return {
        "device_id": device_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prediction": inference_result["prediction"],
        "confidence": inference_result["confidence"],
        "raw_score": inference_result["raw_score"],
        "inference_ms": inference_result["inference_ms"],
    }


def run_pipeline(config: AppConfig) -> List[Dict[str, object]]:
    """Run minimal local MVP inference loop and send telemetry."""

    engine = InferenceEngine()
    telemetry_client = create_telemetry_client(
        config.cloud_mode,
        config.iot_hub_device_connection_string,
    )

    sent_messages: List[Dict[str, object]] = []

    try:
        for index in range(config.iterations):
            inference_result = engine.predict()
            payload = build_telemetry_payload(config.device_id, inference_result)
            telemetry_client.send(payload)
            sent_messages.append(payload)

            # Avoid an unnecessary sleep after the final iteration.
            is_last_iteration = index == (config.iterations - 1)
            if not is_last_iteration and config.telemetry_interval_sec > 0:
                time.sleep(config.telemetry_interval_sec)
    finally:
        telemetry_client.close()

    if isinstance(telemetry_client, MockTelemetryClient):
        return telemetry_client.messages

    return sent_messages
