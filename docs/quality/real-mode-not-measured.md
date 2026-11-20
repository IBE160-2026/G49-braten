# Real mode: what is verified and what is not measured

Status: **Real-mode measurements not run.** The project has no paid Anthropic Key (Author's decision 2026-11-20: no money is spent on the API). Real mode is verified by automated tests against a faked API; the measurements below that need real model replies are not done.

## Why

The model (Claude Haiku 5.5) has no free tier, so every Real-mode call needs prepaid credit. The Author chose not to buy credit. The app is built for this: without a Key it runs in Mock mode with recorded replies for the Sample document, which is the path the Examiner uses (README, NFR-2, UJ-5).

## Verified without a Key

These run in `uv run pytest`, with no Key and sockets blocked. The real `anthropic` SDK runs against an `httpx2.MockTransport`, so the request the app sends and every reply type are checked, but no model is called.

| Area | Evidence |
|---|---|
| Request shape: model, structured-output schema, effort, timeouts, no sampling parameters (FR-21, AD-2) | `tests/test_anthropic_adapter.py` (`test_fr21_generate_request_shape`, `test_nfr3_timeouts_and_retries_per_operation`) |
| Every stop reason and provider error maps to its message; the app keeps running (AD-2) | `tests/test_anthropic_adapter.py` (`test_ad2_…`, `test_fr21_provider_errors_are_mapped`) |
| No retry can be billed twice: timeouts and rejected Keys are never retried | `tests/test_anthropic_adapter.py` (`test_fr21_a_timeout_is_never_retried_so_it_cannot_be_billed_twice`, `test_fr21_a_rejected_key_is_not_retried`) |
| The Key never appears in logs, pages or errors; SDK logs held at WARNING (NFR-4) | `tests/test_anthropic_adapter.py` (`test_nfr4_…`) |
| Nothing leaves before the privacy notice is accepted, and the daily limit is not counted (FR-22, AD-17) | `tests/test_privacy_notice.py`, `tests/test_ai_gateway.py` (`test_ad17_every_gateway_operation_that_takes_a_student_checks_privacy`) |
| Daily limit of 20 generations (NFR-7) | `tests/test_ai_gateway.py`, `tests/test_generation.py` |
| Reference check on generated items (FR-8) | `tests/test_generation.py` and the Mock path with its planted wrong Reference |

## Not measured

| Item | What it needs | Tool, when a Key is available |
|---|---|---|
| **OQ-2** generation time for a 20- and a 50-page PDF; NFR-3 Real «Study material for a 20-page PDF within 2 minutes» | Real replies | `uv run python scripts/measure_generation.py 20-sider.pdf 50-sider.pdf --report` |
| **NFR-3** Real «Free-text grading within 15 seconds» | Real replies | A Quiz in the app with a Key set; the adapter enforces a 12 s timeout either way |
| **NFR-5 content check**: ≥ 12 of 15 Questions correct and answerable from the Source; ≥ 8 of 10 Free-text Grades matching the Author's | Real replies on one fixed 10–20 page set of the Author's notes | Upload in the app with a Key set; judge by hand and write it down here |
| **SM-3** ≥ 90 % of Generated items pass FR-8 on the Author's material | Real replies | `scripts/measure_generation.py` reports the items kept and removed by FR-8 per run |

The prompts (`ai/prompts.py`) have therefore never been tuned against real replies. The FR-7 and FR-8 checks still run on every reply, so a weak reply fails safely (items dropped or the Source marked failed with «Prøv igjen»), but the quality of the Study material in Real mode is unknown.

## To measure later

1. Create a Key with a monthly spending limit (README, «Ekte modus»); measuring all of the above costs well under 1 USD.
2. Put it in `.env` and restart `runserver`.
3. Run the commands in the table above and update this note.
