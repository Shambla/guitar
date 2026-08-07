# Direct MP3 sales (Stripe + site hosting)

Industry-standard light pattern used here (Bandcamp / gumroad-style lite):

1. **Public 30-second preview** — safe to host openly (`audio/previews/`).
2. **Stripe Payment Link** — buyer pays on Stripe (same approach as Trading Signals).
3. **Success redirect** → `audio-purchase.html?track=…&paid=true` with the full download button.
4. **Full MP3** on your site under `audio/fulldownloads/` (not linked from the public catalog card).

## Dedicated storefront (recommended for beats)

Sheet music stays on `catalog.html`. Beat / MP3 buyers use:

- **`mp3-downloads.html`** — browse + preview UI (loads `mp3-downloads-data.json`)
- Catalog CTA / nav: **MP3 Downloads** → that page
- Same purchase page: `audio-purchase.html` (checks `mp3-downloads-data.json` first, then `catalog-data.json`)

Paste each track’s real `https://buy.stripe.com/...` into `mp3-downloads-data.json` → `direct_sale.stripe_payment_link`.

### Product ID vs Payment Link (easy mix-up)

| What you created | Looks like | Does the site use it? |
|------------------|------------|------------------------|
| **Product** | `prod_…` (e.g. `prod_V1wVOuSkqREdYb`) | No — bookkeeping only (`stripe_product_id`) |
| **Payment Link** | `https://buy.stripe.com/…` | **Yes** — this is the Buy button URL |

A Product is the name/price/description in Stripe. A **Payment Link** is the shareable checkout URL built *from* that product.

**Get the URL after creating the product:**

1. Stripe Dashboard → **Payment links** → **Create payment link** (or open an existing one)
2. Choose your product (e.g. Rap backing track 1 / `prod_V1wVOuSkqREdYb`)
3. Under **After payment**, set redirect to:  
   `https://brianstreckfus.com/audio-purchase.html?track=rap-1-may-2026&from=mp3&paid=true`
4. Save → copy the **Payment link** (`buy.stripe.com/...`) and paste into `stripe_payment_link` for that track

Until step 4 is done, the site still shows “Stripe link not configured.”

**TODO:** Give MP3 tracks more memorable names (placeholders like “Rap 1 — May 2026” → distinctive titles). Tracked in `website_todo.md`.

Success URL pattern:

```
https://brianstreckfus.com/audio-purchase.html?track=rap-1-may-2026&from=mp3&paid=true
```

## What we are intentionally *not* doing (for now)

| Idea | Verdict |
|------|---------|
| Rotating download URLs | Needs a backend; overkill until you have real piracy volume |
| Coupon codes that “reveal” the URL | Unusual for music; easy to share; Stripe already handles discounts if you want them |
| Claiming client-side `?paid=true` is secure | It isn’t — anyone can append it. Fine at low traffic; upgrade later with Stripe webhooks + signed URLs |

**Recommendation:** ship this simple flow now; worry about hard DRM later if needed.

## Off Kilter example (practice track)

Catalog id: `off-kiltergrit-120-bpm-a-minor` (also aliased from `off-kilter-grit-120-bpm-a-minor`).

### 1. Drop in audio files

```
web/WebContent/audio/previews/off-kilter-grit-120-bpm-a-minor-30s.mp3   ← public preview
web/WebContent/audio/fulldownloads/off-kilter-grit-120-bpm-a-minor.mp3 ← full track
```

Full downloads are gitignored so large binaries don’t clog the repo. Upload them with your usual AWS/site deploy (same as other static assets), or force-add if you prefer Git.

### 2. Create a Stripe Payment Link

1. Stripe Dashboard → Payment Links → Create  
2. Product: “Off Kilter Grit 120 BPM A minor” — price matching catalog (`$3.99` on the SMD-linked row)  
3. After payment → Success URL:

```
https://brianstreckfus.com/audio-purchase.html?track=off-kiltergrit-120-bpm-a-minor&paid=true
```

Cancel URL:

```
https://brianstreckfus.com/audio-purchase.html?track=off-kiltergrit-120-bpm-a-minor
```

4. Paste the `https://buy.stripe.com/...` URL into `catalog-data.json` → `direct_sale.stripe_payment_link` for that track.

### 3. Go live on the catalog

In `script/catalog.js`:

```js
const DIRECT_AUDIO_SALES_LIVE = true;  // was false
```

Until that flag is true **and** the Payment Link is real (not `YOUR_PAYMENT_LINK_HERE`):

- Catalog still shows sheet-music “Open Listing” when an SMD URL exists  
- Or “Preview / Buy page” in practice mode with `?catalog_preview=1` on catalog.html  
- Purchase page always works locally for testing the player UI

### 4. Local test

```bash
cd ~/Documents/GitHub/guitar/web/WebContent
python3 -m http.server 8000
```

Open:

- Preview page: `http://localhost:8000/audio-purchase.html?track=off-kiltergrit-120-bpm-a-minor`  
- Fake paid state: add `&paid=true` (download appears — remember this is not real security)

## Upgrade path (when traffic matters)

Stripe Checkout Session or Payment Link webhook → your small AWS Lambda/API verifies payment → returns a short-lived signed URL to S3. Same UX; stronger gate.
