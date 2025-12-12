# Stripe Payment Link Setup Guide

This guide explains how to set up Stripe Payment Links for your trading signals subscription, **without needing a backend server**.

## Why Payment Links?

- ✅ **No backend server required** - Stripe handles everything
- ✅ **No ngrok or tunneling needed** - Works immediately
- ✅ **Simple setup** - Just create a link in Stripe Dashboard
- ✅ **Free to use** - No additional costs beyond Stripe's standard fees

## Step-by-Step Setup

### 1. Create a Payment Link in Stripe Dashboard

1. Go to: https://dashboard.stripe.com/payment-links
2. Click **"Create payment link"** button
3. Configure your product:
   - **Product name**: "Trading Signals PRO"
   - **Description**: "Premium algorithmic trading signals with real-time alerts"
   - **Price**: $9.99
   - **Billing**: Select **"Recurring"** → **"Monthly"**
   - **Trial period**: Set to **7 days** (optional, but recommended)

### 2. Configure Success URL

1. In the Payment Link settings, find **"After payment"** section
2. Set **Success URL** to:
   ```
   https://brianstreckfus.com/signals.html?paid=true
   ```
   This is important! When users complete payment, they'll be redirected back to your site with `?paid=true` in the URL, which grants them permanent access.

3. Set **Cancel URL** to:
   ```
   https://brianstreckfus.com/signals.html
   ```

### 3. Copy Your Payment Link

1. After creating the Payment Link, Stripe will give you a URL like:
   ```
   https://buy.stripe.com/abc123xyz...
   ```
2. Copy this entire URL

### 4. Update signals.html

1. Open `signals.html` in your editor
2. Find this line (around line 2280):
   ```javascript
   const STRIPE_PAYMENT_LINK = 'https://buy.stripe.com/YOUR_PAYMENT_LINK_HERE';
   ```
3. Replace `YOUR_PAYMENT_LINK_HERE` with your actual Payment Link URL:
   ```javascript
   const STRIPE_PAYMENT_LINK = 'https://buy.stripe.com/abc123xyz...';
   ```
4. Save the file

### 5. Test It!

1. Clear your browser's localStorage to simulate a new user:
   ```javascript
   // In browser console:
   localStorage.removeItem('trial_start_date');
   localStorage.removeItem('is_subscribed');
   ```
2. Visit your site - you should see signals (7-day trial active)
3. Wait 7 days (or manually expire the trial by setting an old date):
   ```javascript
   localStorage.setItem('trial_start_date', '2024-01-01T00:00:00.000Z');
   location.reload();
   ```
4. You should see "Your Trial Has Expired" with a "Subscribe Now" button
5. Click the button - it should open your Stripe Payment Link
6. Complete a test payment (use Stripe test card: `4242 4242 4242 4242`)
7. After payment, you should be redirected back with `?paid=true` in the URL
8. Signals should now be visible permanently!

## How It Works

1. **First 7 days**: Users see all signals for free (trial period)
2. **After 7 days**: Signals are hidden, user sees "Subscribe Now" button
3. **User clicks button**: Opens Stripe Payment Link in new tab
4. **User pays**: Stripe handles the payment
5. **After payment**: User is redirected to `signals.html?paid=true`
6. **Permanent access**: The `?paid=true` parameter grants permanent access (stored in localStorage)

## Important Notes

- **Permanent access**: Once a user pays, they get **permanent access forever** (stored in browser localStorage)
- **No recurring payments yet**: This is a one-time payment for permanent access. When you set up AWS, you can switch to recurring subscriptions.
- **localStorage-based**: Access is stored in the browser. If user clears browser data, they'll need to pay again (or you can implement email-based tracking later).
- **No backend needed**: Everything works client-side!

## Troubleshooting

**Payment Link not working?**
- Make sure you copied the entire URL (it's long!)
- Check that the URL starts with `https://buy.stripe.com/`
- Verify the Success URL is set correctly in Stripe Dashboard

**User paid but still can't see signals?**
- Check browser console for errors
- Verify the redirect URL includes `?paid=true`
- Check localStorage: `localStorage.getItem('is_subscribed')` should be `'true'`

**Want to test without waiting 7 days?**
- Open browser console and run:
  ```javascript
  localStorage.setItem('trial_start_date', '2024-01-01T00:00:00.000Z');
  location.reload();
  ```

## Next Steps (When Ready for AWS)

When you're ready to set up recurring subscriptions with AWS:
1. Deploy `stripe_payments.py` to AWS (Lambda + API Gateway, or EC2)
2. Update `signals.html` to use the backend API instead of Payment Links
3. Implement proper subscription management (cancel, renew, etc.)
4. Add email-based access tracking (not just localStorage)

For now, Payment Links are the simplest solution that works immediately!

