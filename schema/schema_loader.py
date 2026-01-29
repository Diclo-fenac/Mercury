"""
Firestore Schema Loader
Loads cached schema information without connecting to Firestore
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional, List


class FirestoreSchema:
    """Cached Firestore schema information"""
    
    def __init__(self, schema_path: str = None):
        if schema_path is None:
            schema_path = Path(__file__).parent / "firestore_schema.json"
        
        with open(schema_path, 'r') as f:
            self._schema = json.load(f)
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Get schema metadata"""
        return self._schema.get("metadata", {})
    
    @property
    def collections(self) -> List[str]:
        """Get list of collection names"""
        return list(self._schema.get("collections", {}).keys())
    
    def get_collection_schema(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """Get schema for a specific collection"""
        return self._schema.get("collections", {}).get(collection_name)
    
    def get_field_schema(self, collection_name: str, field_name: str) -> Optional[Dict[str, Any]]:
        """Get schema for a specific field"""
        collection = self.get_collection_schema(collection_name)
        if not collection or "fields" not in collection:
            return None
        return collection["fields"].get(field_name)
    
    def is_field_required(self, collection_name: str, field_name: str) -> bool:
        """Check if a field is required"""
        field_schema = self.get_field_schema(collection_name, field_name)
        return field_schema and field_schema.get("status") == "required"
    
    def get_relationships(self) -> List[Dict[str, Any]]:
        """Get all detected relationships"""
        return self._schema.get("relationships", [])
    
    def get_foreign_keys(self, collection_name: str) -> List[str]:
        """Get foreign key fields for a collection"""
        fks = []
        for rel in self.get_relationships():
            if (rel.get("type") == "foreign_key" and 
                rel.get("from_collection") == collection_name):
                fks.append(rel.get("from_field"))
        return fks
    
    def validate_document(self, collection_name: str, document: Dict[str, Any]) -> List[str]:
        """Validate a document against the schema"""
        errors = []
        collection_schema = self.get_collection_schema(collection_name)
        
        if not collection_schema or "fields" not in collection_schema:
            return [f"No schema found for collection {collection_name}"]
        
        # Check required fields
        for field_name, field_schema in collection_schema["fields"].items():
            if field_schema.get("status") == "required":
                if field_name not in document:
                    errors.append(f"Required field missing: {field_name}")
                elif document[field_name] is None and not field_schema.get("nullable"):
                    errors.append(f"Required field is null: {field_name}")
        
        return errors


# Global instance
schema = FirestoreSchema()
