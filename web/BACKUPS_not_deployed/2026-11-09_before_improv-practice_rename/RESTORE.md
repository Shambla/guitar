# Backup before renaming mp3-downloads.html → improv-practice.html (2026-11-09)

This folder is outside `web/WebContent`, so the S3 deploy never uploads it and nothing links to it.
The five pages here are exact copies taken right before the rename. Git tag `before-improv-practice-rename`
marks the same moment (commit db0105857).

## Planned changes

1. Rename `web/WebContent/mp3-downloads.html` → `web/WebContent/improv-practice.html` (`git mv`, history kept).
2. Add a new small `web/WebContent/mp3-downloads.html` that forwards to `improv-practice.html`, keeping
   everything after `?` and `#` (`?key=`, `?style=`, `?filter=`, `?dev=`, `#browse-mp3s`, `#free-scales`).
3. Point links at the new name:
   - `index.html` — nav "Improv Practice"
   - `catalog.html` — nav link and the "MP3 Downloads" button
   - `audio-purchase.html` — nav link, "Back to MP3 downloads" (twice), missing-track message, `browseHref`
   - `improv-practice.html` — its own nav link and the `?dev=` comment
   - `practice-lab.html` — "Store" link
4. Comments/docs only (nothing breaks if skipped): `script/practice-lab.js`, `script/beauty-scales-viewer.js`,
   `song-keys.json` `_about`, `DIRECT_AUDIO_SALES.md`, `website_todo.md`.

Not renamed (still loaded by the page under their current names): `mp3-downloads-data.json`,
`script/mp3-downloads.js`, `script/practice-lab.js`, `song-keys.json`, the PDFs, and the CSS class
`mp3-downloads-page`.

## Going back

Any one of these restores the old URL. Each deploy takes about 2 minutes after the push.

- Undo just the rename commit (keeps everything done since):
  `git revert <rename commit>` then `git push origin master`
- Put the five pages back from this folder:
  `git rm web/WebContent/improv-practice.html`, copy the five files here into `web/WebContent/`,
  commit, push.
- Reset the site files to the tagged moment:
  `git checkout before-improv-practice-rename -- web/WebContent/` then
  `git rm web/WebContent/improv-practice.html`, commit, push.
  This also rolls back every other site edit made after the tag, including the signals JSON
  until the next auto-sync, so prefer the first two.
