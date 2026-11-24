# Changelog

## 1.0.0 — 2026-11-25

Daily portfolio challenge #11.

- Pure core with a JavaScript port checked by shared vectors: passages from any shape of text (blank lines, single
  line breaks, a PDF's wrapped and hyphenated lines; Uzbek Cyrillic read in Latin), definitions, key terms, number
  questions, the rule-based question generator (fewer questions rather than bad ones), the deterministic checks for
  AI-drafted questions (a quote that occurs in the source, one grounded correct answer), the seeded shuffle, the
  analysis in integer math (corrected item-total discrimination, distractor shares, flags with advice, topics, the
  retest plan and the progress after it), the Excel-friendly CSV and the invented class 7-B.
- Service on SQLite (WAL, `BEGIN IMMEDIATE`): roles that never mix, classes with signed expiring invites and test
  codes, sources and drafts with the teacher's review, settings checked on the server, publishing, solving with the
  deadline kept on the server and answers saved as they go, a submit that counts once, automatic submit at time-out,
  results, the analysis, the retest only to those who missed, reminders and the teacher's summary exactly once.
- Files and AI: PDF / .docx / .txt by their first bytes with limits; Gemini with a JSON schema, the source as
  delimited data, no tools, a daily quota; a mocked model that obeys instructions hidden in a PDF changes nothing.
- aiogram bot (uz/ru) and the Mini App for both roles (aiohttp, initData, per-user rate limits, CSP); the browser demo
  with two phones, a ten-step story and the "O'zingiz sinab ko'ring" box; pytest, node tests and Playwright e2e;
  Docker (non-root, read-only), CI and GitHub Pages.
