# Full MP3 downloads (after payment)

**Canonical folder:** `web/WebContent/audio/fulldownloads/` (same tree as previews in `audio/previews/`).

Kebab-case files in this folder (e.g. `reggae-9-e-minor.mp3`) are what the live site serves. Paths are in `mp3-downloads-data.json` → `direct_sale.full_audio`.

They are tracked in git so a push to `master` deploys them to S3 with the rest of the site.

**Catalog tail (2026-10-26):** Last full files added here are the Egypt tracks in `mp3-downloads-data.json`, through `egypt-13-f-sharp-harmonic-minor.mp3`. Tracks under 2 minutes stay out of this folder. Next track = new MP3 in this folder + 30s preview + JSON row + Stripe Payment Link (see `DIRECT_AUDIO_SALES.md`).

Human-named DAW export folders (`Rap May 2026/`, `Reggae/`, `Bossa/`) may stay local for organization; **site filenames** must match the kebab-case names above when copied into `fulldownloads/`.
