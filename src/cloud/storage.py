"""src/cloud/storage.py

Azure Blob Storage service for the Cloud Orchestrator (runs on server/laptop, NOT on Pi).

Responsibilities:
- Upload a new .eim model file to the designated model container.
- Generate a time-limited SAS URL so the Pi can download without Azure credentials.

Usage (by Teammate A's pipeline or the orchestrator script):
    svc = BlobStorageService(connection_string="DefaultEndpointsProtocol=...")
    url = svc.upload_model_and_get_sas_url("./model_v2.eim", "v2")
    # Pass url to IoTHubService to notify the Pi
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# Container used for model binaries — separate from the fish-images container!
MODEL_CONTAINER = "edge-models"
SAS_EXPIRY_HOURS = 2  # Pi must download within this window


class BlobStorageService:
    """Uploads .eim model files and generates SAS download URLs."""

    def __init__(self, connection_string: str) -> None:
        if not connection_string:
            raise ValueError("BLOB_CONNECTION_STRING is required.")
        try:
            from azure.storage.blob import (
                BlobServiceClient,
                BlobSasPermissions,
                generate_blob_sas,
            )
        except ImportError as exc:
            raise RuntimeError(
                "azure-storage-blob not installed. Run: pip install azure-storage-blob"
            ) from exc

        self._BlobSasPermissions = BlobSasPermissions
        self._generate_blob_sas = generate_blob_sas
        self._client = BlobServiceClient.from_connection_string(connection_string)
        self._ensure_container()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def upload_model_and_get_sas_url(
        self,
        local_path: str,
        version: str,
        blob_name: str | None = None,
    ) -> str:
        """Upload *local_path* to Blob Storage and return a SAS download URL.

        Parameters
        ----------
        local_path : str
            Path to the .eim file on this machine.
        version : str
            Version label, e.g. "v2.0.1". Used to build the blob name.
        blob_name : str, optional
            Override the blob name. Defaults to "model_<version>.eim".

        Returns
        -------
        str
            A time-limited SAS URL the Pi can use to download the model.
        """
        blob_name = blob_name or f"model_{version}.eim"
        local_file = Path(local_path)

        logger.info("[BlobStorage] Uploading %s → %s/%s", local_file.name, MODEL_CONTAINER, blob_name)
        blob_client = self._client.get_blob_client(container=MODEL_CONTAINER, blob=blob_name)

        with open(local_file, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)

        file_size_kb = local_file.stat().st_size // 1024
        logger.info("[BlobStorage] Uploaded %d KB. Generating SAS URL...", file_size_kb)

        sas_url = self._generate_sas_url(blob_name)
        logger.info("[BlobStorage] SAS URL ready (expires in %dh)", SAS_EXPIRY_HOURS)
        return sas_url

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _ensure_container(self) -> None:
        """Create MODEL_CONTAINER if it doesn't exist yet."""
        container_client = self._client.get_container_client(MODEL_CONTAINER)
        try:
            container_client.create_container()
            logger.info("[BlobStorage] Created container '%s'", MODEL_CONTAINER)
        except Exception:
            pass  # Already exists

    def _generate_sas_url(self, blob_name: str) -> str:
        """Generate a read-only SAS URL valid for SAS_EXPIRY_HOURS."""
        account_name = self._client.account_name
        account_key = self._client.credential.account_key

        expiry = datetime.now(timezone.utc) + timedelta(hours=SAS_EXPIRY_HOURS)

        sas_token = self._generate_blob_sas(
            account_name=account_name,
            container_name=MODEL_CONTAINER,
            blob_name=blob_name,
            account_key=account_key,
            permission=self._BlobSasPermissions(read=True),
            expiry=expiry,
        )

        return (
            f"https://{account_name}.blob.core.windows.net"
            f"/{MODEL_CONTAINER}/{blob_name}?{sas_token}"
        )
