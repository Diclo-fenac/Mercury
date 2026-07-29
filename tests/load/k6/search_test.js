import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const searchLatency = new Trend('search_latency');

export const options = {
    scenarios: {
        search_typeahead: {
            executor: 'ramping-vus',
            startVUs: 0,
            stages: [
                { duration: '30s', target: 50 },
                { duration: '1m', target: 320 }, // 320 RPS equivalent
                { duration: '30s', target: 0 },
            ],
            gracefulRampDown: '10s',
        },
    },
    thresholds: {
        'search_latency': ['p(95)<15', 'p(99)<30'], // Sub 15ms P95 is our SLA
        'errors': ['rate<0.001'], // Less than 0.1% error rate
    },
};

const BASE_URL = __ENV.API_URL || 'http://localhost:8000';
// We assume a demo org and search key exist.
const ORG_ID = __ENV.ORG_ID || 'demo-org';
const SEARCH_KEY = __ENV.SEARCH_KEY || 'pk_demo_search_key';

const SEARCH_TERMS = ['laptop', 'shoes', 'phone', 'desk', 'monitor', 'chair'];

export default function () {
    const term = SEARCH_TERMS[Math.floor(Math.random() * SEARCH_TERMS.length)];
    
    // Typeahead simulation - searching 1, then 2, then 3 characters
    for (let i = 1; i <= term.length; i++) {
        const query = term.substring(0, i);
        const payload = JSON.stringify({
            q: query,
            per_page: 5,
        });

        const params = {
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': SEARCH_KEY,
            },
        };

        const startTime = Date.now();
        const res = http.post(`${BASE_URL}/api/v1/search/${ORG_ID}`, payload, params);
        
        searchLatency.add(Date.now() - startTime);
        errorRate.add(res.status !== 200);

        check(res, {
            'is status 200': (r) => r.status === 200,
            'has hits array': (r) => r.json() && Array.isArray(r.json().hits),
        });

        // Simulate typing delay (200ms)
        sleep(0.2);
    }
    
    // Pause between full searches
    sleep(1);
}
