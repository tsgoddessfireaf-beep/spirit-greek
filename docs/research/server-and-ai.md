# Server and AI options for the reading back end

**Research date:** 2026-10-12. A research agent compiled this for Dolores Puckett's decision. Nothing here is built yet.

- Prices and limits come from official pages fetched that day. Each claim has its URL next to it, and anything not confirmed is marked UNVERIFIED.
- The Claude prices below were re-checked against https://platform.claude.com/docs/en/about-claude/pricing on 2026-10-12, and they match.

## Recommendation

| Part | Choice | Reason |
|---|---|---|
| Host and database | **Firebase** in a **new project**, separate from Aevum: Cloud Functions (2nd gen) for the server, Firestore for the database | Familiar from Aevum. A separate project keeps this app's bill, spending cap and data apart. |
| AI model | **Claude Sonnet 5.5**. Test Claude Haiku 5.5 on about 20 sample readings, since it costs about 20× less | Claude's citations feature, and a hard spending stop on the Anthropic side |
| Grounding | Look up the dealt cards' verified entries directly, pass them to Claude with citations turned on, then run automatic checks | There are only 78 cards, so a direct lookup is exact and cheap. No search engine is needed. |
| "Training", phase 1 | A written style guide, 3–6 of Dolores's sample readings for each spread, and a feedback loop | Claude fine-tuning is not realistically available today (see below). Edits take effect on the next reading. |
| "Training", later | Once 100–200 readings are approved, test a fine-tuned Gemini model. Keep it only if it wins a blind comparison judged by Dolores. | Gemini is the only realistic fine-tuning route today |

### Terms used in this document

- **Token** = a word fragment. AI services charge per million tokens ("MTok").
- **Fine-tuning** = retraining a model's weights on example readings.
- **Few-shot examples** = sample readings sent with every request to show the style.
- **Spend cap** = a limit that stops the service. An **alert** only sends an email.

## Monthly cost

These figures assume about 3,000 input tokens and 800 output tokens per reading.

| Readings per month | Hosting | Sonnet 5.5 (no examples → 3K tokens of examples) | Haiku 5.5 |
|---|---|---|---|
| 100 | about $0 | $1.40–$2 | about $0.07 |
| 1,000 | about $0 | $14–$20 | about $0.70 |
| 10,000 | about $0 (check the free quotas) | $140–$200 | about $7 |

Prices per MTok, input / output:

| Model | Input | Output |
|---|---|---|
| Haiku 5.5 | $0.10 | $0.50 |
| Sonnet 5.5 | $2 | $10 |
| Opus 5.5 | $4 | $20 |
| Gemini 3.1 Flash-Lite | $0.25 | $1.50 |
| Gemini 3.6 Flash, until 2026-12-31 | $0.75 | $3.75 |
| Gemini 3.6 Flash, from 2027-01-01 | $1.50 | $7.50 |

Gemini prices: https://cloud.google.com/vertex-ai/generative-ai/pricing

**Hidden cost:** Sonnet 5.5 and Haiku 5.5 "think" by default, and that thinking is billed as output. Set a low effort level and watch real usage.

## Hosts compared

| | Firebase | Cloudflare Workers + D1 | Supabase | Vercel / Netlify |
|---|---|---|---|---|
| Free tier | Functions: 2M calls, 400K GB-s per month, on the paid Blaze plan. Firestore: 50K reads per day. ([pricing](https://firebase.google.com/pricing)) | 100K requests per day, 10 ms of computing time per call ([pricing](https://developers.cloudflare.com/workers/platform/pricing/)) | Free projects pause after 1 week with no use ([pricing](https://supabase.com/pricing)) | Vercel Hobby is non-commercial only ([plans](https://vercel.com/docs/plans/hobby)) |
| Lowest paid plan | $0 beyond the free quotas | $5/month | $25/month | $20/month (Vercel Pro) |
| Ease for Dolores | Best: she already uses it | New account and a command-line tool | New platform | Needs a separate database |

## Training, honestly

| Approach | Cost | Improves | Correcting a mistake |
|---|---|---|---|
| Her verified passages plus her sample readings sent with each request | About $0.006 more per reading | Immediately | Edit one entry and it applies to the next reading |
| Feedback loop: she approves, edits or rejects readings, and her edited versions become the examples | Her time | Gradually | Easy |
| Fine-tuning | Gemini only: about $7–$38 per training run, and each reading then costs 1.5× more | Slowly, after 100+ clean readings | Needs retraining |

### Fine-tuning availability

- **Claude:** only Claude 3 Haiku appears in Amazon Bedrock's fine-tuning table, and that model is retired on the Claude API.
  - Sources: https://docs.aws.amazon.com/bedrock/latest/userguide/custom-model-fine-tuning.html and https://platform.claude.com/docs/en/about-claude/model-deprecations
- **OpenAI:** fine-tuning is closed to new users.
  - Source: https://developers.openai.com/api/docs/guides/model-optimization
- **Gemini:** supervised tuning is available.
  - About 100 examples is a suggested start (UNVERIFIED).
  - Source: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini-supervised-tuning-prepare

### Lock-in

A fine-tuned model stops working when its base model is retired. Anthropic's guaranteed dates:

- Sonnet 5.5: not retired before 2027-09-28.
- Haiku 5.5: not retired before 2027-10-07.

Fine-tuning teaches style, not facts.

## Accuracy, privacy and abuse controls

### Private knowledge base

- Firestore rules deny all access from the phone. Only the server function reads the database, and none of it goes in the public repository.
- Each card entry holds:
  - its upright and reversed meanings;
  - its source: book, edition, page and URL;
  - a status, draft or verified;
  - an empty slot for Dolores's own wording.

### Grounding

- The server uses verified entries only. If a dealt card has no verified entry, it refuses to write prose.
- Citations are turned on: https://platform.claude.com/docs/en/build-with-claude/citations
- Automatic checks run before anything is shown:
  - quotes match the source word for word;
  - every dealt card is mentioned, and no other card is;
  - each card's orientation (upright or reversed) is right.
- If a check fails, the server retries once. If it fails again, the app shows the verbatim passages without prose.
- A set of about 30 test spreads is re-run after any change to the prompt or model.

### Privacy

- Readers' questions are not stored or logged. The server logs only the spread, the card numbers, token counts and cost.
- The Claude API does not use conversation data for training without permission. Fable and Mythos models require 30-day retention; Sonnet and Haiku do not.
  - Source: https://platform.claude.com/docs/en/manage-claude/api-and-data-retention
- **UNVERIFIED:** how long Anthropic keeps safety logs. Confirm this before promising readers anything.
- The README's "nothing leaves the phone" line must change.

### Bills and abuse

- A hard monthly limit on a dedicated Claude Console workspace ([workspaces](https://platform.claude.com/docs/en/manage-claude/workspaces)).
- The Firebase spend cap for Cloud Functions ([billing](https://firebase.google.com/docs/projects/billing/avoid-surprise-bills)).
- App Check, which confirms that calls come from the real page.
- Limits on each call:
  - only valid card numbers are accepted;
  - questions are capped at about 300 characters;
  - output is capped at about 1,200 tokens.
- Hourly limits per device and per network address, and a daily total cap.
- A `readings_enabled` off switch that Dolores can flip from her phone.
- The AI key is stored in Google Secret Manager, never in the page or the repository.

## Open questions for Dolores

1. Will readings be sold through this app, now or later?
2. A new Firebase project (recommended), or share Aevum's?
3. What monthly dollar limit for AI spending, and what daily reading limit per visitor?
4. Store readers' questions at all? The default is no. Should readers see the citations?
5. Run an A/B comparison of Haiku and Sonnet on about 20 sample readings, judged by Dolores?
6. How should entries be approved: a small private phone page, or a spreadsheet?
7. Account steps only Dolores can take: creating the Anthropic account, setting spending limits, creating the Firebase project, and issuing keys.
