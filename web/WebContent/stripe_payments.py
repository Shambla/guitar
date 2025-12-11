#!/usr/bin/env python3
"""
Stripe Payment Integration for brianstreckfus.com
==================================================

Handles:
- One-time payments (sheet music, MP3s, donations)
- Subscriptions (trading signals)
- Webhooks for payment confirmation
- Customer management

Setup:
1. pip install stripe flask
2. Get API keys from https://dashboard.stripe.com/apikeys
3. Set environment variables:
   - STRIPE_SECRET_KEY
   - STRIPE_PUBLISHABLE_KEY
   - STRIPE_WEBHOOK_SECRET

Usage:
    python3 stripe_payments.py --port 5006
    
    Or with gunicorn:
    gunicorn -w 1 -b 0.0.0.0:5006 stripe_payments:app
"""

import os
import json
import stripe
from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    load_dotenv(env_path)
except ImportError:
    print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")
    print("   Environment variables will be loaded from system environment only.")

# Configuration - Load from .env file (stripe_public_key and stripe_private_key)
STRIPE_SECRET_KEY = os.getenv("stripe_private_key") or os.getenv("STRIPE_SECRET_KEY", "sk_test_YOUR_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = os.getenv("stripe_public_key") or os.getenv("STRIPE_PUBLISHABLE_KEY", "pk_test_YOUR_PUBLISHABLE_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_YOUR_WEBHOOK_SECRET")
DOMAIN = os.getenv("DOMAIN", "https://brianstreckfus.com")

# Initialize Stripe
stripe.api_key = STRIPE_SECRET_KEY

# Product Pricing (in cents)
PRODUCTS = {
    "signals_subscription": {
        "name": "Trading Signals PRO",
        "amount": 999,  # $9.99
        "currency": "usd",
        "interval": "month",
        "description": "Premium algorithmic trading signals with real-time alerts"
    },
    "sheet_music": {
        "name": "Sheet Music",
        "amount_range": (299, 999),  # $2.99 - $9.99
        "currency": "usd",
        "description": "Professional guitar arrangement with TAB"
    },
    "mp3": {
        "name": "MP3 Backing Track",
        "amount_range": (99, 499),  # $0.99 - $4.99
        "currency": "usd",
        "description": "High-quality MP3 backing track"
    }
}

# Create Flask app
app = Flask(__name__)
CORS(app, origins=["*"])  # Adjust for production


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"ok": True, "service": "stripe_payments"}), 200


@app.route('/api/stripe-public-key', methods=['GET'])
def get_stripe_public_key():
    """Return the Stripe public key for client-side use"""
    return jsonify({"publicKey": STRIPE_PUBLISHABLE_KEY}), 200


@app.route('/api/create-checkout-session', methods=['POST'])
def create_checkout_session():
    """
    Create a Stripe Checkout Session for payment
    
    Request body:
    {
        "productType": "subscription|sheet_music|mp3|donation",
        "amount": 1999 (for one-time payments, in cents),
        "priceId": "price_xxx" (for subscriptions),
        "metadata": {"title": "...", "file": "..."}
    }
    """
    try:
        data = request.json
        product_type = data.get('productType')
        
        # Base session parameters
        session_params = {
            'payment_method_types': ['card'],
            'mode': 'payment',  # or 'subscription'
            'success_url': f'{DOMAIN}/signals.html?session_id={{CHECKOUT_SESSION_ID}}',
            'cancel_url': f'{DOMAIN}/signals.html',
        }
        
        # Handle different product types
        if product_type == 'subscription':
            # Subscription for trading signals
            price_id = data.get('priceId')
            trial_days = data.get('trial_days', 7)  # Default 7-day free trial
            
            if not price_id:
                # Create a price on-the-fly (or use pre-created price ID)
                product = PRODUCTS['signals_subscription']
                stripe_product = stripe.Product.create(
                    name=product['name'],
                    description=product['description']
                )
                stripe_price = stripe.Price.create(
                    product=stripe_product.id,
                    unit_amount=product['amount'],
                    currency=product['currency'],
                    recurring={'interval': product['interval']}
                )
                price_id = stripe_price.id
            
            session_params['mode'] = 'subscription'
            session_params['line_items'] = [{
                'price': price_id,
                'quantity': 1
            }]
            
            # Add free trial (7 days, no card required)
            if trial_days and trial_days > 0:
                session_params['subscription_data'] = {
                    'trial_period_days': trial_days
                }
                # Allow subscription without payment method for trial
                session_params['payment_method_collection'] = 'if_required'
                print(f"✅ Adding {trial_days}-day free trial to subscription (no card required)")
            
        elif product_type == 'donation':
            # One-time donation
            amount = data.get('amount', 1000)  # Default $10
            session_params['line_items'] = [{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'Donation to Brian Streckfus',
                        'description': 'Thank you for your support!'
                    },
                    'unit_amount': amount
                },
                'quantity': 1
            }]
            
        elif product_type in ['sheet_music', 'mp3']:
            # One-time purchase
            amount = data.get('amount')
            title = data.get('metadata', {}).get('title', 'Download')
            product_info = PRODUCTS[product_type]
            
            if not amount:
                # Use middle of range if not specified
                amount = sum(product_info['amount_range']) // 2
            
            session_params['line_items'] = [{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f"{product_info['name']}: {title}",
                        'description': product_info['description']
                    },
                    'unit_amount': amount
                },
                'quantity': 1
            }]
            
            # Add metadata for fulfillment
            session_params['metadata'] = data.get('metadata', {})
            
        else:
            return jsonify({"error": "Invalid product type"}), 400
        
        # Create the Checkout Session
        session = stripe.checkout.Session.create(**session_params)
        
        return jsonify({
            "sessionId": session.id,
            "id": session.id,  # For backwards compatibility
            "url": session.url
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/webhook', methods=['POST'])
def stripe_webhook():
    """
    Handle Stripe webhooks for payment events
    
    Important events:
    - checkout.session.completed: Payment successful
    - customer.subscription.created: New subscription
    - customer.subscription.deleted: Subscription cancelled
    - invoice.payment_succeeded: Recurring payment successful
    """
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        return jsonify({"error": "Invalid payload"}), 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return jsonify({"error": "Invalid signature"}), 400
    
    # Handle the event
    event_type = event['type']
    
    if event_type == 'checkout.session.completed':
        session = event['data']['object']
        handle_successful_payment(session)
        
    elif event_type == 'customer.subscription.created':
        subscription = event['data']['object']
        handle_new_subscription(subscription)
        
    elif event_type == 'customer.subscription.deleted':
        subscription = event['data']['object']
        handle_cancelled_subscription(subscription)
        
    elif event_type == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        handle_recurring_payment(invoice)
    
    return jsonify({"success": True}), 200


def handle_successful_payment(session: Dict[str, Any]):
    """
    Handle successful one-time payment
    
    Actions:
    1. Log the payment
    2. Send download link via email
    3. Grant access to content
    """
    print(f"✅ Payment successful!")
    print(f"   Customer: {session.get('customer_email')}")
    print(f"   Amount: ${session.get('amount_total', 0) / 100}")
    print(f"   Metadata: {session.get('metadata')}")
    
    # TODO: Send email with download link
    # TODO: Grant access to purchased content
    
    # Log to file
    log_payment(session)


def handle_new_subscription(subscription: Dict[str, Any]):
    """
    Handle new subscription signup
    
    Actions:
    1. Grant access to trading signals
    2. Send welcome email
    3. Add to subscriber list
    """
    print(f"🎉 New subscription!")
    print(f"   Customer: {subscription.get('customer')}")
    print(f"   Plan: {subscription.get('plan', {}).get('nickname')}")
    
    # TODO: Grant access to signals page
    # TODO: Send welcome email
    # TODO: Add to subscriber database
    
    log_subscription(subscription)


def handle_cancelled_subscription(subscription: Dict[str, Any]):
    """
    Handle subscription cancellation
    
    Actions:
    1. Revoke access to trading signals
    2. Send cancellation confirmation
    """
    print(f"❌ Subscription cancelled")
    print(f"   Customer: {subscription.get('customer')}")
    
    # TODO: Revoke access
    # TODO: Send cancellation email
    
    log_subscription_cancellation(subscription)


def handle_recurring_payment(invoice: Dict[str, Any]):
    """
    Handle successful recurring payment
    
    Actions:
    1. Extend subscription access
    2. Send payment receipt
    """
    print(f"💰 Recurring payment received")
    print(f"   Amount: ${invoice.get('amount_paid', 0) / 100}")
    
    # TODO: Extend subscription
    # TODO: Send receipt


def log_payment(data: Dict[str, Any]):
    """Log payment to file"""
    log_dir = Path.home() / "Documents" / "GitHub" / "guitar" / "web" / "WebContent" / "payments"
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"payment_{datetime.now().strftime('%Y%m%d')}.json"
    
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "type": "payment",
        "data": data
    }
    
    # Append to log file
    with open(log_file, 'a') as f:
        f.write(json.dumps(entry) + "\n")


def log_subscription(data: Dict[str, Any]):
    """Log subscription event"""
    log_dir = Path.home() / "Documents" / "GitHub" / "guitar" / "web" / "WebContent" / "payments"
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / "subscriptions.json"
    
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "type": "subscription_created",
        "data": data
    }
    
    with open(log_file, 'a') as f:
        f.write(json.dumps(entry) + "\n")


def log_subscription_cancellation(data: Dict[str, Any]):
    """Log subscription cancellation"""
    log_dir = Path.home() / "Documents" / "GitHub" / "guitar" / "web" / "WebContent" / "payments"
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / "subscriptions.json"
    
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "type": "subscription_cancelled",
        "data": data
    }
    
    with open(log_file, 'a') as f:
        f.write(json.dumps(entry) + "\n")


@app.route('/api/customer-portal', methods=['POST'])
def customer_portal():
    """
    Create a link to Stripe Customer Portal
    where customers can manage their subscription
    """
    try:
        data = request.json
        customer_id = data.get('customer_id')
        
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=f'{DOMAIN}/signals.html'
        )
        
        return jsonify({"url": session.url}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def main():
    """Run the Flask app"""
    import argparse
    parser = argparse.ArgumentParser(description="Stripe Payment API")
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind')
    parser.add_argument('--port', type=int, default=5006, help='Port to bind')
    args = parser.parse_args()
    
    print("=" * 60)
    print("🔐 Stripe Payment API Starting...")
    print("=" * 60)
    print(f"✅ Listening on http://{args.host}:{args.port}")
    print(f"✅ Endpoints:")
    print(f"   - POST /api/create-checkout-session")
    print(f"   - POST /api/webhook")
    print(f"   - POST /api/customer-portal")
    print(f"   - GET  /health")
    print()
    print("📝 Next Steps:")
    print("   1. Set environment variables:")
    print("      export STRIPE_SECRET_KEY='sk_test_...'")
    print("      export STRIPE_PUBLISHABLE_KEY='pk_test_...'")
    print("      export STRIPE_WEBHOOK_SECRET='whsec_...'")
    print("   2. Update shop.html with your publishable key")
    print("   3. Set up webhook endpoint in Stripe Dashboard")
    print("   4. Create subscription price in Stripe Dashboard")
    print("=" * 60)
    
    app.run(host=args.host, port=args.port, debug=False)


if __name__ == '__main__':
    main()

