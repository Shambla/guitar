# Stripe Payment Integration Setup

## Overview
The trading signals page now supports Stripe subscriptions with:
- **7-day free trial** (no credit card required)
- **$9.99/month** recurring subscription after trial

## Prerequisites

1. **Install Python dependencies:**
   ```bash
   pip install stripe flask flask-cors python-dotenv
   ```

2. **Environment Variables (.env file)**
   Your `.env` file should contain:
   ```
   stripe_public_key=pk_test_...
   stripe_private_key=sk_test_...
   ```

## Running the Backend

Start the Stripe payment server:
```bash
cd /Users/olivia2/Documents/GitHub/guitar/web/WebContent
python3 stripe_payments.py --port 5006
```

Or with gunicorn (production):
```bash
gunicorn -w 1 -b 0.0.0.0:5006 stripe_payments:app
```

## API Endpoints

The backend provides these endpoints:

- `GET /api/stripe-public-key` - Returns the Stripe public key for client-side use
- `POST /api/create-checkout-session` - Creates a Stripe Checkout session for subscriptions
- `POST /api/webhook` - Handles Stripe webhooks for payment events
- `GET /health` - Health check endpoint

## Frontend Integration

The `signals.html` page includes:
- Subscription button in the navigation bar
- Subscription modal with pricing details
- JavaScript to handle Stripe Checkout redirect

## Stripe Dashboard Setup

1. **Create a Product & Price:**
   - Go to Stripe Dashboard → Products
   - Create a new product: "Trading Signals PRO"
   - Add a recurring price: $9.99/month
   - Copy the Price ID (optional - backend will create one if not provided)

2. **Set up Webhook:**
   - Go to Stripe Dashboard → Webhooks
   - Add endpoint: `https://yourdomain.com/api/webhook`
   - Select events:
     - `checkout.session.completed`
     - `customer.subscription.created`
     - `customer.subscription.deleted`
     - `invoice.payment_succeeded`
   - Copy the webhook signing secret to `STRIPE_WEBHOOK_SECRET` in .env

3. **Test Mode:**
   - Use test API keys for development
   - Test card: `4242 4242 4242 4242`
   - Any future expiry date and CVC

## How It Works

1. User clicks "Subscribe" button on signals.html
2. Modal opens showing pricing ($9.99/month, 7-day free trial)
3. User clicks "Start 7-Day Free Trial"
4. JavaScript calls `/api/create-checkout-session` with `productType: 'subscription'`
5. Backend creates Stripe Checkout session with 7-day trial
6. User is redirected to Stripe Checkout (no card required for trial)
7. After trial, user is redirected back to signals.html
8. Stripe webhooks notify backend of subscription events

## Notes

- The 7-day free trial requires no payment method upfront
- After the trial, Stripe will automatically charge $9.99/month
- Users can manage their subscription through Stripe Customer Portal
- All subscription events are logged to `payments/subscriptions.json`

