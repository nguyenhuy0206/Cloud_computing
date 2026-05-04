"""device_service.py

Connects to Azure IoT Hub using a Device Connection String,
listens for Device Twin desired-property patches, and triggers
the OTA callback when a new model update is detected.

Pattern mirrors telemetry_client.py (already in the project).
"""
from __future__ import annotations

import logging
import threading
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# The key name used in Device Twin desired properties.
# MUST match whatever Teammate A's Cloud script writes.
TWIN_MODEL_UPDATE_KEY = "modelUpdate"


class DeviceService:
    """Manages the IoT Hub Device Twin connection on the Edge device.

    Usage
    -----
    service = DeviceService(
        connection_string="HostName=...",
        on_model_update=my_callback,   # called with (version: str, url: str)
    )
    service.start()   # non-blocking — starts background listener
    ...
    service.stop()
    """

    def __init__(
        self,
        connection_string: str,
        on_model_update: Callable[[str, str], None],
    ) -> None:
        if not connection_string:
            raise ValueError("IOT_HUB_DEVICE_CONNECTION_STRING is required.")

        self._connection_string = connection_string
        self._on_model_update = on_model_update
        self._client = None
        self._stop_event = threading.Event()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Connect to IoT Hub and register the Twin patch listener."""
        try:
            from azure.iot.device import IoTHubDeviceClient
        except ImportError as exc:
            raise RuntimeError(
                "azure-iot-device is not installed. Run: pip install azure-iot-device"
            ) from exc

        logger.info("[DeviceService] Connecting to Azure IoT Hub...")
        self._client = IoTHubDeviceClient.create_from_connection_string(
            self._connection_string
        )
        self._client.connect()
        logger.info("[DeviceService] Connected! Listening for Device Twin patches...")

        # Fetch initial twin on startup — handles the case where a model update
        # was sent while the device was offline.
        self._check_initial_twin()

        # Register callback for future patches
        self._client.on_twin_desired_properties_patch_received = self._twin_patch_handler

    def report_status(self, version: str, status: str) -> None:
        """Send reported properties back to IoT Hub (visible in Azure Portal)."""
        if self._client is None:
            logger.warning("[DeviceService] Cannot report — client not started.")
            return

        reported = {
            "currentModel": {
                "version": version,
                "status": status,
            }
        }
        self._client.patch_twin_reported_properties(reported)
        logger.info("[DeviceService] Reported status to Cloud: %s v%s", status, version)

    def stop(self) -> None:
        if self._client:
            self._client.shutdown()
            logger.info("[DeviceService] Disconnected from IoT Hub.")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _twin_patch_handler(self, patch: dict) -> None:
        """Called automatically by the SDK when desired properties change."""
        logger.info("[DeviceService] Twin patch received: %s", patch)
        self._process_patch(patch)

    def _check_initial_twin(self) -> None:
        """On startup, read the full twin to catch any missed update while offline."""
        try:
            twin = self._client.get_twin()
            desired = twin.get("desired", {})
            if TWIN_MODEL_UPDATE_KEY in desired:
                logger.info("[DeviceService] Found pending model update in initial Twin.")
                self._process_patch(desired)
        except Exception as exc:
            logger.warning("[DeviceService] Could not fetch initial twin: %s", exc)

    def _process_patch(self, patch: dict) -> None:
        """Extract modelUpdate fields and invoke the OTA callback."""
        model_info = patch.get(TWIN_MODEL_UPDATE_KEY)
        if not model_info:
            return  # patch is about something else, ignore

        version: Optional[str] = model_info.get("version")
        download_url: Optional[str] = model_info.get("downloadUrl")

        if not download_url:
            logger.warning("[DeviceService] Patch has modelUpdate but no downloadUrl.")
            return

        logger.info(
            "[DeviceService] Model update requested — version=%s", version
        )
        # Invoke the OTA callback (defined in ota.py) in the current thread.
        # OTA will handle the actual download + swap.
        self._on_model_update(version or "unknown", download_url)
