import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 5,
  duration: '30s',
  thresholds: {
    http_req_duration: ['p(95)<500'],
    http_req_failed: ['rate<0.01'],
  },
};

const BASE_URL = __ENV.TARGET || 'http://127.0.0.1:3100';

export default function () {
  // Test Paperclip API endpoints
  const endpoints = [
    '/api/',
    '/api/agents',
    '/api/companies',
  ];
  
  for (const ep of endpoints) {
    const res = http.get(`${BASE_URL}${ep}`);
    check(res, {
      [`GET ${ep} status 200`]: (r) => r.status === 200,
      [`GET ${ep} < 200ms`]: (r) => r.timings.duration < 200,
    });
    sleep(0.5);
  }
}
