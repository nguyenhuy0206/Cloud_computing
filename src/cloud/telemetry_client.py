from __future__ import annotations

import json
from typing import Dict, List


class MockTelemetryClient:
    """Local mock sender used by default for development/demo."""

    def __init__(self) -> None:
        self.messages: List[Dict[str, object]] = []

    def send(self, payload: Dict[str, object]) -> None:
        self.messages.append(dict(payload))
        print(f"[MOCK SEND] {json.dumps(payload)}")

    def close(self) -> None:
        return


class AzureIoTHubTelemetryClient:
    """Real sender for Azure IoT Hub device telemetry."""

    def __init__(self, connection_string: str) -> None:
        if not connection_string:
            raise ValueError("IOT_HUB_DEVICE_CONNECTION_STRING is required for azure mode.")

        try:
            from azure.iot.device import IoTHubDeviceClient, Message
        except ImportError as exc:
            raise RuntimeError(
                "azure-iot-device is not installed. Install it with: pip install azure-iot-device"
            ) from exc

        self._message_cls = Message
        self._client = IoTHubDeviceClient.create_from_connection_string(connection_string)
        self._client.connect()

    def send(self, payload: Dict[str, object]) -> None:
        message = self._message_cls(json.dumps(payload))
        self._client.send_message(message)
        print(f"[AZURE SEND] {json.dumps(payload)}")

    def close(self) -> None:
        self._client.shutdown()


def create_telemetry_client(mode: str, connection_string: str):
    if mode == "azure":
        return AzureIoTHubTelemetryClient(connection_string)
    return MockTelemetryClient()
