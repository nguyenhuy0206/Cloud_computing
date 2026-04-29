"""src/cloud/iot_hub_service.py

Azure IoT Hub SERVICE-side client (runs on server/laptop, NOT on Pi).

Responsibilities:
- Update the Device Twin "desired" properties to notify the Pi of a new model.
- Read "reported" properties to verify the Pi successfully applied the update.

This is the CLOUD SIDE of Device Twin — it's a different SDK from what the Pi uses.
Pi uses: azure-iot-device (IoTHubDeviceClient)
Cloud uses: azure-iot-hub (IoTHubRegistryManager)
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

TWIN_MODEL_UPDATE_KEY = "modelUpdate"  # Must match device_service.py on the Pi


class IoTHubService:
    """Cloud-side Device Twin manager.

    Usage (by Teammate A's orchestrator after uploading model):
        svc = IoTHubService(hub_connection_string="HostName=...")
        svc.notify_device_of_new_model("esp32", "v2.0.1", sas_url)
    """

    def __init__(self, hub_connection_string: str) -> None:
        if not hub_connection_string:
            raise ValueError("IOT_HUB_SERVICE_CONNECTION_STRING is required.")
        try:
            from azure.iot.hub import IoTHubRegistryManager
        except ImportError as exc:
            raise RuntimeError(
                "azure-iot-hub not installed. Run: pip install azure-iot-hub"
            ) from exc

        self._registry = IoTHubRegistryManager(hub_connection_string)
        logger.info("[IoTHubService] Connected to IoT Hub registry.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def notify_device_of_new_model(
        self,
        device_id: str,
        version: str,
        download_url: str,
    ) -> None:
        """Update Device Twin desired properties to trigger OTA on the Pi.

        The Pi's DeviceService (device_service.py) will receive this patch
        automatically via the Twin patch listener and kick off the download.
        """
        twin_patch = {
            "properties": {
                "desired": {
                    TWIN_MODEL_UPDATE_KEY: {
                        "version": version,
                        "downloadUrl": download_url,
                    }
                }
            }
        }

        logger.info(
            "[IoTHubService] Patching Device Twin for '%s' → version=%s",
            device_id,
            version,
        )
        # etag="*" means update regardless of current etag (force patch)
        self._registry.update_twin(device_id, twin_patch, "*")
        logger.info("[IoTHubService] Device Twin patch sent successfully.")

    def get_reported_status(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Read what the Pi last reported about its current model (for verification)."""
        twin = self._registry.get_twin(device_id)
        reported = twin.properties.reported
        return reported.get("currentModel") if reported else None

    def wait_for_device_confirmation(
        self,
        device_id: str,
        expected_version: str,
        timeout_sec: int = 120,
        poll_interval_sec: int = 5,
    ) -> bool:
        """Poll reported properties until the Pi confirms the new model version.

        Returns True if confirmed within timeout, False otherwise.
        """
        logger.info(
            "[IoTHubService] Waiting for '%s' to confirm model %s ...",
            device_id,
            expected_version,
        )
        deadline = time.time() + timeout_sec
        while time.time() < deadline:
            status = self.get_reported_status(device_id)
            if status:
                reported_ver = status.get("version")
                reported_st = status.get("status")
                logger.info(
                    "[IoTHubService] Device reported: version=%s status=%s",
                    reported_ver,
                    reported_st,
                )
                if reported_ver == expected_version and reported_st == "Success":
                    logger.info("[IoTHubService] Device confirmed update!")
                    return True
            time.sleep(poll_interval_sec)

        logger.warning(
            "[IoTHubService] Timeout: device did not confirm within %ds.", timeout_sec
        )
        return False
