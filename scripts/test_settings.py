#!/usr/bin/env python3
"""
Test settings configuration
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app.settings import get_settings
    
    print("Testing Settings Configuration...")
    print("=" * 40)
    
    settings = get_settings()
    
    # Test Typesense settings
    print(f"TYPESENSE_HOST: {settings.TYPESENSE_HOST}")
    print(f"TYPESENSE_PORT: {settings.TYPESENSE_PORT}")
    print(f"TYPESENSE_API_KEY: {settings.TYPESENSE_API_KEY}")
    

    
    # Test Google settings
    print(f"GOOGLE_API_KEY: {'***' if settings.GOOGLE_API_KEY else 'Not set'}")
    
    print("=" * 40)
    print("✅ Settings loaded successfully!")
    
except Exception as e:
    print(f"❌ Error loading settings: {e}")
    sys.exit(1)