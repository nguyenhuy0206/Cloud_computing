"""scripts/test_ota.py

Quick local test for the OTA pipeline on Mac before deploying to Pi.

What this script does:
  1. Connects to Azure IoT Hub using the real Device Connection String.
  2. Listens for Device Twin patches.
  3. If a modelUpdate is detected, downloads the file and logs the result.

How to trigger the test (no Pi needed):
  - Go to Azure Portal → IoT Hub → Devices → esp32 → Device Twin
  - Add this to "desired" and click Save:
      {
        "modelUpdate": {
          "version": "v1.0-test",
          "downloadUrl": "https://datasetfish.blob.core.windows.net/fish-images/<filename>?<sas_token>"
        }
      }
  - Watch the console output here.

Run:
    python -m scripts.test_ota
"""
import logging
import os
import sys
import time

# Make sure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.edge.ota import OTAManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------ #
#  CONFIG — paste from config.txt                                     #
# ------------------------------------------------------------------ #
DEVICE_CONNECTION_STRING = (
    "HostName=<HOSTNAME>"
    "DeviceId=<DEVICE>"
    "SharedAccessKey=<KEY>"
)

# Where to save the downloaded model locally (can be any path while testing)
MODEL_PATH = "./downloaded_model_test.eim"
# ------------------------------------------------------------------ #


def on_model_swapped():
    """Called after a successful model swap. In production: restart inference."""
    logger.info("[TEST] on_model_swapped() called — in production this restarts inference.")


def main():
    logger.info("=" * 60)
    logger.info("OTA Test Script — running on LOCAL MACHINE")
    logger.info("Connecting to IoT Hub as device: piedge")
    logger.info("=" * 60)

    ota = OTAManager(
        connection_string=DEVICE_CONNECTION_STRING,
        model_path=MODEL_PATH,
        on_model_swapped=on_model_swapped,
    )

    try:
        ota.start()
        logger.info("Listening... Press Ctrl+C to stop.")
        logger.info("")
        logger.info("ACTION REQUIRED:")
        logger.info("  Go to Azure Portal → IoT Hub → Devices → esp32 → Device Twin")
        logger.info('  Add/update "modelUpdate" in desired properties and Save.')
        logger.info("")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Stopping...")
    finally:
        ota.stop()


if __name__ == "__main__":
    main()
