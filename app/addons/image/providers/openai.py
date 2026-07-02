from typing import Any, Dict, Optional
import json
import base64
from datetime import datetime

from app.addons.image.provider import VisionProvider
from app.utils.logger import get_logger

logger = get_logger("vision_openai")

class OpenAIVisionProvider(VisionProvider):
    def __init__(self, api_key: str, api_base: Optional[str] = None, model_name: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.api_base = api_base
        self.model_name = model_name
        self.client = None
        self.mock_mode = False

    async def initialize(self) -> None:
        try:
            if not self.api_key or self.api_key in ["your-openai-api-key", "dummy", "mock", ""] or not self.api_key.strip():
                logger.warning("OpenAI API key not found, running in mock mode")
                self.mock_mode = True
                return
            
            import openai
            self.client = openai.AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.api_base
            )
            self.mock_mode = False
            logger.info(f"OpenAI vision client initialized (model: {self.model_name})")
        except ImportError:
            logger.error("openai package not installed. Falling back to mock mode.")
            self.mock_mode = True
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI: {e}")
            self.mock_mode = True

    def _prepare_image_url(self, image_data: str) -> str:
        if not image_data.startswith('data:image/'):
            # Assuming JPEG if no prefix
            return f"data:image/jpeg;base64,{image_data}"
        return image_data

    async def detect_barcode(self, image_data: str) -> Dict[str, Any]:
        if self.mock_mode or not self.client:
            return {
                "success": True, "is_barcode": False, "barcode_data": None, 
                "barcode_type": None, "confidence": 1.0, "engine": "mock"
            }
        
        try:
            image_url = self._prepare_image_url(image_data)
            prompt = \"\"\"
            Analyze this image specifically for BARCODE DETECTION.
            
            Look for:
            - UPC barcodes (vertical black/white lines with numbers below)
            - EAN barcodes (similar to UPC, often 13 digits)
            - QR codes (square black/white patterns)
            
            Return ONLY a JSON response:
            {
                "is_barcode": true/false,
                "barcode_data": "extracted_code_or_null",
                "barcode_type": "UPC|EAN|QR|null",
                "confidence": 0.0-1.0
            }
            
            If no barcode is detected, return:
            {"is_barcode": false, "barcode_data": null, "barcode_type": null, "confidence": 1.0}
            \"\"\"
            
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": image_url}}
                        ],
                    }
                ],
                response_format={ "type": "json_object" },
                max_tokens=300
            )
            
            result = json.loads(response.choices[0].message.content)
            return {
                "success": True,
                "is_barcode": result.get('is_barcode', False),
                "barcode_data": result.get('barcode_data'),
                "barcode_type": result.get('barcode_type'),
                "confidence": result.get('confidence', 0.0)
            }
        except Exception as e:
            logger.error(f"OpenAI barcode detection error: {e}")
            return {"success": False, "error": str(e), "is_barcode": False, "barcode_data": None, "barcode_type": None}

    async def analyze_product_features(self, image_data: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if self.mock_mode or not self.client:
            return {
                "success": True,
                "category": "Clothing and Accessories",
                "sub_category": "T-Shirt",
                "product_type": "Casual T-Shirt",
                "brand": "Mercury",
                "attributes": {"color": "blue", "pattern": "solid", "fabric": "cotton", "size_indicators": ["L"], "other_features": ["crew neck"]},
                "confidence": 0.9,
                "description": "A stylish blue cotton t-shirt from Mercury (Offline Mode Mock Analysis)",
                "analysis_timestamp": datetime.now().isoformat()
            }
        
        try:
            image_url = self._prepare_image_url(image_data)
            prompt = f\"\"\"
            Analyze this product image for e-commerce search optimization.
            
            IDENTIFY:
            1. **Product Category**: Clothing and Accessories, Electronics, Home & Kitchen, etc.
            2. **Product Type**: T-shirt, smartphone, etc.
            3. **Brand**: Any visible brand names or logos
            4. **Key Attributes**:
               - For Clothing: Color, Pattern, Fabric, Fit, Size indicators
               - For Electronics: Brand, model, color, type
               - For FMCG: Brand, flavor, packaging type
            
            USER CONTEXT: {user_context or 'None provided'}
            
            Return ONLY JSON:
            {{
                "category": "main_category",
                "sub_category": "specific_type", 
                "product_type": "specific_product",
                "brand": "detected_brand_or_null",
                "attributes": {{
                    "color": "primary_color",
                    "pattern": "pattern_type_or_null",
                    "fabric": "material_type_or_null",
                    "size_indicators": ["visible_size_info"],
                    "other_features": ["additional_attributes"]
                }},
                "confidence": 0.0-1.0,
                "description": "natural_language_description"
            }}
            \"\"\"
            
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": image_url}}
                        ],
                    }
                ],
                response_format={ "type": "json_object" },
                max_tokens=500
            )
            
            result = json.loads(response.choices[0].message.content)
            return {
                "success": True,
                "category": result.get('category'),
                "sub_category": result.get('sub_category'),
                "product_type": result.get('product_type'),
                "brand": result.get('brand'),
                "attributes": result.get('attributes', {}),
                "confidence": result.get('confidence', 0.0),
                "description": result.get('description', ''),
                "analysis_timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"OpenAI product feature analysis error: {e}")
            return {"success": False, "error": str(e), "confidence": 0.0}
