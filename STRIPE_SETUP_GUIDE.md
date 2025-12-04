# 💳 Stripe Integration Setup Guide

## 📋 Overview

This guide walks you through integrating Stripe payments for:
- ✅ **Sheet Music** (one-time, $2.99-$9.99)
- ✅ **MP3s** (one-time, $0.99-$4.99)
- ✅ **Trading Signals Subscription** ($19.99/month)
- ✅ **Donations** (one-time, any amount)
- ✅ **Crypto Payments** (Bitcoin, Ethereum via Stripe)

---

## 💰 Stripe Fees & Requirements

### **Good News - No Minimums!**

- **Standard Rate**: 2.9% + $0.30 per successful charge
- **No monthly fees**, no setup fees, no minimums
- **Instant payout** (or 2-day rolling)
- **Crypto payments**: Same rate + 1% crypto conversion fee

### Examples:
- $9.99 sheet music → You keep **$9.40** (Stripe takes $0.59)
- $19.99/month subscription → You keep **$19.30** (Stripe takes $0.69)
- $100 donation → You keep **$96.80** (Stripe takes $3.20)

---

## 🚀 Step-by-Step Setup

### **Step 1: Create Stripe Account** (5 minutes)

1. Go to https://stripe.com
2. Click "Start now" → Sign up
3. Verify your email
4. Complete business information:
   - Business type: Individual or LLC
   - Industry: Music/Entertainment
   - Website: brianstreckfus.com
5. Add bank account for payouts

**Note**: You'll start in "Test Mode" - perfect for development!

---

### **Step 2: Get API Keys** (2 minutes)

1. Go to https://dashboard.stripe.com/apikeys
2. Copy your keys:
   - **Publishable key** (starts with `pk_test_...`)
   - **Secret key** (starts with `sk_test_...`)

3. **Keep secret key SAFE!** Never commit to git, never share.

---

### **Step 3: Create Products in Stripe** (10 minutes)

#### **A. Trading Signals Subscription**

1. Go to https://dashboard.stripe.com/products
2. Click "Add product"
3. Fill in:
   - **Name**: Trading Signals PRO
   - **Description**: Premium algorithmic trading signals with real-time alerts
   - **Pricing model**: Standard pricing
   - **Price**: $19.99
   - **Billing period**: Monthly
   - **Currency**: USD
4. Click "Save product"
5. **Copy the Price ID** (starts with `price_...`) - you'll need this!

#### **B. Sheet Music & MP3s**

These are created dynamically when purchased, so no setup needed!

#### **C. (Optional) Create Donation Product**

1. Same process as above
2. Name: "Donation"
3. Price: Can be flexible (set in code)

---

### **Step 4: Configure Environment Variables**

On your **Mac** (where bots run):

```bash
# Add to ~/.zshrc or ~/.bash_profile
export STRIPE_SECRET_KEY="sk_test_YOUR_SECRET_KEY_HERE"
export STRIPE_PUBLISHABLE_KEY="pk_test_YOUR_PUBLISHABLE_KEY_HERE"
export STRIPE_WEBHOOK_SECRET="whsec_YOUR_WEBHOOK_SECRET_HERE"  # Get in Step 6
export DOMAIN="https://brianstreckfus.com"

# Reload shell
source ~/.zshrc
```

---

### **Step 5: Update Website Files**

#### **A. Update shop.html**

Replace line 147:
```javascript
const stripe = Stripe('pk_test_YOUR_PUBLISHABLE_KEY_HERE');
```

With your actual publishable key:
```javascript
const stripe = Stripe('pk_test_ACTUAL_KEY_FROM_STRIPE_DASHBOARD');
```

#### **B. Update API endpoint**

In `shop.html`, change:
```javascript
const response = await fetch('/api/create-checkout-session', {
```

To your actual domain:
```javascript
const response = await fetch('https://brianstreckfus.com/api/create-checkout-session', {
```

---

### **Step 6: Set Up Webhooks** (5 minutes)

Webhooks notify your server when payments succeed.

1. Go to https://dashboard.stripe.com/webhooks
2. Click "Add endpoint"
3. **Endpoint URL**: `https://brianstreckfus.com/api/webhook`
4. **Events to send**:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
5. Click "Add endpoint"
6. **Copy the Webhook Secret** (starts with `whsec_...`)
7. Add to environment variables (Step 4)

---

### **Step 7: Start the Payment API**

On your Mac:

```bash
cd /Users/olivia2/Documents/GitHub/guitar/web/WebContent

# Install dependencies
pip install stripe flask flask-cors

# Test locally first
python3 stripe_payments.py --port 5006

# Or with gunicorn
gunicorn -w 1 -b 0.0.0.0:5006 stripe_payments:app
```

**For Production**: Run on your AWS server or use a service like Railway/Render.

---

### **Step 8: Test Payments** (10 minutes)

Stripe provides test card numbers:

#### **Successful Payment**:
- Card: `4242 4242 4242 4242`
- Expiry: Any future date (e.g., 12/34)
- CVC: Any 3 digits (e.g., 123)
- ZIP: Any 5 digits (e.g., 12345)

#### **Other Test Cases**:
- **Declined**: `4000 0000 0000 0002`
- **Requires authentication**: `4000 0027 6000 3184`

Try buying:
1. A donation ($10)
2. The trading signals subscription
3. Navigate to brianstreckfus.com/shop.html

---

### **Step 9: Go Live!** 🚀

Once testing works:

1. Go to https://dashboard.stripe.com
2. Click "Activate account" (top-right)
3. Complete business verification:
   - Add bank account details
   - Verify identity (photo ID)
   - Business details
4. Switch from Test Mode → Live Mode (toggle in dashboard)
5. Get **Live API keys**:
   - `pk_live_...` (publishable)
   - `sk_live_...` (secret)
6. Update environment variables with live keys
7. Update shop.html with live publishable key
8. Test with a small real purchase ($1)

---

## 🪙 Crypto Payment Setup

Stripe now supports crypto! Here's how:

### **Option A: Stripe Crypto (Easiest)**

1. Go to https://dashboard.stripe.com/settings/payment_methods
2. Enable "Crypto"
3. Select currencies: Bitcoin, Ethereum, USDC
4. **Fee**: 2.9% + $0.30 + 1% crypto conversion = **3.9% total**
5. Customers see "Pay with Crypto" option at checkout
6. You receive USD in your bank (Stripe handles conversion)

### **Option B: Direct Crypto (More Advanced)**

For direct wallet-to-wallet (no Stripe):

1. Generate receiving addresses:
   - **Bitcoin**: Use Coinbase, Blockchain.com, or hardware wallet
   - **Ethereum**: Use MetaMask or hardware wallet
2. Display addresses on shop.html (already templated)
3. Manually verify payments (not automatic)
4. Manually send download links

**Pro**: No fees, you keep 100%  
**Con**: Manual process, no automation

---

## 📊 Cutting Out ArrangeMe Middleman

### **Current: ArrangeMe**
- They take ~40-50% commission
- You get ~$2-5 per $5-10 sale

### **Direct Sales via Stripe**
- You take ~97% (after 3% Stripe fee)
- You get ~$9.40 per $9.99 sale

### **What You Can Sell Direct**:
✅ **Public Domain Works** (Bach, Chopin, Mozart, etc.)  
✅ **Your Original Compositions**  
✅ **Your Original MP3s**  
❌ Copyrighted arrangements (still need ArrangeMe/licensing)

### **Implementation**:
1. Upload PDFs to `/web/WebContent/downloads/sheet_music/`
2. Create product in Stripe
3. After payment, send download link via email
4. (Optional) Use signed S3 URLs for secure downloads

---

## 🔐 Security Best Practices

1. **Never expose secret keys** in frontend code
2. **Always verify webhooks** using Stripe signature
3. **Use HTTPS** for all payment pages
4. **Store customer data** securely (or let Stripe handle it)
5. **Test in test mode** before going live
6. **Monitor for fraud** in Stripe Dashboard

---

## 📧 Email Setup (Optional but Recommended)

After successful payment, send download links via email:

### **Options**:

1. **SendGrid** (free tier: 100 emails/day)
2. **AWS SES** (cheap, $0.10 per 1000 emails)
3. **Gmail API** (free, use your Gmail)

### **What to Send**:
- ✅ Payment receipt
- ✅ Download link (with expiry)
- ✅ Thank you message
- ✅ For subscriptions: Access credentials

---

## 🎯 Next Steps Priority

### **Immediate** (Do This Week):
1. ✅ Create Stripe account
2. ✅ Get test API keys
3. ✅ Update shop.html with publishable key
4. ✅ Test locally with test cards

### **Short-term** (Do This Month):
1. ⏳ Set up webhook endpoint
2. ⏳ Create subscription product
3. ⏳ Upload public domain sheet music PDFs
4. ⏳ Go live with Stripe

### **Long-term** (Do This Quarter):
1. 🔮 Add email automation
2. 🔮 Build customer portal
3. 🔮 Add more products
4. 🔮 Integrate crypto wallets

---

## 💡 Revenue Projections

### **Conservative Estimates**:

| Product | Price | Sales/Month | Revenue/Month |
|---------|-------|-------------|---------------|
| Sheet Music | $5 avg | 20 | $97 |
| MP3s | $2 avg | 10 | $19 |
| Signals Subscription | $19.99 | 10 | $193 |
| Donations | $10 avg | 5 | $48 |
| **Total** | | | **$357/month** |

### **Optimistic (with marketing)**:

| Product | Price | Sales/Month | Revenue/Month |
|---------|-------|-------------|---------------|
| Sheet Music | $5 avg | 100 | $485 |
| MP3s | $2 avg | 50 | $97 |
| Signals Subscription | $19.99 | 50 | $969 |
| Donations | $10 avg | 20 | $194 |
| **Total** | | | **$1,745/month** |

**After Stripe Fees**: ~$1,693/month net

---

## 🆘 Troubleshooting

### **"Payment failed" error**
- Check API keys are correct
- Verify webhook endpoint is accessible
- Check Stripe Dashboard for error details

### **"Invalid publishable key"**
- Make sure using `pk_test_...` or `pk_live_...`
- Not the secret key (`sk_...`)

### **Webhook not receiving events**
- Verify endpoint URL is publicly accessible
- Check webhook secret is correct
- Look at Stripe Dashboard → Webhooks → Recent deliveries

### **Subscription not working**
- Verify Price ID is correct
- Check product is active in Stripe
- Ensure mode='subscription' in session

---

## 📚 Resources

- **Stripe Docs**: https://stripe.com/docs
- **Stripe Checkout**: https://stripe.com/docs/payments/checkout
- **Stripe Subscriptions**: https://stripe.com/docs/billing/subscriptions
- **Stripe Webhooks**: https://stripe.com/docs/webhooks
- **Test Cards**: https://stripe.com/docs/testing
- **Stripe Crypto**: https://stripe.com/docs/crypto

---

## ✅ Checklist

- [ ] Create Stripe account
- [ ] Verify email & bank account
- [ ] Get test API keys
- [ ] Create subscription product
- [ ] Update shop.html with publishable key
- [ ] Update stripe_payments.py with API keys
- [ ] Test checkout with test cards
- [ ] Set up webhook endpoint
- [ ] Test subscription flow
- [ ] Go live (activate account)
- [ ] Switch to live API keys
- [ ] Make first real test purchase
- [ ] Upload sheet music PDFs
- [ ] Set up email delivery
- [ ] Launch! 🚀

---

**Need Help?** Check Stripe's excellent docs or their support chat (very responsive!).

Good luck! 💪

