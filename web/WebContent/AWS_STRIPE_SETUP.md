# AWS Deployment Guide for Stripe Payment Server

## Overview

This guide explains how to deploy the Stripe payment server (`stripe_payments.py`) to AWS for production use, replacing the local `MASTERMASTER_control_bot5.py` setup. This provides automatic scaling, high availability, and eliminates the need for manual server management.

## Current Setup

- **Local Server**: `stripe_payments.py` runs on port 5006
- **Location**: `/Users/olivia2/Documents/GitHub/guitar/web/WebContent/stripe_payments.py`
- **Environment Variables**: `.env` file with `stripe_public_key` and `stripe_private_key`
- **Frontend**: `signals.html` connects to backend at `http://localhost:5006` (local) or same origin (production)

## AWS Deployment Options

### Option 1: AWS Lambda + API Gateway (Recommended for Cost-Effectiveness)
**Best for**: Low to moderate traffic, pay-per-request pricing
- **Pros**: 
  - Very cost-effective (pay only for requests)
  - Automatic scaling
  - No server management
  - Built-in high availability
- **Cons**: 
  - 15-minute execution timeout limit
  - Cold starts (minimal with proper configuration)
  - Requires code adaptation for Lambda

### Option 2: AWS Elastic Beanstalk (Recommended for Simplicity)
**Best for**: Quick deployment, familiar Flask app structure
- **Pros**:
  - Minimal code changes needed
  - Automatic load balancing and scaling
  - Easy deployment via CLI or console
  - Built-in monitoring
- **Cons**:
  - Always-on server costs (~$10-30/month minimum)
  - More expensive than Lambda for low traffic

### Option 3: AWS EC2 (Most Control)
**Best for**: Full control, custom configurations
- **Pros**:
  - Complete control over environment
  - Can run alongside other services
  - Familiar server management
- **Cons**:
  - Requires server management
  - Manual scaling
  - Higher maintenance overhead

## Recommended: AWS Lambda + API Gateway Setup

### Prerequisites

1. AWS Account
2. AWS CLI installed and configured
3. Python 3.9+ (for local testing)
4. Stripe account with API keys

### Step 1: Prepare Lambda-Compatible Code

Create a new file `stripe_payments_lambda.py`:

```python
#!/usr/bin/env python3
"""
Stripe Payment Lambda Handler
Adapted from stripe_payments.py for AWS Lambda
"""

import os
import json
import stripe
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Load environment variables (Lambda will use AWS Systems Manager Parameter Store or Secrets Manager)
STRIPE_SECRET_KEY = os.getenv("stripe_private_key") or os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = os.getenv("stripe_public_key") or os.getenv("STRIPE_PUBLISHABLE_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

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
    }
}

# Lambda handler function
def lambda_handler(event, context):
    """
    AWS Lambda handler for Stripe payment API
    
    Event structure:
    {
        "httpMethod": "GET|POST",
        "path": "/api/stripe-public-key",
        "body": "..." (JSON string for POST requests),
        "headers": {...}
    }
    """
    try:
        http_method = event.get("httpMethod", "GET")
        path = event.get("path", "")
        
        # CORS headers
        headers = {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",  # Configure properly for production
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        }
        
        # Handle OPTIONS (CORS preflight)
        if http_method == "OPTIONS":
            return {
                "statusCode": 200,
                "headers": headers,
                "body": ""
            }
        
        # Route requests
        if path == "/api/stripe-public-key" and http_method == "GET":
            return {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps({"publicKey": STRIPE_PUBLISHABLE_KEY})
            }
        
        elif path == "/api/create-checkout-session" and http_method == "POST":
            body = json.loads(event.get("body", "{}"))
            result = create_checkout_session(body)
            return {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps(result)
            }
        
        elif path == "/api/webhook" and http_method == "POST":
            result = handle_webhook(event)
            return {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps(result)
            }
        
        elif path == "/health" and http_method == "GET":
            return {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps({"ok": True, "service": "stripe_payments_lambda"})
            }
        
        else:
            return {
                "statusCode": 404,
                "headers": headers,
                "body": json.dumps({"error": "Not found"})
            }
    
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"error": str(e)})
        }


def create_checkout_session(data: Dict[str, Any]):
    """Create a Stripe Checkout Session"""
    try:
        product_type = data.get('productType')
        
        if product_type == 'subscription':
            price_id = data.get('priceId')
            trial_days = data.get('trial_days', 7)
            
            if not price_id:
                # Create price on-the-fly
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
            
            # Get domain from environment or use default
            domain = os.getenv("DOMAIN", "https://brianstreckfus.com")
            
            session_params = {
                'payment_method_types': ['card'],
                'mode': 'subscription',
                'line_items': [{
                    'price': price_id,
                    'quantity': 1
                }],
                'success_url': f'{domain}/signals.html?session_id={{CHECKOUT_SESSION_ID}}',
                'cancel_url': f'{domain}/signals.html',
                'subscription_data': {
                    'trial_period_days': trial_days
                },
                'payment_method_collection': 'if_required'
            }
            
            session = stripe.checkout.Session.create(**session_params)
            
            return {
                "sessionId": session.id,
                "id": session.id,
                "url": session.url
            }
        
        else:
            return {"error": "Invalid product type"}
    
    except Exception as e:
        return {"error": str(e)}


def handle_webhook(event):
    """Handle Stripe webhook events"""
    try:
        payload = event.get("body", "")
        sig_header = event.get("headers", {}).get("stripe-signature", "")
        
        # Verify webhook signature
        event_obj = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
        
        # Handle different event types
        event_type = event_obj['type']
        
        if event_type == 'checkout.session.completed':
            session = event_obj['data']['object']
            log_payment(session)
        
        elif event_type == 'customer.subscription.created':
            subscription = event_obj['data']['object']
            log_subscription(subscription)
        
        elif event_type == 'customer.subscription.deleted':
            subscription = event_obj['data']['object']
            log_subscription_cancellation(subscription)
        
        elif event_type == 'invoice.payment_succeeded':
            invoice = event_obj['data']['object']
            log_recurring_payment(invoice)
        
        return {"success": True}
    
    except ValueError as e:
        return {"error": "Invalid payload"}
    except stripe.error.SignatureVerificationError as e:
        return {"error": "Invalid signature"}
    except Exception as e:
        return {"error": str(e)}


def log_payment(data: Dict[str, Any]):
    """Log payment to CloudWatch"""
    import logging
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.info(f"Payment successful: {json.dumps(data)}")


def log_subscription(data: Dict[str, Any]):
    """Log subscription event"""
    import logging
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.info(f"Subscription created: {json.dumps(data)}")


def log_subscription_cancellation(data: Dict[str, Any]):
    """Log subscription cancellation"""
    import logging
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.info(f"Subscription cancelled: {json.dumps(data)}")


def log_recurring_payment(data: Dict[str, Any]):
    """Log recurring payment"""
    import logging
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.info(f"Recurring payment: {json.dumps(data)}")
```

### Step 2: Create Deployment Package

```bash
# Create deployment directory
mkdir stripe_lambda_deploy
cd stripe_lambda_deploy

# Copy Lambda handler
cp ../stripe_payments_lambda.py lambda_function.py

# Install dependencies
pip install stripe -t .

# Create deployment zip
zip -r stripe_payments_lambda.zip . -x "*.pyc" "__pycache__/*" "*.dist-info/*"
```

### Step 3: Store Secrets in AWS Systems Manager Parameter Store

```bash
# Store Stripe keys securely
aws ssm put-parameter \
  --name "/stripe/private_key" \
  --value "sk_live_..." \
  --type "SecureString" \
  --region us-east-1

aws ssm put-parameter \
  --name "/stripe/public_key" \
  --value "pk_live_..." \
  --type "String" \
  --region us-east-1

aws ssm put-parameter \
  --name "/stripe/webhook_secret" \
  --value "whsec_..." \
  --type "SecureString" \
  --region us-east-1

aws ssm put-parameter \
  --name "/stripe/domain" \
  --value "https://brianstreckfus.com" \
  --type "String" \
  --region us-east-1
```

### Step 4: Create Lambda Function

```bash
# Create Lambda function
aws lambda create-function \
  --function-name stripe-payments-api \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-execution-role \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://stripe_payments_lambda.zip \
  --timeout 30 \
  --memory-size 256 \
  --environment Variables={} \
  --region us-east-1
```

### Step 5: Update Lambda to Read from Parameter Store

Add this to your Lambda function code (or use Lambda Layers):

```python
import boto3

def get_parameter(name, decrypt=False):
    """Get parameter from AWS Systems Manager"""
    ssm = boto3.client('ssm', region_name='us-east-1')
    response = ssm.get_parameter(Name=name, WithDecryption=decrypt)
    return response['Parameter']['Value']

# In lambda_handler, before processing:
STRIPE_SECRET_KEY = get_parameter('/stripe/private_key', decrypt=True)
STRIPE_PUBLISHABLE_KEY = get_parameter('/stripe/public_key')
STRIPE_WEBHOOK_SECRET = get_parameter('/stripe/webhook_secret', decrypt=True)
DOMAIN = get_parameter('/stripe/domain')
```

### Step 6: Create API Gateway

```bash
# Create REST API
aws apigateway create-rest-api \
  --name stripe-payments-api \
  --region us-east-1

# Note the API ID from output, then create resources and methods
# This is easier done via AWS Console or Terraform/CloudFormation
```

**Via AWS Console:**
1. Go to API Gateway → Create API → REST API
2. Create resources: `/api/stripe-public-key`, `/api/create-checkout-session`, `/api/webhook`, `/health`
3. Create methods (GET/POST) for each
4. Set integration type to Lambda Function
5. Select your `stripe-payments-api` function
6. Deploy API to a stage (e.g., `prod`)
7. Note the API endpoint URL

### Step 7: Update Frontend

Update `signals.html` to use the API Gateway endpoint:

```javascript
// Update getStripeApiBase function
function getStripeApiBase() {
    const hostname = window.location.hostname;
    
    // Production: Use API Gateway endpoint
    if (hostname === 'brianstreckfus.com' || hostname.includes('brianstreckfus.com')) {
        return 'https://YOUR_API_GATEWAY_ID.execute-api.us-east-1.amazonaws.com/prod';
    }
    
    // Local development
    if (hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '') {
        return 'http://localhost:5006';
    }
    
    // Default to same origin
    return window.location.origin;
}
```

### Step 8: Configure Stripe Webhook

1. Go to Stripe Dashboard → Webhooks
2. Add endpoint: `https://YOUR_API_GATEWAY_ID.execute-api.us-east-1.amazonaws.com/prod/api/webhook`
3. Select events:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
4. Copy webhook signing secret to AWS Parameter Store

## Alternative: AWS Elastic Beanstalk Setup

### Step 1: Prepare Application

Create `application.py` (Flask app entry point):

```python
from stripe_payments import app

if __name__ == "__main__":
    app.run()
```

### Step 2: Create `requirements.txt`

```
stripe==14.0.1
flask==3.1.0
flask-cors==6.0.1
python-dotenv==1.0.1
gunicorn==21.2.0
```

### Step 3: Create `Procfile`

```
web: gunicorn --bind 0.0.0.0:8000 stripe_payments:app
```

### Step 4: Create `.ebextensions/stripe.config`

```yaml
option_settings:
  aws:elasticbeanstalk:application:environment:
    stripe_private_key: 'sk_live_...'  # Or use Parameter Store
    stripe_public_key: 'pk_live_...'
    STRIPE_WEBHOOK_SECRET: 'whsec_...'
    DOMAIN: 'https://brianstreckfus.com'
```

### Step 5: Deploy

```bash
# Install EB CLI
pip install awsebcli

# Initialize
eb init -p python-3.11 stripe-payments-api

# Create environment
eb create stripe-payments-prod

# Deploy
eb deploy
```

## Security Best Practices

### 1. Use AWS Secrets Manager (Better than Parameter Store)

```python
import boto3
import json

def get_secret(secret_name):
    """Get secret from AWS Secrets Manager"""
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# Usage
secrets = get_secret('stripe-keys')
STRIPE_SECRET_KEY = secrets['stripe_private_key']
STRIPE_PUBLISHABLE_KEY = secrets['stripe_public_key']
```

### 2. IAM Roles and Policies

**Lambda Execution Role Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter",
        "ssm:GetParameters"
      ],
      "Resource": "arn:aws:ssm:us-east-1:ACCOUNT_ID:parameter/stripe/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

### 3. API Gateway Security

- Enable API key authentication for production
- Use AWS WAF for DDoS protection
- Set up rate limiting
- Enable CloudWatch logging

## Monitoring and Logging

### CloudWatch Metrics

Monitor:
- Lambda invocations
- Error rates
- Duration
- API Gateway 4xx/5xx errors

### CloudWatch Alarms

Set up alarms for:
- High error rates (>5%)
- High latency (>2 seconds)
- Unusual traffic spikes

### Logging

All Lambda logs automatically go to CloudWatch Logs:
- `/aws/lambda/stripe-payments-api`

## Cost Estimation

### Lambda + API Gateway (Low Traffic: ~1000 requests/month)
- Lambda: $0.20 (1M free requests)
- API Gateway: $3.50 (1M free requests)
- **Total: ~$3.70/month**

### Elastic Beanstalk (Always-On)
- EC2 t3.micro: ~$7-10/month
- Load Balancer: ~$16/month
- **Total: ~$23-26/month**

## Migration Checklist

- [ ] Create AWS account and configure CLI
- [ ] Store Stripe keys in AWS Secrets Manager
- [ ] Create Lambda function or Elastic Beanstalk app
- [ ] Set up API Gateway
- [ ] Test endpoints (health, public key, checkout)
- [ ] Configure Stripe webhook endpoint
- [ ] Update frontend to use new API endpoint
- [ ] Test full subscription flow
- [ ] Set up CloudWatch alarms
- [ ] Update DNS/domain if needed
- [ ] Monitor for 24-48 hours
- [ ] Remove local server from MASTERMASTER_control_bot5.py

## Testing

### Local Testing with SAM (Serverless Application Model)

```bash
# Install SAM CLI
pip install aws-sam-cli

# Initialize project
sam init

# Test locally
sam local start-api
```

### Test Endpoints

```bash
# Health check
curl https://YOUR_API_GATEWAY_ID.execute-api.us-east-1.amazonaws.com/prod/health

# Get public key
curl https://YOUR_API_GATEWAY_ID.execute-api.us-east-1.amazonaws.com/prod/api/stripe-public-key

# Create checkout session (POST)
curl -X POST https://YOUR_API_GATEWAY_ID.execute-api.us-east-1.amazonaws.com/prod/api/create-checkout-session \
  -H "Content-Type: application/json" \
  -d '{"productType":"subscription","trial_days":7}'
```

## Troubleshooting

### Common Issues

1. **CORS Errors**: Ensure API Gateway has CORS enabled
2. **Timeout Errors**: Increase Lambda timeout (max 15 minutes)
3. **Cold Starts**: Use provisioned concurrency for critical paths
4. **Webhook Failures**: Verify webhook secret in Parameter Store
5. **Parameter Access Denied**: Check IAM role permissions

## Support Resources

- AWS Lambda Documentation: https://docs.aws.amazon.com/lambda/
- Stripe API Documentation: https://stripe.com/docs/api
- API Gateway Documentation: https://docs.aws.amazon.com/apigateway/

## Notes for Developer

- The current `stripe_payments.py` uses Flask - Lambda version uses direct handler
- Environment variables should be stored in AWS Secrets Manager (not hardcoded)
- Webhook endpoint must be publicly accessible
- Consider using AWS CloudFormation or Terraform for infrastructure as code
- Set up automated deployments via GitHub Actions or AWS CodePipeline
- Monitor costs via AWS Cost Explorer

