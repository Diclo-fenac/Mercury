"""
Translation Service
Language detection and translation using deep-translator
"""
from typing import Optional, Dict, Any
from langdetect import detect
from deep_translator import GoogleTranslator

from app.services.container import ServiceInterface
from app.core.logging import get_logger

logger = get_logger("translation")

class TranslationService(ServiceInterface):
    """Translation service using deep-translator"""
    
    def __init__(self):
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize translation service"""
        self._initialized = True
        logger.info("✅ Translation service initialized")
    
    async def cleanup(self) -> None:
        """Cleanup translation service"""
        self._initialized = False
        logger.info("✅ Translation service cleaned up")
    
    async def health_check(self) -> bool:
        """Check translation service health"""
        return self._initialized
    
    def detect_language(self, text: str) -> str:
        """Detect language of text"""
        try:
            if not text or len(text.strip()) < 3:
                return 'en'
            
            lang = detect(text)
            return lang
        except Exception as e:
            logger.error(f"Language detection error: {e}")
            return 'en'  # Default to English
    
    def translate_text(
        self, 
        text: str, 
        target_lang: str = 'en', 
        source_lang: Optional[str] = None
    ) -> Dict[str, Any]:
        """Translate text to target language"""
        try:
            if not text or not text.strip():
                return {
                    "success": False,
                    "error": "Empty text provided"
                }
            
            # Detect source language if not provided
            if not source_lang:
                source_lang = self.detect_language(text)
            
            # Skip translation if already in target language
            if source_lang == target_lang:
                return {
                    "success": True,
                    "original_text": text,
                    "translated_text": text,
                    "source_language": source_lang,
                    "target_language": target_lang,
                    "translation_needed": False
                }
            
            # Perform translation
            translator = GoogleTranslator(source=source_lang, target=target_lang)
            translated = translator.translate(text)
            
            return {
                "success": True,
                "original_text": text,
                "translated_text": translated,
                "source_language": source_lang,
                "target_language": target_lang,
                "translation_needed": True
            }
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return {
                "success": False,
                "error": str(e),
                "original_text": text,
                "translated_text": text,  # Return original on error
                "source_language": source_lang or 'unknown',
                "target_language": target_lang
            }
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Get supported languages"""
        try:
            # Common language codes and names
            return {
                'en': 'English',
                'es': 'Spanish',
                'fr': 'French',
                'de': 'German',
                'it': 'Italian',
                'pt': 'Portuguese',
                'ru': 'Russian',
                'ja': 'Japanese',
                'ko': 'Korean',
                'zh': 'Chinese',
                'ar': 'Arabic',
                'hi': 'Hindi',
                'th': 'Thai',
                'vi': 'Vietnamese',
                'nl': 'Dutch',
                'sv': 'Swedish',
                'da': 'Danish',
                'no': 'Norwegian',
                'fi': 'Finnish',
                'pl': 'Polish'
            }
        except Exception as e:
            logger.error(f"Error getting supported languages: {e}")
            return {'en': 'English'}
    
    async def translate_async(
        self, 
        text: str, 
        target_lang: str = 'en', 
        source_lang: Optional[str] = None
    ) -> Dict[str, Any]:
        """Async wrapper for translation"""
        import asyncio
        
        # Run translation in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, 
            self.translate_text, 
            text, 
            target_lang, 
            source_lang
        )
        
        return result