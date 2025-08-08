import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 5 },  // Ramp up to 5 users
    { duration: '1m', target: 5 },   // Stay at 5 users
    { duration: '30s', target: 0 },  // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'], // 95% of requests must complete below 2s
    http_req_failed: ['rate<0.1'],     // Error rate must be less than 10%
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export default function () {
  // Test API Gateway health
  const healthCheck = http.get(`${BASE_URL}/health`);
  check(healthCheck, {
    'health check status is 200': (r) => r.status === 200,
    'health check response time < 500ms': (r) => r.timings.duration < 500,
  });

  // Test API endpoints
  const apiEndpoints = [
    '/api/users/health',
    '/api/products/health',
    '/api/orders/health',
    '/api/payments/health',
    '/api/search/health',
    '/api/notifications/health',
  ];

  apiEndpoints.forEach(endpoint => {
    const response = http.get(`${BASE_URL}${endpoint}`);
    check(response, {
      [`${endpoint} status is 200`]: (r) => r.status === 200,
      [`${endpoint} response time < 1000ms`]: (r) => r.timings.duration < 1000,
    });
  });

  // Test product listing
  const productsResponse = http.get(`${BASE_URL}/api/products`);
  check(productsResponse, {
    'products endpoint status is 200': (r) => r.status === 200,
    'products endpoint response time < 2000ms': (r) => r.timings.duration < 2000,
  });

  sleep(1);
}
