from __future__ import annotations

from src.pipeline import run_pipeline
from src.shared.config import load_config


def main() -> None:
    config = load_config()
    print(
        f"Starting MVP pipeline in {config.cloud_mode} mode "
        f"for {config.iterations} iterations (device={config.device_id})."
    )

    sent_messages = run_pipeline(config)
    print(f"Finished. Telemetry messages sent: {len(sent_messages)}")


if __name__ == "__main__":
    main()
