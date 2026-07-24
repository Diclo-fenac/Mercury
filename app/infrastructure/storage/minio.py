"""
MinIO Storage Client
Layer 6: Infrastructure - Data & State
S3-compliant file operations using MinIO SDK
"""
import asyncio
import base64
import io
from typing import Optional

from minio import Minio

from app.utils.logger import get_logger

logger = get_logger("minio_storage")


class MinIOStorageClient:
    """MinIO (S3-compatible) file storage client"""

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        secure: bool = False
    ):
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket_name = bucket_name
        self.secure = secure
        self.client: Optional[Minio] = None
        self._connected = False

    async def connect(self) -> None:
        """Initialize MinIO client and ensure bucket exists"""
        try:
            loop = asyncio.get_event_loop()
            
            # Initialize the MinIO client in the executor to avoid blocking the main event loop
            self.client = await loop.run_in_executor(
                None,
                lambda: Minio(
                    endpoint=self.endpoint,
                    access_key=self.access_key,
                    secret_key=self.secret_key,
                    secure=self.secure
                )
            )
            
            # Check/create bucket
            bucket_exists = await loop.run_in_executor(
                None,
                lambda: self.client.bucket_exists(self.bucket_name)
            )
            
            if not bucket_exists:
                await loop.run_in_executor(
                    None,
                    lambda: self.client.make_bucket(self.bucket_name)
                )
                logger.info(f"📁 Created MinIO bucket: {self.bucket_name}")
            
            self._connected = True
            logger.info(f"✅ MinIO storage connected: {self.endpoint}/{self.bucket_name}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to MinIO at {self.endpoint}: {e}")
            raise

    async def close(self) -> None:
        """Close storage client (noop)"""
        self._connected = False
        logger.info("✅ MinIO connection closed")

    async def health_check(self) -> bool:
        """Verify connection to MinIO by checking bucket existence"""
        if not self._connected or not self.client:
            return False
        try:
            loop = asyncio.get_event_loop()
            exists = await loop.run_in_executor(
                None,
                lambda: self.client.bucket_exists(self.bucket_name)
            )
            return exists
        except Exception as e:
            logger.error(f"MinIO health check failed: {e}")
            return False

    async def upload_blob(
        self,
        blob_name: str,
        data: bytes,
        content_type: str = "application/octet-stream"
    ) -> bool:
        """Upload binary file to MinIO bucket"""
        try:
            if not self.client:
                return False
            
            data_stream = io.BytesIO(data)
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.client.put_object(
                    bucket_name=self.bucket_name,
                    object_name=blob_name,
                    data=data_stream,
                    length=len(data),
                    content_type=content_type
                )
            )
            logger.info("Uploaded file to MinIO")
            return True
        except Exception as e:
            logger.error(f"Error uploading file to MinIO {blob_name}: {e}")
            return False

    async def upload_blob_from_base64(
        self,
        blob_name: str,
        base64_data: str,
        content_type: str = "application/octet-stream"
    ) -> bool:
        """Upload file to MinIO from a base64 string"""
        try:
            if base64_data.startswith('data:'):
                base64_data = base64_data.split(',')[1]
            data = base64.b64decode(base64_data)
            return await self.upload_blob(blob_name, data, content_type)
        except Exception as e:
            logger.error(f"Error uploading base64 file to MinIO {blob_name}: {e}")
            return False

    async def download_blob(self, blob_name: str) -> Optional[bytes]:
        """Download file from MinIO bucket"""
        try:
            if not self.client:
                return None
            
            loop = asyncio.get_event_loop()
            
            response = await loop.run_in_executor(
                None,
                lambda: self.client.get_object(self.bucket_name, blob_name)
            )
            try:
                data = response.read()
            finally:
                response.close()
                response.release_conn()
            
            return data
        except Exception as e:
            logger.error(f"Error downloading file from MinIO {blob_name}: {e}")
            return None

    async def get_blob_public_url(self, blob_name: str) -> Optional[str]:
        """Get public API URL for local image serving"""
        image_id = blob_name.rsplit("/", 1)[-1].removesuffix(".jpg")
        return f"/api/v1/images/{image_id}/raw"
