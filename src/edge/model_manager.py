"""model_manager.py

Handles downloading, backing up, and swapping the Edge Impulse .eim model file.
Designed to run on both local Mac (for testing) and Raspberry Pi (production).
"""
from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path

import requests

logger = logging.getLogger(__name__)


class ModelManager:
    """Manages the lifecycle of the local .eim model file.

    Responsibilities:
    - Download a new model from a SAS URL (Azure Blob Storage).
    - Back up the current model before replacing it.
    - Grant execute permission (chmod +x) after download.
    - Restore backup if something goes wrong.
    """

    def __init__(self, model_path: str = "./model.eim") -> None:
        self.model_path = Path(model_path)
        self.backup_path = self.model_path.with_suffix(".eim.bak")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def download_and_swap(self, download_url: str, version: str) -> bool:
        """Download a new model from *download_url* and replace the current one.

        Returns True on success, False on any failure (backup is restored).
        """
        tmp_path = self.model_path.with_suffix(".eim.tmp")
        logger.info("[ModelManager] Downloading model %s ...", version)

        try:
            self._download(download_url, tmp_path)
        except Exception as exc:
            logger.error("[ModelManager] Download failed: %s", exc)
            tmp_path.unlink(missing_ok=True)
            return False

        # Backup current model if it exists
        self._backup()

        try:
            # Replace current model with newly downloaded file
            shutil.move(str(tmp_path), str(self.model_path))

            # CRITICAL on Linux/Pi: .eim is an executable binary.
            # Python's requests saves it without execute permission — we must set it.
            self._grant_execute()
            logger.info("[ModelManager] Model swapped successfully -> %s", self.model_path)
            return True

        except Exception as exc:
            logger.error("[ModelManager] Swap failed, restoring backup: %s", exc)
            self._restore_backup()
            tmp_path.unlink(missing_ok=True)
            return False

    def get_current_version_label(self) -> str:
        """Return a human-readable label for the current model file."""
        if self.model_path.exists():
            size_kb = self.model_path.stat().st_size // 1024
            return f"exists ({size_kb} KB)"
        return "not found"

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _download(self, url: str, dest: Path) -> None:
        """Stream-download *url* to *dest*. Raises on HTTP error."""
        # NOTE: The SAS URL already contains the authentication token.
        # Pi does NOT need an Azure account to download — just this URL.
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()

        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        downloaded_kb = dest.stat().st_size // 1024
        logger.info("[ModelManager] Downloaded %d KB -> %s", downloaded_kb, dest)

    def _backup(self) -> None:
        if self.model_path.exists():
            shutil.copy2(str(self.model_path), str(self.backup_path))
            logger.info("[ModelManager] Backed up current model to %s", self.backup_path)

    def _restore_backup(self) -> None:
        if self.backup_path.exists():
            shutil.move(str(self.backup_path), str(self.model_path))
            logger.info("[ModelManager] Restored model from backup.")
        else:
            logger.warning("[ModelManager] No backup to restore.")

    def _grant_execute(self) -> None:
        """Set chmod 755 on the model file (required on Linux/Pi)."""
        current_mode = self.model_path.stat().st_mode
        self.model_path.chmod(current_mode | 0o111)  # add +x for owner/group/other
        logger.info("[ModelManager] chmod +x applied to %s", self.model_path)
