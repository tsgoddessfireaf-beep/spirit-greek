# 2026-10-12 — Intuitive Shuffle — Claude reading server live, "Get my reading" works on phone

QED close entry (Protocol v2.0 shape), kept in the repository at Dolores's request. It has **not** been written to Notion.

## Row fields

| Field | Value |
|---|---|
| Session Title | ⬜ 2026-10-12 — 🆕 POSSIBLE NEW PROJECT: Intuitive Shuffle — Claude reading server deployed, page button live \| https://claude.ai/code/session_0125hLpjk9DXG8zvCYgDAUC6 |
| Date | 2026-10-12 |
| Project | System/Admin (same relation as the 10-03 and 10-08 entries). No project page created. |
| Interface | Code |
| Device | Android (phone test). Cloud Shell steps run from a desktop browser. |
| Open Items | Yes |
| Files Created | Yes |
| File Location | GitHub |

## Done

- Reading server (`functions/`: `reading`, `deleteReading`) merged (PR 17) and deployed from Cloud Shell. First live test reading returned `mode: "ai"`.
- "Get my reading" button, opt-in question saving (default off) with a delete button, and corrected privacy wording merged (PR 18). Dolores confirmed it works on her phone.
- Found why GitHub Pages updates had failed since PR 15: Jekyll crashed on `{{` in the saved Waite source text. Added `.nojekyll` (PR 19); the button then appeared.
- One live reading failed with "reading failed" and no cause, because the logger overwrote the error text. Fixed the logging (PR 20). Which of two changes then fixed it (a database permission command, or the redeploy) is **not confirmed**, and so is whether the permission command was run. AI model: not recorded in this file (repository rule); the Notion entry will carry it.

## Decisions Made

- Draft Waite quotes may be used (each flagged approved or draft). A question is saved only on a ticked box that starts unticked. Claude workspace limit $10 a month.
- Deploy from Cloud Shell, not GitHub. The GitHub deploy file inside PR 18 is unused.

## Still Open

- The two server addresses are public: no App Check and no per-visitor limit.
- Not built: Yes / No reading, approval page for Waite quotes, Claude citations. Also open: a test question may still be saved; leftover Google build files (small monthly cost); check Claude workspace usage in a week.
- Server gotchas met (build permission, empty function shells, Pages) are in `docs/HANDOFF.md`.

## Files

- `spirit-greek` on GitHub: `functions/`, `index.html`, `.nojekyll`, `firebase.json`, `.firebaserc`, `firestore.rules`, `docs/HANDOFF.md`. PRs 17, 18, 19 and 20 merged; this entry is PR 21.

Quod Erat Demonstrandum - "that which was to be demonstrated" to use the vernacular of our times... BOOYA!
