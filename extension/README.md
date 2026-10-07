# Mirage browser extension (ambient scoring)

Scores job postings as you browse LinkedIn Jobs and Indeed. No clicks,
no copy-paste. The badge appears on the page by itself.

## How it works

The content script reads the posting text from the page DOM (your own
browser, so job boards cannot block it), sends it to the Mirage scoring
API, and stamps a small score badge on the page. Each URL is scored
once. If the API is unreachable the script stays silent and never
breaks the page.

## Setup

1. Deploy the scoring API (`api/`). Note its public URL.
2. In `content.js`, replace `__MIRAGE_API_URL__` with that URL.
3. In `manifest.json`, replace `__MIRAGE_API_ORIGIN__` with the same
   URL's origin (for example `https://mirage-api-xxxx.up.railway.app`).
4. Add an `icon128.png` (128x128 Mirage logo).
5. Open `chrome://extensions`, enable Developer mode, "Load unpacked",
   pick this folder.

## Publishing

The Chrome Web Store needs his developer account (one time $5 fee).
That step is his: Developer Dashboard, upload this folder as a zip,
fill the listing, submit for review.
