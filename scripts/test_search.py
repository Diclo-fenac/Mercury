#!/usr/bin/env python3
"""
Test script for advanced search system
"""
import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import with error handling
try:
    from app.infrastructure.search.typesense import TypesenseClient
except ImportError as e:
    print(f"❌ Failed to import TypesenseClient: {e}")
    TypesenseClient = None


try:
    from app.addons.embeddings.gemini import GeminiEmbeddings
except ImportError as e:
    print(f"❌ Failed to import GeminiEmbeddings: {e}")
    GeminiEmbeddings = None

try:
    from app.addons.search.rrf import ReciprocalRankFusion
except ImportError as e:
    print(f"❌ Failed to import ReciprocalRankFusion: {e}")
    ReciprocalRankFusion = None

try:
    from app.settings import get_settings
except ImportError as e:
    print(f"❌ Failed to import Settings: {e}")
    get_settings = None


async def test_typesense():
    """Test Typesense connection and search"""
    print("\n=== Testing Typesense ===")
    
    if not TypesenseClient or not get_settings:
        print("❌ Typesense client or Settings not available")
        return False
    
    settings = get_settings()
    
    client = TypesenseClient(
        host=settings.TYPESENSE_HOST,
        port=settings.TYPESENSE_PORT,
        api_key=settings.TYPESENSE_API_KEY
    )
    
    try:
        await client.connect()
        print("✅ Typesense connected")
        
        # Test search
        result = await client.search(
            collection='products',
            query='laptop',
            query_by='title,description',
            per_page=5
        )
        
        print(f"✅ Search returned {len(result.get('documents', []))} results")
        
        if result.get('documents'):
            print(f"   First result: {result['documents'][0].get('title', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Typesense error: {e}")
        return False




async def test_embeddings():
    """Test Gemini embeddings"""
    print("\n=== Testing Gemini Embeddings ===")
    
    if not GeminiEmbeddings or not get_settings:
        print("❌ Gemini embeddings or Settings not available")
        return False
    
    settings = get_settings()
    
    embeddings = GeminiEmbeddings(api_key=settings.GOOGLE_API_KEY)
    
    try:
        await embeddings.initialize()
        print("✅ Gemini embeddings initialized")
        
        # Test embedding
        vector = await embeddings.embed_text("test query")
        if vector:
            print(f"✅ Generated embedding with {len(vector)} dimensions")
        
        return True
        
    except Exception as e:
        print(f"❌ Embeddings error: {e}")
        return False


async def test_rrf():
    """Test RRF fusion"""
    print("\n=== Testing RRF ===")
    
    if not ReciprocalRankFusion:
        print("❌ RRF not available")
        return False
    
    rrf = ReciprocalRankFusion(k=60)
    
    # Mock results
    typesense_results = [
        {'id': '1', 'title': 'Product 1', 'price': 100},
        {'id': '2', 'title': 'Product 2', 'price': 200},
        {'id': '3', 'title': 'Product 3', 'price': 150}
    ]
    
    vector_results = [
        {'id': '2', 'score': 0.9, 'payload': {'title': 'Product 2', 'price': 200}},
        {'id': '1', 'score': 0.8, 'payload': {'title': 'Product 1', 'price': 100}},
        {'id': '4', 'score': 0.7, 'payload': {'title': 'Product 4', 'price': 300}}
    ]
    
    try:
        fused = rrf.fuse_results(typesense_results, vector_results)
        print(f"✅ RRF fused {len(fused)} results")
        
        if fused:
            print(f"   Top result: {fused[0]['product'].get('title', 'N/A')}")
            print(f"   RRF score: {fused[0]['rrf_score']:.4f}")
            print(f"   Sources: {fused[0]['sources']}")
        
        return True
        
    except Exception as e:
        print(f"❌ RRF error: {e}")
        return False


async def check_dependencies():
    """Check if required dependencies are available"""
    print("=" * 50)
    print("Dependency Check")
    print("=" * 50)
    
    missing_deps = []
    
    # Check core dependencies
    try:
        import typesense
        print("✅ typesense - Available")
    except ImportError:
        print("❌ typesense - Missing (pip install typesense)")
        missing_deps.append("typesense")
    
    
    try:
        import google.genai
        print("✅ google-genai - Available")
    except ImportError:
        print("❌ google-genai - Missing (pip install google-genai)")
        missing_deps.append("google-genai")
    
    if missing_deps:
        print(f"\n⚠️  Missing dependencies: {', '.join(missing_deps)}")
        print("Install with: pip install -r requirements.txt")
        return False
    
    print("\n✅ All dependencies available")
    return True


async def main():
    """Run all tests"""
    print("=" * 50)
    print("Advanced Search System Test")
    print("=" * 50)
    
    # Check dependencies first
    deps_ok = await check_dependencies()
    if not deps_ok:
        print("\n" + "=" * 50)
        print("❌ Dependency check failed. Install missing packages first.")
        print("=" * 50)
        return 1
    
    results = {
        'Typesense': await test_typesense(),
        'Embeddings': await test_embeddings(),
        'RRF': await test_rrf()
    }
    
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name:15} {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests passed! System is ready.")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
    print("=" * 50)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
