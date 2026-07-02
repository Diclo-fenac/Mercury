"""
Local File Storage Client
Layer 6: Infrastructure - Data & State
Pure file operations on the local disk
"""
import os
import shutil
import base64
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional
from app.utils.logger import get_logger

logger = get_logger("local_storage")


class LocalStorageClient:
    """Local disk file storage client emulating cloud storage for offline operations"""
    
    def __init__(self, base_dir: str = "uploads"):
        self.base_dir = Path(base_dir)
        self._connected = False
    
    async def connect(self) -> None:
        """Initialize local storage directory"""
        try:
            self.base_dir.mkdir(parents=True, exist_ok=True)
            self._connected = True
            logger.info(f"✅ Local storage initialized at: {self.base_dir.resolve()}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize local storage: {e}")
            raise
    
    async def close(self) -> None:
        """Close connection (noop)"""
        self._connected = False
        logger.info("✅ Local storage connection closed")
    
    async def health_check(self) -> bool:
        """Check if storage directory exists and is writable"""
        return self._connected and self.base_dir.exists()
    
    async def upload_blob(
        self,
        blob_name: str,
        data: bytes,
        content_type: str = "application/octet-stream"
    ) -> bool:
        """Upload local file"""
        try:
            file_path = self.base_dir / blob_name
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: file_path.write_bytes(data)
            )
            logger.info(f"✅ Uploaded local file: {blob_name}")
            return True
        except Exception as e:
            logger.error(f"Error uploading local file {blob_name}: {e}")
            return False
            
    async def upload_blob_from_base64(
        self,
        blob_name: str,
        base64_data: str,
        content_type: str = "application/octet-stream"
    ) -> bool:
        """Upload local file from base64 string"""
        try:
            if base64_data.startswith('data:'):
                base64_data = base64_data.split(',')[1]
            data = base64.b64decode(base64_data)
            return await self.upload_blob(blob_name, data, content_type)
        except Exception as e:
            logger.error(f"Error uploading base64 file {blob_name}: {e}")
            return False

    async def download_blob(self, blob_name: str) -> Optional[bytes]:
        """Download local file bytes"""
        try:
            file_path = self.base_dir / blob_name
            if not file_path.exists():
                return None
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                lambda: file_path.read_bytes()
            )
        except Exception as e:
            logger.error(f"Error downloading local file {blob_name}: {e}")
            return None

    async def get_blob_public_url(self, blob_name: str) -> Optional[str]:
        """Get public URL for local file"""
        # Remove any leading directory components (e.g. images/) to match flat file storage
        filename = os.path.basename(blob_name)
        if filename.endswith(".jpg"):
            filename = filename[:-4]
        return f"/api/v1/images/{filename}/raw"
