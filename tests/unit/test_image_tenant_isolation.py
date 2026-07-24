import base64

import pytest

from app.addons.image.processor import ImageProcessor
from app.orchestrators.image_orchestrator import ImageOrchestrator


class FakeCache:
    def __init__(self):
        self.values = {}

    async def set_json(self, key, value, ttl):
        self.values[key] = value
        return True

    async def get_json(self, key):
        return self.values.get(key)


class FakeStorage:
    def __init__(self):
        self.blobs = {}

    async def upload_blob_from_base64(self, blob_name, value, content_type):
        self.blobs[blob_name] = (value, content_type)
        return True


class FakeVisionProvider:
    async def detect_barcode(self, image_data):
        return {"is_barcode": False}

    async def analyze_product_features(self, image_data, user_context):
        return {"success": True, "description": "test product"}


@pytest.mark.asyncio
async def test_uploaded_image_metadata_and_blob_are_tenant_scoped():
    cache = FakeCache()
    storage = FakeStorage()
    processor = ImageProcessor(storage, cache, FakeVisionProvider())
    orchestrator = ImageOrchestrator(processor, search_service=None)
    image = "data:image/jpeg;base64," + base64.b64encode(b"\xff\xd8\xff").decode()

    uploaded = await orchestrator.process_image_upload(image, "tenant-a", "user-1")

    assert uploaded["success"] is True
    image_id = uploaded["image_id"]
    assert "tenant-a" not in next(iter(storage.blobs))
    assert next(iter(storage.blobs)).startswith("images/")

    owner = await orchestrator.get_image_metadata("tenant-a", image_id, "user-1")
    other_tenant = await orchestrator.get_image_metadata("tenant-b", image_id, "user-1")
    other_user = await orchestrator.get_image_metadata("tenant-a", image_id, "user-2")

    assert owner["success"] is True
    assert owner["image"]["blob_name"] in storage.blobs
    assert other_tenant == {"success": False, "error": "not_found"}
    assert other_user == {"success": False, "error": "access_denied"}
