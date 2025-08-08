const express = require('express');
const { body, validationResult } = require('express-validator');
const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);
const { v4: uuidv4 } = require('uuid');
const auth = require('../middleware/auth');

const router = express.Router();

/**
 * @swagger
 * components:
 *   schemas:
 *     PaymentIntentRequest:
 *       type: object
 *       required:
 *         - amount
 *         - currency
 *         - orderId
 *       properties:
 *         amount:
 *           type: integer
 *           description: Amount in cents
 *         currency:
 *           type: string
 *           default: usd
 *         orderId:
 *           type: string
 *         paymentMethodId:
 *           type: string
 *         description:
 *           type: string
 *     PaymentMethodRequest:
 *       type: object
 *       required:
 *         - type
 *         - card
 *       properties:
 *         type:
 *           type: string
 *           enum: [card]
 *         card:
 *           type: object
 *           properties:
 *             number:
 *               type: string
 *             expMonth:
 *               type: integer
 *             expYear:
 *               type: integer
 *             cvc:
 *               type: string
 *     PaymentResponse:
 *       type: object
 *       properties:
 *         success:
 *           type: boolean
 *         paymentIntentId:
 *           type: string
 *         clientSecret:
 *           type: string
 *         status:
 *           type: string
 */

/**
 * @swagger
 * /api/payments/create-payment-intent:
 *   post:
 *     summary: Create a payment intent
 *     tags: [Payments]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             $ref: '#/components/schemas/PaymentIntentRequest'
 *     responses:
 *       200:
 *         description: Payment intent created successfully
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/PaymentResponse'
 *       400:
 *         description: Validation error
 *       401:
 *         description: Unauthorized
 */
router.post('/create-payment-intent', [
  auth,
  body('amount').isInt({ min: 50 }).withMessage('Amount must be at least 50 cents'),
  body('currency').isIn(['usd', 'eur', 'gbp']).withMessage('Currency must be usd, eur, or gbp'),
  body('orderId').notEmpty().withMessage('Order ID is required')
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { amount, currency, orderId, paymentMethodId, description } = req.body;
    const userId = req.user.userId;

    // Check if payment intent already exists for this order
    const existingPayment = await global.redisClient.get(`payment_intent:${orderId}`);
    if (existingPayment) {
      const paymentData = JSON.parse(existingPayment);
      return res.json({
        success: true,
        paymentIntentId: paymentData.paymentIntentId,
        clientSecret: paymentData.clientSecret,
        status: paymentData.status
      });
    }

    // Create payment intent with Stripe
    const paymentIntent = await stripe.paymentIntents.create({
      amount,
      currency,
      payment_method_types: ['card'],
      metadata: {
        orderId,
        userId: userId.toString()
      },
      description: description || `Payment for order ${orderId}`,
      ...(paymentMethodId && { payment_method: paymentMethodId })
    });

    // Store payment intent in Redis
    const paymentData = {
      paymentIntentId: paymentIntent.id,
      clientSecret: paymentIntent.client_secret,
      status: paymentIntent.status,
      amount,
      currency,
      orderId,
      userId,
      createdAt: new Date().toISOString()
    };

    await global.redisClient.setEx(
      `payment_intent:${orderId}`,
      3600, // 1 hour expiry
      JSON.stringify(paymentData)
    );

    res.json({
      success: true,
      paymentIntentId: paymentIntent.id,
      clientSecret: paymentIntent.client_secret,
      status: paymentIntent.status
    });
  } catch (error) {
    console.error('Create payment intent error:', error);
    res.status(500).json({ error: 'Failed to create payment intent' });
  }
});

/**
 * @swagger
 * /api/payments/confirm-payment:
 *   post:
 *     summary: Confirm a payment
 *     tags: [Payments]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - paymentIntentId
 *             properties:
 *               paymentIntentId:
 *                 type: string
 *     responses:
 *       200:
 *         description: Payment confirmed successfully
 *       400:
 *         description: Payment failed
 *       401:
 *         description: Unauthorized
 */
router.post('/confirm-payment', [
  auth,
  body('paymentIntentId').notEmpty().withMessage('Payment intent ID is required')
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { paymentIntentId } = req.body;
    const userId = req.user.userId;

    // Retrieve payment intent from Stripe
    const paymentIntent = await stripe.paymentIntents.retrieve(paymentIntentId);
    
    if (!paymentIntent) {
      return res.status(404).json({ error: 'Payment intent not found' });
    }

    // Verify user owns this payment intent
    if (paymentIntent.metadata.userId !== userId.toString()) {
      return res.status(403).json({ error: 'Access denied' });
    }

    // Check if payment is already succeeded
    if (paymentIntent.status === 'succeeded') {
      return res.json({
        success: true,
        message: 'Payment already confirmed',
        status: paymentIntent.status
      });
    }

    // Confirm the payment
    const confirmedPayment = await stripe.paymentIntents.confirm(paymentIntentId);

    if (confirmedPayment.status === 'succeeded') {
      // Update Redis cache
      const orderId = confirmedPayment.metadata.orderId;
      const cachedPayment = await global.redisClient.get(`payment_intent:${orderId}`);
      
      if (cachedPayment) {
        const paymentData = JSON.parse(cachedPayment);
        paymentData.status = confirmedPayment.status;
        paymentData.confirmedAt = new Date().toISOString();
        
        await global.redisClient.setEx(
          `payment_intent:${orderId}`,
          3600,
          JSON.stringify(paymentData)
        );
      }

      // Store successful payment
      await global.redisClient.setEx(
        `payment:${confirmedPayment.id}`,
        86400, // 24 hours
        JSON.stringify({
          paymentIntentId: confirmedPayment.id,
          orderId: confirmedPayment.metadata.orderId,
          userId,
          amount: confirmedPayment.amount,
          currency: confirmedPayment.currency,
          status: confirmedPayment.status,
          confirmedAt: new Date().toISOString()
        })
      );
    }

    res.json({
      success: true,
      status: confirmedPayment.status,
      message: confirmedPayment.status === 'succeeded' ? 'Payment confirmed successfully' : 'Payment processing'
    });
  } catch (error) {
    console.error('Confirm payment error:', error);
    res.status(500).json({ error: 'Failed to confirm payment' });
  }
});

/**
 * @swagger
 * /api/payments/payment-status/{paymentIntentId}:
 *   get:
 *     summary: Get payment status
 *     tags: [Payments]
 *     security:
 *       - bearerAuth: []
 *     parameters:
 *       - in: path
 *         name: paymentIntentId
 *         required: true
 *         schema:
 *           type: string
 *         description: Payment intent ID
 *     responses:
 *       200:
 *         description: Payment status retrieved successfully
 *       401:
 *         description: Unauthorized
 *       404:
 *         description: Payment not found
 */
router.get('/payment-status/:paymentIntentId', auth, async (req, res) => {
  try {
    const { paymentIntentId } = req.params;
    const userId = req.user.userId;

    // Check Redis cache first
    const cachedPayment = await global.redisClient.get(`payment:${paymentIntentId}`);
    if (cachedPayment) {
      const paymentData = JSON.parse(cachedPayment);
      if (paymentData.userId === userId) {
        return res.json({
          success: true,
          payment: paymentData
        });
      }
    }

    // Retrieve from Stripe
    const paymentIntent = await stripe.paymentIntents.retrieve(paymentIntentId);
    
    if (!paymentIntent) {
      return res.status(404).json({ error: 'Payment not found' });
    }

    // Verify user owns this payment
    if (paymentIntent.metadata.userId !== userId.toString()) {
      return res.status(403).json({ error: 'Access denied' });
    }

    res.json({
      success: true,
      payment: {
        paymentIntentId: paymentIntent.id,
        orderId: paymentIntent.metadata.orderId,
        userId,
        amount: paymentIntent.amount,
        currency: paymentIntent.currency,
        status: paymentIntent.status,
        created: new Date(paymentIntent.created * 1000).toISOString()
      }
    });
  } catch (error) {
    console.error('Get payment status error:', error);
    res.status(500).json({ error: 'Failed to get payment status' });
  }
});

/**
 * @swagger
 * /api/payments/refund:
 *   post:
 *     summary: Refund a payment
 *     tags: [Payments]
 *     security:
 *       - bearerAuth: []
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - paymentIntentId
 *             properties:
 *               paymentIntentId:
 *                 type: string
 *               amount:
 *                 type: integer
 *               reason:
 *                 type: string
 *     responses:
 *       200:
 *         description: Refund processed successfully
 *       400:
 *         description: Refund failed
 *       401:
 *         description: Unauthorized
 */
router.post('/refund', [
  auth,
  body('paymentIntentId').notEmpty().withMessage('Payment intent ID is required'),
  body('amount').optional().isInt({ min: 1 }).withMessage('Amount must be positive'),
  body('reason').optional().isIn(['duplicate', 'fraudulent', 'requested_by_customer']).withMessage('Invalid refund reason')
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { paymentIntentId, amount, reason } = req.body;
    const userId = req.user.userId;

    // Retrieve payment intent
    const paymentIntent = await stripe.paymentIntents.retrieve(paymentIntentId);
    
    if (!paymentIntent) {
      return res.status(404).json({ error: 'Payment not found' });
    }

    // Verify user owns this payment
    if (paymentIntent.metadata.userId !== userId.toString()) {
      return res.status(403).json({ error: 'Access denied' });
    }

    // Check if payment is eligible for refund
    if (paymentIntent.status !== 'succeeded') {
      return res.status(400).json({ error: 'Payment is not eligible for refund' });
    }

    // Create refund
    const refundData = {
      payment_intent: paymentIntentId,
      ...(amount && { amount }),
      ...(reason && { reason })
    };

    const refund = await stripe.refunds.create(refundData);

    // Store refund in Redis
    await global.redisClient.setEx(
      `refund:${refund.id}`,
      86400, // 24 hours
      JSON.stringify({
        refundId: refund.id,
        paymentIntentId,
        orderId: paymentIntent.metadata.orderId,
        userId,
        amount: refund.amount,
        currency: refund.currency,
        status: refund.status,
        reason: refund.reason,
        createdAt: new Date().toISOString()
      })
    );

    res.json({
      success: true,
      refundId: refund.id,
      status: refund.status,
      message: 'Refund processed successfully'
    });
  } catch (error) {
    console.error('Refund error:', error);
    res.status(500).json({ error: 'Failed to process refund' });
  }
});

module.exports = router;
