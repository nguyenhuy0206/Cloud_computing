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

import base64
import hashlib
import hmac
import logging
import time
import urllib.parse
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)

TWIN_MODEL_UPDATE_KEY = "modelUpdate"  # Must match device_service.py on the Pi


class IoTHubService:
    """Cloud-side Device Twin manager using Azure REST API.

    Usage (by Teammate A's orchestrator after uploading model):
        svc = IoTHubService(hub_connection_string="HostName=...;SharedAccessKeyName=iothubowner;...")
        svc.notify_device_of_new_model("piedge", "v2.0.1", sas_url)
    """

    def __init__(self, hub_connection_string: str) -> None:
        if not hub_connection_string:
            raise ValueError("IOT_HUB_SERVICE_CONNECTION_STRING is required.")
        
        # Parse connection string
        parts = dict(p.split("=", 1) for p in hub_connection_string.split(";") if "=" in p)
        self.hostname = parts.get("HostName")
        self.key_name = parts.get("SharedAccessKeyName")
        self.key = parts.get("SharedAccessKey")
        
        if not (self.hostname and self.key_name and self.key):
            raise ValueError(
                "Invalid Connection String. Make sure it contains HostName, SharedAccessKeyName, and SharedAccessKey."
            )
            
        logger.info("[IoTHubService] Initialized REST API client for IoT Hub (bypassed uamqp).")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _generate_sas_token(self, expiry_seconds: int = 3600) -> str:
        """Generate a SAS token to authenticate REST API requests."""
        ttl = int(time.time()) + expiry_seconds
        uri = urllib.parse.quote_plus(self.hostname)
        sign_key = base64.b64decode(self.key)
        to_sign = f"{uri}\n{ttl}".encode("utf-8")
        signature = base64.b64encode(
            hmac.new(sign_key, to_sign, hashlib.sha256).digest()
        ).decode("utf-8")
        
        return f"SharedAccessSignature sr={uri}&sig={urllib.parse.quote_plus(signature)}&se={ttl}&skn={self.key_name}"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def notify_device_of_new_model(
        self,
        device_id: str,
        version: str,
        download_url: str,
    ) -> None:
        """Update Device Twin desired properties to trigger OTA on the Pi."""
        token = self._generate_sas_token()
        url = f"https://{self.hostname}/twins/{device_id}?api-version=2020-03-13"
        
        headers = {
            "Authorization": token,
            "Content-Type": "application/json"
        }
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
        resp = requests.patch(url, headers=headers, json=twin_patch, timeout=10)
        
        if resp.status_code >= 400:
            logger.error("[IoTHubService] Patch failed: %s", resp.text)
        resp.raise_for_status()
        
        logger.info("[IoTHubService] Device Twin patch sent successfully via REST.")

    def get_reported_status(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Read what the Pi last reported about its current model (for verification)."""
        token = self._generate_sas_token()
        url = f"https://{self.hostname}/twins/{device_id}?api-version=2020-03-13"
        headers = {"Authorization": token}
        
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        
        data = resp.json()
        reported = data.get("properties", {}).get("reported", {})
        return reported.get("currentModel")

    def wait_for_device_confirmation(
        self,
        device_id: str,
        expected_version: str,
        timeout_sec: int = 120,
        poll_interval_sec: int = 5,
    ) -> bool:
        """Poll reported properties until the Pi confirms the new model version."""
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
