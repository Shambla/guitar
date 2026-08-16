# Full MP3 downloads (after payment)

Kebab-case files in this folder (e.g. `reggae-9-e-minor.mp3`) are what the live site serves. Paths are in `mp3-downloads-data.json` → `direct_sale.full_audio`.

They are tracked in git so a push to `master` deploys them to S3 with the rest of the site.

Human-named DAW export folders (`Rap May 2026/`, `Reggae/`, `Bossa/`) stay local and are gitignored.
