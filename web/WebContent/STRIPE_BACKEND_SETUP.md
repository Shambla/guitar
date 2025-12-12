# Stripe Backend Setup Guide

## The Problem

Your production site (`brianstreckfus.com`) can't reach the Stripe backend because it's only running locally. The backend needs to be accessible from the internet for production.

## Quick Answer

**You don't HAVE to use AWS**, but you DO need the backend accessible from the internet. Here are your options:

---

## Option 1: Deploy to Simple Cloud Service (Easiest Production)

### Heroku (Free Tier Available)
```bash
# Install Heroku CLI
# Create app
heroku create your-stripe-backend

# Set environment variables
heroku config:set stripe_private_key=sk_live_...
heroku config:set stripe_public_key=pk_live_...

# Deploy
git push heroku main
```

### Railway (Simple & Fast)
1. Go to https://railway.app
2. New Project → Deploy from GitHub
3. Select your repo
4. Set environment variables
5. Deploy

### Render (Free Tier)
1. Go to https://render.com
2. New Web Service
3. Connect GitHub repo
4. Set environment variables
5. Deploy

**Then update `getStripeApiBase()` in signals.html to point to your deployed URL.**

---

## Option 2: Deploy to AWS (As Documented)

See `AWS_STRIPE_SETUP.md` for full AWS Lambda/Elastic Beanstalk setup.

---

## Option 3: Run on Your Own Server

If you have a VPS or server:

1. **SSH into your server**
2. **Upload `stripe_payments.py`**:
   ```bash
   scp stripe_payments.py user@your-server:/path/to/app/
   ```
3. **Set environment variables**:
   ```bash
   export stripe_private_key="sk_live_..."
   export stripe_public_key="pk_live_..."
   ```
4. **Install dependencies**:
   ```bash
   pip3 install stripe flask flask-cors python-dotenv
   ```
5. **Run as service** (using systemd, PM2, or screen):
   ```bash
   python3 stripe_payments.py --port 5006
   ```
6. **Update frontend** to point to your server URL

---

## Current Status

- ✅ **Local**: Works perfectly (`http://localhost:5006`)
- ❌ **Production**: Backend not accessible (needs deployment)

---

## Recommended Next Steps

1. **For production**: Deploy to Heroku/Railway (Option 1) - easiest
2. **For long-term**: Deploy to AWS (Option 2) - most robust
3. **If you have a server**: Run on your own VPS (Option 3)

---

## Testing After Deployment

Once your backend is deployed:

1. Visit: `https://your-backend-url.com/api/stripe-public-key`
2. Should return: `{"publicKey": "pk_live_..."}`
3. Update `signals.html` to use your backend URL
4. Test subscription flow

---

## MASTERMASTER_control_bot5.py Note

The control bot runs the Stripe server locally on port 5006. This is perfect for:
- ✅ Local development
- ✅ Testing
- ❌ Production (needs deployment to a cloud service)

For production, you'll need to deploy the backend separately, or modify the control bot to deploy it automatically (future enhancement).

