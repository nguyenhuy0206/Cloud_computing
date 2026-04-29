"""ota.py — Over-The-Air Model Update Orchestrator

Ties together DeviceService (IoT Hub listener) and ModelManager (download/swap).
Acts as the single entry point for OTA logic on the Edge device.

Usage (from pipeline.py or main.py):
    ota = OTAManager(connection_string="...", model_path="./model.eim")
    ota.start()          # non-blocking, runs listener in background
    ...
    ota.stop()
"""
from __future__ import annotations

import logging
import threading

from src.edge.device_service import DeviceService
from src.edge.model_manager import ModelManager

logger = logging.getLogger(__name__)


class OTAManager:
    """Orchestrates the full OTA model-update flow on the Edge device.

    Flow triggered when Cloud updates Device Twin:
      1. DeviceService receives Twin patch from IoT Hub.
      2. OTAManager._handle_model_update() is called.
      3. ModelManager downloads new .eim and swaps it in.
      4. DeviceService reports success/failure back to Cloud.
      5. (Optional) inference engine is restarted by the caller via callback.
    """

    def __init__(
        self,
        connection_string: str,
        model_path: str = "./model.eim",
        on_model_swapped=None,  # Optional[Callable[[], None]]
    ) -> None:
        """
        Parameters
        ----------
        connection_string
            IoT Hub Device Connection String (from config.txt / .env).
        model_path
            Local path where the .eim model is stored.
        on_model_swapped
            Optional callback invoked after a successful model swap,
            e.g. to restart the inference engine.
        """
        self._model_manager = ModelManager(model_path)
        self._device_service = DeviceService(
            connection_string=connection_string,
            on_model_update=self._handle_model_update,
        )
        self._on_model_swapped = on_model_swapped
        self._lock = threading.Lock()  # prevent concurrent OTA runs

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Connect to IoT Hub and begin listening for model updates."""
        self._device_service.start()
        logger.info("[OTAManager] Started — waiting for model update commands.")

    def stop(self) -> None:
        """Gracefully disconnect from IoT Hub."""
        self._device_service.stop()
        logger.info("[OTAManager] Stopped.")

    # ------------------------------------------------------------------
    # Internal callback (called by DeviceService)
    # ------------------------------------------------------------------

    def _handle_model_update(self, version: str, download_url: str) -> None:
        """Full OTA sequence executed when a new model is available."""
        # Use a lock so that two rapid Twin patches don't run OTA simultaneously.
        if not self._lock.acquire(blocking=False):
            logger.warning("[OTAManager] OTA already in progress — ignoring duplicate request.")
            return

        try:
            logger.info("[OTAManager] Starting OTA update to version: %s", version)

            # Step 1: Download new model and swap with current
            success = self._model_manager.download_and_swap(download_url, version)

            # Step 2: Report result back to Cloud (visible in Azure Portal Twin)
            status = "Success" if success else "Failed"
            self._device_service.report_status(version, status)

            if success:
                logger.info("[OTAManager] OTA complete. Model is now at version: %s", version)
                # Step 3: Notify caller to restart inference engine (if hooked up)
                if self._on_model_swapped:
                    self._on_model_swapped()
            else:
                logger.error("[OTAManager] OTA failed. Previous model retained (backup restored).")

        finally:
            self._lock.release()
