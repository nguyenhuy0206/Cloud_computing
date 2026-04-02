from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


@dataclass
class AppConfig:
    cloud_mode: str
    telemetry_interval_sec: float
    iterations: int
    device_id: str
    iot_hub_device_connection_string: str


def _load_env_file(path: Path) -> None:
    """Load simple KEY=VALUE pairs from a local .env file.

    Existing process environment variables are not overwritten.
    """

    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue

        key, raw_value = stripped.split("=", 1)
        value = raw_value.strip().strip('"').strip("'")
        os.environ.setdefault(key.strip(), value)


def load_config(env_path: str = ".env") -> AppConfig:
    _load_env_file(Path(env_path))

    cloud_mode = os.getenv("CLOUD_MODE", "mock").strip().lower()
    if cloud_mode not in {"mock", "azure"}:
        raise ValueError("CLOUD_MODE must be 'mock' or 'azure'.")

    return AppConfig(
        cloud_mode=cloud_mode,
        telemetry_interval_sec=float(os.getenv("TELEMETRY_INTERVAL_SEC", "1.0")),
        iterations=int(os.getenv("ITERATIONS", "5")),
        device_id=os.getenv("DEVICE_ID", "edge-demo-01"),
        iot_hub_device_connection_string=os.getenv("IOT_HUB_DEVICE_CONNECTION_STRING", ""),
    )
