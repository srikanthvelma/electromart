const redis = require('redis');

async function healthCheck() {
  const client = redis.createClient({
    url: process.env.REDIS_URL || 'redis://redis:6379'
  });

  try {
    await client.connect();
    await client.ping();
    console.log('Health check passed');
    await client.quit();
    process.exit(0);
  } catch (error) {
    console.error('Health check failed:', error);
    await client.quit();
    process.exit(1);
  }
}

healthCheck();
