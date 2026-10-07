# Mirage

Every job hunter knows the feeling. You find the perfect role, you tailor the resume, you wait two weeks, and nothing. The posting was never real. It was a ghost, reposted for months to farm resumes, or bait for a scam.

Try it live: https://mirage-production-db25.up.railway.app

Mirage reads a job posting the way a skeptic would. Paste the text, and seconds later you hold the verdict. A legitimacy score, every red flag named in plain English, and the exact reason behind the call. No more perfect applications sent into the void.

## How it works

Mirage runs two passes over a posting.

The first pass is a rules engine. It checks for the classic tells. Requests for money, contact only through Telegram or WhatsApp, salaries that make no sense, no real company identity, pressure language, and postings so thin they say nothing at all. Every tell carries a weight, and the weights add up to a score from 0 to 100.

The second pass is optional. Set a Google API key and Mirage asks Gemini for a second opinion, a short plain English read on the same posting. Gemini is the default because its free tier keeps the product free at scale. A Claude key still works as a fallback. No key, no problem. The rules engine stands on its own.

## Quick start

```bash
pip install -r requirements.txt

python -m mirage --file posting.txt
python -m mirage --url https://example.com/jobs/123
python -m mirage --text "We are hiring..."
```

More options:

```bash
python -m mirage --file posting.txt --format json
python -m mirage --file posting.txt --posted 2026-06-01
python -m mirage --file posting.txt --no-llm
```

Set `GOOGLE_API_KEY` (get one free at Google AI Studio) to enable the
second opinion pass via Gemini. `ANTHROPIC_API_KEY` still works as a
fallback. Force a provider with `MIRAGE_LLM_PROVIDER=gemini|claude|none`,
and pick the Gemini model with `MIRAGE_GEMINI_MODEL` (default
`gemini-2.5-flash`).

## The verdict

| Score  | Verdict      | What it means                             |
|--------|--------------|-------------------------------------------|
| 80-100 | Legitimate   | No serious red flags found.               |
| 55-79  | Caution      | Worth a closer look before you apply.     |
| 30-54  | Suspicious   | Real problems here. Verify independently. |
| 0-29   | Likely ghost | Walk away, or verify very carefully.      |

## Signals

Each signal below is one check in the rules engine.

- **Money request** (critical). The posting asks you to pay anything. Fees, deposits, gift cards. Real employers never do this.
- **Too good combo** (critical). No experience plus work from home plus high pay. The classic scam shape.
- **Off platform contact** (high). Contact runs only through Telegram, WhatsApp, or Signal, with no company email anywhere.
- **Salary anomaly** (high). Pay figures that make no sense, like five figure monthly pay for a role needing no experience.
- **Anonymous employer** (high). No real company identity. Phrases like our client with no name attached.
- **Free email only** (medium). The only contact is a free email account and no company website is listed.
- **Thin description** (medium). The posting says almost nothing about the actual work.
- **Stale posting** (medium). Posted over 60 days ago and still open. Perpetual reposts are a ghost pattern. Needs `--posted`.
- **Pressure language** (low). Urgent hiring, limited slots, apply immediately. Real roles rarely beg.
- **Buzzword stuffing** (low). Rockstars and ninjas wanted. Usually a sign nobody thought about the role.
- **Vague pay** (low). Big talk about competitive packages, zero numbers anywhere.

## Limitations

Mirage analyzes text. It does not browse the web for you.

The command line accepts a `--url` flag, and it works for ordinary pages. But the big job boards, Indeed and LinkedIn first among them, block automated readers outright. No header trick or reader proxy gets through reliably. That is their bot protection doing its job, not a bug in Mirage.

For that reason the live demo is text only. Copy the posting, paste it in, and the analysis is identical. A link that cannot be fetched is not a failed analysis, it is a site refusing to be read, and pasting the text sidesteps it completely.

## Browser extension

The extension kills copy-paste for good. It watches the job pages you
already visit on LinkedIn Jobs and Indeed, reads the posting from your
own browser (so no bot blocking), scores it through the API below, and
stamps a small score badge on the page. Zero clicks. See `extension/`
for setup and publishing notes.

## Scoring API

`api/` is a small FastAPI service that powers the extension. `POST
/score` takes posting text and returns the score, verdict, and top
signals. Rate limited per IP. Deploy it as its own Railway service
with `GOOGLE_API_KEY` set, then point the extension at its URL.

## Examples

The `examples/` folder holds five fictional postings, two clean, one ghost, one scam, one vague. Run Mirage on each and compare the reports.

## A note of honesty

Mirage is a screening aid, not a ruling on any employer. Scammers adapt, and legit postings can trip a signal or two. Always verify through official channels before you share personal data or send money.
