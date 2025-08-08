const express = require('express');
const router = express.Router();

const userRoutes = require('./userRoutes');
const productRoutes = require('./productRoutes');
const orderRoutes = require('./orderRoutes');
const paymentRoutes = require('./paymentRoutes');
const searchRoutes = require('./searchRoutes');
const notificationRoutes = require('./notificationRoutes');

// Service discovery and routing
router.use('/users', userRoutes);
router.use('/products', productRoutes);
router.use('/orders', orderRoutes);
router.use('/payments', paymentRoutes);
router.use('/search', searchRoutes);
router.use('/notifications', notificationRoutes);

// API Gateway info endpoint
router.get('/', (req, res) => {
  res.json({
    message: 'ElectroMart API Gateway',
    version: '1.0.0',
    services: {
      users: '/api/users',
      products: '/api/products',
      orders: '/api/orders',
      payments: '/api/payments',
      search: '/api/search',
      notifications: '/api/notifications'
    },
    documentation: '/api-docs'
  });
});

module.exports = router;
