"""
Google Cloud Storage Client
Layer 6: Infrastructure - Data & State
Pure file operations, no business logic
"""
import asyncio
import base64
from typing import Optional, List, Dict, Any
from io import BytesIO

from google.cloud import storage
from google.cloud.storage import Bucket, Blob

from app.utils.logger import get_logger

logger = get_logger("gcs")


class GCSClient:
    """Google Cloud Storage client"""
    
    def __init__(
        self,
        bucket_name: str,
        credentials_path: Optional[str] = None,
        project_id: Optional[str] = None
    ):
        self.bucket_name = bucket_name
        self.credentials_path = credentials_path
        self.project_id = project_id
        self.client: Optional[storage.Client] = None
        self.bucket: Optional[Bucket] = None
        self._connected = False
    
    async def connect(self) -> None:
        """Initialize GCS client"""
        try:
            if self.credentials_path:
                self.client = storage.Client.from_service_account_json(
                    self.credentials_path,
                    project=self.project_id
                )
            else:
                self.client = storage.Client(project=self.project_id)
            
            self.bucket = self.client.bucket(self.bucket_name)
            
            # Test connection
            await self._test_connection()
            
            self._connected = True
            logger.info(f"✅ GCS connected: {self.bucket_name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to GCS: {e}")
            raise
    
    async def close(self) -> None:
        """Close GCS connection"""
        if self.client:
            self.client.close()
        self._connected = False
        logger.info("✅ GCS connection closed")
    
    async def _test_connection(self) -> None:
        """Test GCS connection"""
        if not self.bucket:
            raise Exception("GCS bucket not initialized")
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: self.bucket.exists())
    
    async def health_check(self) -> bool:
        """Check GCS health"""
        if not self._connected or not self.bucket:
            return False
        
        try:
            loop = asyncio.get_event_loop()
            exists = await loop.run_in_executor(None, lambda: self.bucket.exists())
            return exists
        except Exception as e:
            logger.error(f"GCS health check failed: {e}")
            return False
    
    # ==================== Upload Operations ====================
    
    async def upload_blob(
        self,
        blob_name: str,
        data: bytes,
        content_type: str = "application/octet-stream"
    ) -> bool:
        """Upload blob to GCS"""
        try:
            if not self.bucket:
                return False
            
            blob = self.bucket.blob(blob_name)
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: blob.upload_from_string(data, content_type=content_type)
            )
            
            logger.info(f"✅ Uploaded blob: {blob_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error uploading blob {blob_name}: {e}")
            return False
    
    async def upload_blob_from_base64(
        self,
        blob_name: str,
        base64_data: str,
        content_type: str = "application/octet-stream"
    ) -> bool:
        """Upload blob from base64 string"""
        try:
            # Remove data URL prefix if present
            if base64_data.startswith('data:'):
                base64_data = base64_data.split(',')[1]
            
            # Decode base64
            data = base64.b64decode(base64_data)
            
            return await self.upload_blob(blob_name, data, content_type)
            
        except Exception as e:
            logger.error(f"Error uploading base64 blob {blob_name}: {e}")
            return False
    
    async def upload_blob_from_file(
        self,
        blob_name: str,
        file_path: str,
        content_type: str = "application/octet-stream"
    ) -> bool:
        """Upload blob from file"""
        try:
            if not self.bucket:
                return False
            
            blob = self.bucket.blob(blob_name)
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: blob.upload_from_filename(file_path, content_type=content_type)
            )
            
            logger.info(f"✅ Uploaded file: {blob_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error uploading file {blob_name}: {e}")
            return False
    
    # ==================== Download Operations ====================
    
    async def download_blob(self, blob_name: str) -> Optional[bytes]:
        """Download blob from GCS"""
        try:
            if not self.bucket:
                return None
            
            blob = self.bucket.blob(blob_name)
            
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(
                None,
                lambda: blob.download_as_bytes()
            )
            
            return data
            
        except Exception as e:
            logger.error(f"Error downloading blob {blob_name}: {e}")
            return None
    
    async def download_blob_as_base64(self, blob_name: str) -> Optional[str]:
        """Download blob as base64 string"""
        try:
            data = await self.download_blob(blob_name)
            
            if data:
                return base64.b64encode(data).decode()
            
            return None
            
        except Exception as e:
            logger.error(f"Error downloading blob as base64 {blob_name}: {e}")
            return None
    
    async def download_blob_to_file(
        self,
        blob_name: str,
        file_path: str
    ) -> bool:
        """Download blob to file"""
        try:
            if not self.bucket:
                return False
            
            blob = self.bucket.blob(blob_name)
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: blob.download_to_filename(file_path)
            )
            
            logger.info(f"✅ Downloaded blob to file: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading blob to file {blob_name}: {e}")
            return False
    
    # ==================== Blob Operations ====================
    
    async def delete_blob(self, blob_name: str) -> bool:
        """Delete blob from GCS"""
        try:
            if not self.bucket:
                return False
            
            blob = self.bucket.blob(blob_name)
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: blob.delete())
            
            logger.info(f"✅ Deleted blob: {blob_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting blob {blob_name}: {e}")
            return False
    
    async def blob_exists(self, blob_name: str) -> bool:
        """Check if blob exists"""
        try:
            if not self.bucket:
                return False
            
            blob = self.bucket.blob(blob_name)
            
            loop = asyncio.get_event_loop()
            exists = await loop.run_in_executor(None, lambda: blob.exists())
            
            return exists
            
        except Exception as e:
            logger.error(f"Error checking blob existence {blob_name}: {e}")
            return False
    
    async def get_blob_metadata(self, blob_name: str) -> Optional[Dict[str, Any]]:
        """Get blob metadata"""
        try:
            if not self.bucket:
                return None
            
            blob = self.bucket.blob(blob_name)
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: blob.reload())
            
            return {
                'name': blob.name,
                'size': blob.size,
                'content_type': blob.content_type,
                'created': blob.time_created,
                'updated': blob.updated,
                'public_url': blob.public_url
            }
            
        except Exception as e:
            logger.error(f"Error getting blob metadata {blob_name}: {e}")
            return None
    
    async def get_blob_public_url(self, blob_name: str) -> Optional[str]:
        """Get public URL for blob"""
        try:
            if not self.bucket:
                return None
            
            blob = self.bucket.blob(blob_name)
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: blob.reload())
            
            return blob.public_url
            
        except Exception as e:
            logger.error(f"Error getting public URL for {blob_name}: {e}")
            return None
    
    # ==================== List Operations ====================
    
    async def list_blobs(
        self,
        prefix: Optional[str] = None,
        delimiter: Optional[str] = None,
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """List blobs in bucket"""
        try:
            if not self.bucket:
                return []
            
            loop = asyncio.get_event_loop()
            blobs = await loop.run_in_executor(
                None,
                lambda: list(self.bucket.list_blobs(
                    prefix=prefix,
                    delimiter=delimiter,
                    max_results=max_results
                ))
            )
            
            return [
                {
                    'name': blob.name,
                    'size': blob.size,
                    'content_type': blob.content_type,
                    'created': blob.time_created
                }
                for blob in blobs
            ]
            
        except Exception as e:
            logger.error(f"Error listing blobs: {e}")
            return []
    
    # ==================== Batch Operations ====================
    
    async def delete_blobs(self, blob_names: List[str]) -> bool:
        """Delete multiple blobs"""
        try:
            if not self.bucket:
                return False
            
            loop = asyncio.get_event_loop()
            
            for blob_name in blob_names:
                await loop.run_in_executor(
                    None,
                    lambda bn=blob_name: self.bucket.delete_blob(bn)
                )
            
            logger.info(f"✅ Deleted {len(blob_names)} blobs")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting blobs: {e}")
            return False
    
    # ==================== Bucket Operations ====================
    
    async def get_bucket_stats(self) -> Optional[Dict[str, Any]]:
        """Get bucket statistics"""
        try:
            if not self.bucket:
                return None
            
            loop = asyncio.get_event_loop()
            
            # Get bucket info
            await loop.run_in_executor(None, lambda: self.bucket.reload())
            
            # Count blobs and total size
            blobs = await loop.run_in_executor(
                None,
                lambda: list(self.bucket.list_blobs())
            )
            
            total_size = sum(blob.size or 0 for blob in blobs)
            
            return {
                'bucket_name': self.bucket.name,
                'total_blobs': len(blobs),
                'total_size': total_size,
                'location': self.bucket.location,
                'storage_class': self.bucket.storage_class
            }
            
        except Exception as e:
            logger.error(f"Error getting bucket stats: {e}")
            return None
