"""
Zero-result query tracking and analysis
Run periodically to measure search success rates
"""
import asyncio
import json
from datetime import datetime
from collections import defaultdict
from app.orchestrators.search_orchestrator import SearchOrchestrator
from app.addons.search.hybrid import HybridSearch
from app.infrastructure.cache.redis import RedisClient


class ZeroResultTracker:
    """Track and analyze zero-result queries"""
    
    def __init__(self, orchestrator: SearchOrchestrator):
        self.orchestrator = orchestrator
        self.stats = {
            'total_queries': 0,
            'zero_results': 0,
            'with_fallback': 0,
            'fallback_success': 0,
            'by_query_type': defaultdict(int),
            'zero_by_type': defaultdict(int)
        }
    
    async def run_test_queries(self, test_queries: list):
        """Run test queries and track results"""
        for query in test_queries:
            self.stats['total_queries'] += 1
            
            # Try primary search
            result = await self.orchestrator.handle(
                query=query['query'],
                user_id='test_user',
                filters=query.get('filters'),
                limit=10
            )
            
            result_count = len(result.get('results', []))
            query_type = query.get('type', 'keyword')
            self.stats['by_query_type'][query_type] += 1
            
            if result_count == 0:
                self.stats['zero_results'] += 1
                self.stats['zero_by_type'][query_type] += 1
                
                # Check if fallback was used (simulated)
                # In real implementation, check logs/metrics
                self.stats['with_fallback'] += 1
                
                # Try fallback (semantic expansion)
                fallback_result = await self.orchestrator.handle(
                    query=query['expanded_query'] if query.get('expanded_query') else query['query'],
                    user_id='test_user',
                    limit=10
                )
                
                if len(fallback_result.get('results', [])) > 0:
                    self.stats['fallback_success'] += 1
    
    def get_report(self) -> dict:
        """Generate zero-result analysis report"""
        total = self.stats['total_queries']
        zero = self.stats['zero_results']
        
        reduction = 0
        if self.stats['with_fallback'] > 0:
            fallback_failed = self.stats['with_fallback'] - self.stats['fallback_success']
            reduction = (fallback_failed / total) * 100 if total > 0 else 0
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_queries': total,
            'zero_result_count': zero,
            'zero_result_rate': f"{(zero/total*100):.1f}%" if total > 0 else "0%",
            'fallback_applied': self.stats['with_fallback'],
            'fallback_success_rate': f"{self.stats['fallback_success']/self.stats['with_fallback']*100:.1f}%" if self.stats['with_fallback'] > 0 else "0%",
            'zero_result_reduction_potential': f"{reduction:.1f}%",
            'by_query_type': dict(self.stats['by_query_type']),
            'zero_by_type': dict(self.stats['zero_by_type'])
        }


# Test queries with semantic expansions
TEST_QUERIES = [
    {'query': 'laptop', 'type': 'keyword', 'expanded_query': 'laptop computer notebook'},
    {'query': 'phon', 'type': 'typo', 'expanded_query': 'phone mobile smartphone'},
    {'query': 'hedfons', 'type': 'typo', 'expanded_query': 'headphones earbuds audio'},
    {'query': 'shoe', 'type': 'keyword', 'expanded_query': 'shoes footwear sneakers'},
    {'query': 'bluetooth speker', 'type': 'misspelling', 'expanded_query': 'bluetooth speaker audio'},
    {'query': 'tshrt', 'type': 'typo', 'expanded_query': 'tshirt t-shirt apparel'},
    {'query': 'lappi', 'type': 'typo', 'expanded_query': 'laptop computer notebook'},
    {'query': 'wrist watch', 'type': 'keyword', 'expanded_query': 'wrist watch timepiece'},
]


if __name__ == '__main__':
    print("Run: python -c \"from tests.track_zero_results import *; asyncio.run(main())\"")
    print("Or integrate into your test suite to track over time")