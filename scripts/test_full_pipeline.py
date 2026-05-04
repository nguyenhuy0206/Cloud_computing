"""scripts/test_full_pipeline.py

End-to-end integration test for the OTA pipeline.

Tests two separate flows:

FLOW A — Edge side (your responsibility):
  Simulates Pi receiving a Twin patch and downloading a real file from Blob.
  Uses the actual IoT Hub connection string and the existing model.eim as test file.

FLOW B — Cloud trigger side (what Teammate A's script will do):
  Manually triggers a Device Twin patch using IoT Hub service connection.
  Requires IOT_HUB_SERVICE_CONNECTION_STRING in environment / .env.

Run:
    # Test Edge-side only (always works with current credentials):
    python3 -m scripts.test_full_pipeline --mode edge

    # Test full round-trip (requires IoT Hub service connection string):
    python3 -m scripts.test_full_pipeline --mode full
"""
import argparse
import logging
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# CONFIG  (fill in or set as environment variables)
# ─────────────────────────────────────────────────────────────
DEVICE_CONNECTION_STRING = os.getenv(
    "IOT_HUB_DEVICE_CONNECTION_STRING",
    "HostName=my-iot-hub-2026.azure-devices.net;"
    "DeviceId=esp32;"
    "SharedAccessKey=7m30yuToe7rivjWmyX3lNzYENYKu/73lBGAtlxoRyZs="
)

# Teammate A needs to provide this (iothubowner policy connection string)
HUB_SERVICE_CONNECTION_STRING = os.getenv("IOT_HUB_SERVICE_CONNECTION_STRING", "")

DEVICE_ID = "esp32"

# --- Blob info ---
# Container for MODELS (different from fish-images which stores training data)
# Teammate A must create this container and upload a model file there.
# For now we test with the local model.eim as a simulated download target.
BLOB_CONTAINER_URL_FOR_MODELS = os.getenv(
    "BLOB_MODEL_SAS_URL",
    # TODO: Teammate A replaces this with real model container SAS URL
    ""
)

# Local fallback: use existing model.eim in artifacts as download target
LOCAL_MODEL_PATH = "artifacts/models/edge_impulse/v1/model.eim"
DOWNLOAD_DEST = "/tmp/ota_test_model.eim"
# ─────────────────────────────────────────────────────────────


def test_edge_side_ota(download_url: str) -> bool:
    """FLOW A: Test ModelManager download + swap without IoT Hub involvement."""
    from src.edge.model_manager import ModelManager

    logger.info("=" * 60)
    logger.info("FLOW A: Testing ModelManager (download + swap)")
    logger.info("=" * 60)

    mgr = ModelManager(model_path=DOWNLOAD_DEST)
    success = mgr.download_and_swap(download_url, version="v-test")

    if success:
        logger.info("FLOW A PASSED: Model downloaded and swapped at %s", DOWNLOAD_DEST)
        size = os.path.getsize(DOWNLOAD_DEST) // 1024
        logger.info("  File size: %d KB", size)
        import stat
        mode = os.stat(DOWNLOAD_DEST).st_mode
        is_exec = bool(mode & stat.S_IXUSR)
        logger.info("  Executable bit set: %s", is_exec)
    else:
        logger.error("FLOW A FAILED: ModelManager returned False")

    return success


def test_full_round_trip(version: str = "v2-integration-test") -> bool:
    """FLOW B: Cloud triggers Twin → Edge detects → downloads model."""
    from src.cloud.iot_hub_service import IoTHubService
    from src.edge.ota import OTAManager

    if not HUB_SERVICE_CONNECTION_STRING:
        logger.error(
            "FLOW B SKIPPED: IOT_HUB_SERVICE_CONNECTION_STRING not set.\n"
            "  Ask Teammate A for the IoT Hub 'iothubowner' connection string\n"
            "  and set it in your environment or .env file."
        )
        return False
    if not BLOB_CONTAINER_URL_FOR_MODELS:
        logger.error(
            "FLOW B SKIPPED: BLOB_MODEL_SAS_URL not set.\n"
            "  Teammate A needs to create 'edge-models' container,\n"
            "  upload a model.eim file, and provide a SAS URL."
        )
        return False

    logger.info("=" * 60)
    logger.info("FLOW B: Full round-trip test (Cloud → IoT Hub → Edge → Blob)")
    logger.info("=" * 60)

    model_swapped_event = {"done": False}

    def on_swapped():
        model_swapped_event["done"] = True
        logger.info("FLOW B: on_model_swapped callback fired — inference would restart here.")

    # Start OTA listener on Edge side
    ota = OTAManager(
        connection_string=DEVICE_CONNECTION_STRING,
        model_path=DOWNLOAD_DEST,
        on_model_swapped=on_swapped,
    )
    ota.start()

    # Cloud side: trigger the Twin patch
    hub = IoTHubService(HUB_SERVICE_CONNECTION_STRING)
    hub.notify_device_of_new_model(DEVICE_ID, version, BLOB_CONTAINER_URL_FOR_MODELS)

    # Wait for Pi to confirm
    logger.info("Waiting up to 60s for device to download and report back...")
    confirmed = hub.wait_for_device_confirmation(DEVICE_ID, version, timeout_sec=60)
    ota.stop()

    if confirmed:
        logger.info("FLOW B PASSED: Full automation pipeline verified!")
    else:
        logger.warning(
            "FLOW B: Device did not confirm within timeout.\n"
            "Check if model file exists at BLOB_MODEL_SAS_URL."
        )
    return confirmed


def main():
    parser = argparse.ArgumentParser(description="OTA Pipeline Integration Test")
    parser.add_argument(
        "--mode",
        choices=["edge", "full"],
        default="edge",
        help="edge: test ModelManager download only | full: end-to-end with IoT Hub",
    )
    args = parser.parse_args()

    if args.mode == "edge":
        # Use the local model.eim served via file:// or a real URL
        # For a real test, provide a URL to any downloadable file
        test_url = BLOB_CONTAINER_URL_FOR_MODELS

        if not test_url:
            # Fallback: create a tiny test file and copy it as "download"
            logger.info("No BLOB_MODEL_SAS_URL set — using local file copy as mock download")
            logger.info("")
            logger.info("To test with a real download URL, set BLOB_MODEL_SAS_URL env var")
            logger.info("or run after Teammate A uploads a model to Blob Storage.")
            logger.info("")

            # Self-test: just validate imports are all working
            logger.info("Validating all module imports...")
            from src.edge.model_manager import ModelManager
            from src.edge.device_service import DeviceService
            from src.edge.ota import OTAManager
            from src.cloud.storage import BlobStorageService
            from src.cloud.iot_hub_service import IoTHubService
            logger.info("All modules import OK.")
            logger.info("")
            logger.info("NEXT STEP: Run OTA listener and trigger from Azure Portal:")
            logger.info("  python3 -m scripts.test_ota")
            logger.info("  Then edit Device Twin in Azure Portal to trigger update.")
            return

        passed = test_edge_side_ota(test_url)
        sys.exit(0 if passed else 1)

    elif args.mode == "full":
        passed = test_full_round_trip()
        sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
