import ws from 'k6/ws';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const connectionErrors = new Rate('ws_connection_errors');
const connectionDuration = new Trend('ws_connection_duration');

export const options = {
    scenarios: {
        websocket_concurrency: {
            executor: 'ramping-vus',
            startVUs: 0,
            stages: [
                { duration: '30s', target: 250 }, // Ramp to 250
                { duration: '1m', target: 1000 }, // Sustain 1,000 WebSocket connections
                { duration: '30s', target: 0 },
            ],
            gracefulRampDown: '10s',
        },
    },
    thresholds: {
        'ws_connection_errors': ['rate<0.01'], // Strict <1% drop rate
    },
};

const BASE_WS_URL = __ENV.WS_URL || 'ws://localhost:8000';
const ORG_ID = __ENV.ORG_ID || 'demo-org';
const ADMIN_TOKEN = __ENV.ADMIN_TOKEN || 'sk_demo_admin_key';

export default function () {
    const url = `${BASE_WS_URL}/api/v1/ws/dashboard`;
    const params = { tags: { my_tag: 'dashboard' } };

    const startTime = Date.now();
    const res = ws.connect(url, params, function (socket) {
        
        socket.on('open', function open() {
            // Send auth handshake exactly as router expects
            socket.send(JSON.stringify({
                event: 'auth',
                token: ADMIN_TOKEN
            }));
        });

        socket.on('message', function (msg) {
            // We expect regular index updates or pings
            console.log(`Received message: ${msg}`);
        });

        socket.on('close', function (code, reason) {
            // Check if we hit the 1008 Too Many Connections limit
            if (code !== 1000) {
                connectionErrors.add(1);
            } else {
                connectionErrors.add(0);
            }
            connectionDuration.add(Date.now() - startTime);
        });
        
        socket.on('error', function (e) {
            if (e.error() !== "websocket: close 1006 (abnormal closure)") {
                connectionErrors.add(1);
            }
        });

        socket.setTimeout(function () {
            // Hold the connection open for 15 seconds to simulate a live user
            socket.close();
        }, 15000);
    });

    check(res, { 'status is 101': (r) => r && r.status === 101 });
}
