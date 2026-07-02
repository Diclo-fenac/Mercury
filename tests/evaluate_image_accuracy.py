"""
Image Retrieval Accuracy Evaluation
Place test images in tests/datasets/image_retrieval/
- query_images/: Images to search with
- expected_matches/: Expected matching product images (named by product_id)

Run: python tests/evaluate_image_accuracy.py
"""
import os
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict

# Configuration
DATASET_DIR = Path("tests/datasets/image_retrieval")
QUERY_DIR = DATASET_DIR / "query_images"
EXPECTED_DIR = DATASET_DIR / "expected_matches"
RESULTS_FILE = DATASET_DIR / "accuracy_results.json"


class ImageRetrievalEvaluator:
    """Evaluate image-based product retrieval accuracy"""
    
    def __init__(self, image_service):
        self.image_service = image_service
        self.results = {
            'total_queries': 0,
            'top1_matches': 0,
            'top3_matches': 0,
            'top5_matches': 0,
            'no_match': 0,
            'by_category': defaultdict(lambda: {'total': 0, 'top1': 0, 'top3': 0, 'top5': 0})
        }
    
    def load_test_dataset(self) -> List[Dict[str, Any]]:
        """Load test dataset from filesystem"""
        queries = []
        
        if not QUERY_DIR.exists():
            print(f"⚠️ Query directory not found: {QUERY_DIR}")
            print(f"   Create images in: {QUERY_DIR}")
            return queries
        
        for query_file in QUERY_DIR.iterdir():
            if query_file.is_file() and query_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']:
                # Expected match is a file with same name in expected_matches/
                expected_file = EXPECTED_DIR / query_file.name
                expected_id = expected_file.stem if expected_file.exists() else None
                
                queries.append({
                    'image_path': str(query_file),
                    'image_name': query_file.stem,
                    'expected_product_id': expected_id,
                    'category': query_file.stem.split('_')[0] if '_' in query_file.stem else 'unknown'
                })
        
        return queries
    
    async def evaluate(self, queries: List[Dict]) -> Dict[str, Any]:
        """Run evaluation on all queries"""
        print(f"📊 Evaluating {len(queries)} image queries...")
        
        for i, query in enumerate(queries):
            print(f"  [{i+1}/{len(queries)}] Processing: {query['image_name']}")
            
            # Read image
            with open(query['image_path'], 'rb') as f:
                import base64
                image_data = base64.b64encode(f.read()).decode()
                image_data = f"data:image/jpeg;base64,{image_data}"
            
            # Search by image
            try:
                results = await self.image_service.search_by_image(image_data, limit=5)
                
                self.results['total_queries'] += 1
                category = query['category']
                self.results['by_category'][category]['total'] += 1
                
                # Check Top-K accuracy
                result_ids = [r.get('id') or r.get('product_id') for r in results]
                expected_id = query['expected_product_id']
                
                if not expected_id:
                    print(f"    ⚠️ No expected match defined")
                    continue
                
                if expected_id in result_ids:
                    rank = result_ids.index(expected_id) + 1
                    
                    if rank == 1:
                        self.results['top1_matches'] += 1
                        self.results['by_category'][category]['top1'] += 1
                        print(f"    ✅ Top-1 match!")
                    elif rank <= 3:
                        self.results['top3_matches'] += 1
                        self.results['by_category'][category]['top3'] += 1
                        print(f"    ✅ Top-3 match (rank {rank})")
                    elif rank <= 5:
                        self.results['top5_matches'] += 1
                        self.results['by_category'][category]['top5'] += 1
                        print(f"    ✅ Top-5 match (rank {rank})")
                else:
                    self.results['no_match'] += 1
                    print(f"    ❌ No match in top 5")
                    
            except Exception as e:
                print(f"    ❌ Error: {e}")
        
        return self._compute_accuracy()
    
    def _compute_accuracy(self) -> Dict[str, Any]:
        """Compute accuracy metrics"""
        total = self.results['total_queries']
        
        if total == 0:
            return {'error': 'No queries evaluated'}
        
        top1_acc = self.results['top1_matches'] / total * 100
        top3_acc = self.results['top3_matches'] / total * 100
        top5_acc = self.results['top5_matches'] / total * 100
        
        report = {
            'total_queries': total,
            'top1_accuracy': f"{top1_acc:.1f}%",
            'top3_accuracy': f"{top3_acc:.1f}%",
            'top5_accuracy': f"{top5_acc:.1f}%",
            'top1_count': self.results['top1_matches'],
            'top3_count': self.results['top3_matches'],
            'top5_count': self.results['top5_matches'],
            'no_match_count': self.results['no_match'],
            'by_category': dict(self.results['by_category'])
        }
        
        return report


def print_accuracy_report(report: Dict):
    """Print formatted accuracy report"""
    print("\n" + "="*50)
    print("📸 IMAGE RETRIEVAL ACCURACY REPORT")
    print("="*50)
    print(f"Total queries:     {report.get('total_queries', 0)}")
    print(f"Top-1 Accuracy:    {report.get('top1_accuracy', 'N/A')}")
    print(f"Top-3 Accuracy:    {report.get('top3_accuracy', 'N/A')}")
    print(f"Top-5 Accuracy:    {report.get('top5_accuracy', 'N/A')}")
    print("-"*50)
    
    if 'by_category' in report:
        print("By Category:")
        for cat, stats in report['by_category'].items():
            cat_top1 = stats['top1'] / stats['total'] * 100 if stats['total'] > 0 else 0
            print(f"  {cat}: {cat_top1:.1f}% ({stats['top1']}/{stats['total']})")
    
    print("="*50)


# Instructions for creating test dataset
def print_setup_instructions():
    """Print setup instructions"""
    print("""
📁 SETUP INSTRUCTIONS FOR IMAGE RETRIEVAL DATASET
===================================================

1. Create test query images in:
   tests/datasets/image_retrieval/query_images/
   
   Naming: {category}_{product_id}.jpg
   Example: electronics_laptop_001.jpg

2. Create expected match images in:
   tests/datasets/image_retrieval/expected_matches/
   
   Naming: {product_id}.jpg
   Example: laptop_001.jpg

3. Run evaluation:
   python tests/evaluate_image_accuracy.py

Example structure:
├── query_images/
│   ├── electronics_phone_001.jpg
│   ├── clothing_tshirt_002.jpg
│   └── shoes_sneakers_003.jpg
└── expected_matches/
    ├── phone_001.jpg
    ├── tshirt_002.jpg
    └── sneakers_003.jpg
""")


if __name__ == '__main__':
    print_setup_instructions()