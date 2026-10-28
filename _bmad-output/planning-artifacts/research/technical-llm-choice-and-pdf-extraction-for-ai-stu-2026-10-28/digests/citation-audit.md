# Citation audit of research.md against digests

Scope: every sentence/table row with a [n] marker, plus unmarked specific facts. Digest numbers (prices, versions, licences, limits, page counts) otherwise match.

## Mismatches

| # | Sentence (quote) | Marker | What the digests say | Severity |
|---|---|---|---|---|
| 1 | "koster under ca. 2 øre (under 0,02 USD) på alle de billige betalte modellene" (Sammendrag, funn 1); also A1 "under 2 øre per PDF" | [9][10][13][14] | Digest A1-A2-r1: "under ~2 cents per PDF" (USD). 0,02 USD is about 20 øre at ~10 NOK/USD, not 2 øre. Cost table itself (0,003-0,09 USD) is correct. Unit/currency error | wrong |
| 2 | "under 1 øre per PDF [9][10]" (Anbefaling 2, Haiku/Flash-Lite) | [9][10] | Digest: Haiku ~0,0043 USD (~0,005 with tokenizer), Flash-Lite ~0,0038 USD. That is under 1 US cent only if read as cents, about 4-5 øre, not under 1 øre | wrong |
| 3 | "Bare Gemini har et bekreftet gratisnivå med eget API [10]" | [10] | Digest A1-A2-r1 says Gemini (free tier Yes) AND OpenRouter :free (limits confirmed) have evidenced free access. The report does cover OpenRouter in A2, but "bare Gemini" contradicts it (OpenRouter is a router, and its free list showed no known chat models, so the wording is defensible) | overstated (minor) |
| 4 | "Det som begrenser en sidegrense er tokens per minutt på gratisnivåer [11][15]" | [11] | [11] gives no TPM numbers at all (digest: numeric limits not on page). Only [15] (Groq Developer plan, 8K TPM, low confidence) supports a figure | overstated (minor) |
| 5 | "avvises (400) fordi sitater må flettes inn i teksten [2]" | [2] | Digest supports the 400 and mutual exclusivity but gives no reason; "må flettes inn i teksten" is not in the digest | unsupported (reason clause) |
| 6 | pypdf and pdfplumber rows: "Sidevis tekst: Ja" | [28][29][30] | Digests give version/licence/benchmark only. No claim that either offers per-page extraction (pypdf no tables; pdfplumber 0 on reading order). The "Ja" is unsourced, although generally true | unsupported |
| 7 | "Det er også billigere enn å sende PDF-en direkte [1]" | [1] | Digest gives 1,5-3k text tokens/page plus image tokens for native PDF; the 18k vs 30-60k comparison is the author's own arithmetic from an assumed 18k tokens (flagged as unsourced elsewhere). Direction is supported, not sourced as a measured comparison | overstated (minor) |

## Notes (not counted as mismatches)
- Cost table and the 18k/5k assumption are marked as the author's own arithmetic; all arithmetic checked and correct.
- Unmarked facts (Mistral 404, no Norwegian benchmark found, Gemini 3 PDF text not billed marked uncertain) match digests.
- Source URL differences (NorEval arxiv 2503.03592 vs 2504.07749; models overview path) are cosmetic.
- Frontmatter `claims_verified/unverified/disputed` counts were not checked against digests.

## Checked and found fine
Roughly 75 marked sentences/rows (all price, version, licence, limit, page-count, structured-output, Ollama, Groq, OpenRouter, NotebookLM, secret-scanning rows) matched their digest claims. Unmarked specific facts: none without digest support.
