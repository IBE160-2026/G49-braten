"""OQ-2: measure Real-mode generation time against the Anthropic API (Author's tool, not app code).

Sends exactly the request the app sends for «Lag studiemateriell» (same model, system prompt,
user prompt with Location markers, structured-output schema and effort, from `ai.anthropic_adapter`
and `ai.prompts`), times it, and runs the app's FR-7 and Reference checks on the reply. Nothing is
stored and the daily limit is not touched.

Unlike the app, each call runs with **no retry** and a long timeout, so the time shown is one real
call. The app's limits are compared afterwards: the generation timeout (`GENERATE_TIMEOUT`, 110 s)
and the AD-16 request floor (150 s).

Every call costs money on your Key. Usage:

    uv run python scripts/measure_generation.py path/to/20-sider.pdf path/to/50-sider.pdf
    uv run python scripts/measure_generation.py deck.pdf --runs 2 --detail detailed --report

Options:
    --detail short|medium|detailed   the Detail level (default medium)
    --effort low|medium|high          override the adapter's generation effort, to compare
    --runs N                          calls per file (default 1); the first call of the whole
                                      run pays the one-time schema compilation ("cold")
    --report                          append the results to docs/quality/oq2-generation-time.md
    --yes                             do not ask before spending money

The Key is read from `.env` like the app does and is never printed.
"""

import argparse
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "docs" / "quality" / "oq2-generation-time.md"
MEASURE_TIMEOUT = 600.0
AD16_FLOOR = 150.0
RATE_LIMIT_HEADERS = (
    "anthropic-ratelimit-requests-limit",
    "anthropic-ratelimit-input-tokens-limit",
    "anthropic-ratelimit-output-tokens-limit",
    "anthropic-ratelimit-input-tokens-remaining",
    "anthropic-ratelimit-output-tokens-remaining",
)


def setup_django() -> None:
    sys.path.insert(0, str(ROOT))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django

    django.setup()


@dataclass
class Result:
    file: str
    run: int
    pages: int
    chars: int
    seconds: float
    outcome: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    counts: dict = field(default_factory=dict)
    rate_limits: dict = field(default_factory=dict)


def load_locations(path: Path):
    """The file's non-empty Locations, as the app builds them (pages for PDF, paragraphs for text)."""
    from ai.schemas import Location
    from ingestion import extract

    data = path.read_bytes()
    if extract.extension(path.name) == extract.PDF_EXTENSION:
        texts = extract.pdf_pages(data)
    else:
        texts = extract.paragraphs(extract.decode_text(data))
    extract.check_char_limit(texts)
    locations = [Location(index=i, text=text) for i, text in enumerate(texts, start=1) if text.strip()]
    return len(texts), locations


def measure(path: Path, run: int, detail: str, effort: str) -> Result:
    from ai import anthropic_adapter as adapter
    from ai import prompts
    from ai.errors import AIError
    from ai.schemas import GenerateRequest, StudyMaterial
    from studymat import checks

    pages, locations = load_locations(path)
    request = GenerateRequest(source_id=0, content_sha256="", detail_level=detail, locations=locations)
    chars = sum(len(loc.text) for loc in locations)
    client = adapter._client().with_options(timeout=MEASURE_TIMEOUT, max_retries=0)
    started = time.perf_counter()
    try:
        raw = client.messages.with_raw_response.create(
            model=adapter.MODEL,
            max_tokens=adapter.MAX_OUTPUT_TOKENS,
            system=prompts.GENERATE_SYSTEM,
            messages=[{"role": "user", "content": prompts.generate_user(request)}],
            output_config={"format": adapter.output_format(StudyMaterial), "effort": effort},
        )
        message = raw.parse()
    except adapter.anthropic.AnthropicError as error:
        seconds = time.perf_counter() - started
        code = adapter._mapped(error).code if isinstance(error, adapter.anthropic.APIError) else "provider_unavailable"
        return Result(path.name, run, pages, chars, seconds, f"{code} ({type(error).__name__})")
    seconds = time.perf_counter() - started
    result = Result(
        path.name,
        run,
        pages,
        chars,
        seconds,
        outcome="ok",
        input_tokens=message.usage.input_tokens,
        output_tokens=message.usage.output_tokens,
        rate_limits={name: raw.headers.get(name) for name in RATE_LIMIT_HEADERS if raw.headers.get(name)},
    )
    try:
        material = adapter._read(message, StudyMaterial)
    except AIError as error:
        result.outcome = f"{error.code} (stop_reason={message.stop_reason})"
        return result
    checked = checks.check(material, {loc.index: loc.text for loc in locations})
    result.counts = {
        "key_concepts": len(checked.key_concepts),
        "flashcards": len(checked.flashcards),
        "mc": sum(q.kind == "multiple_choice" for q in checked.questions),
        "free_text": sum(q.kind == "free_text" for q in checked.questions),
        "dropped": checked.dropped,
        "removed": checked.removed,
    }
    return result


def verdict(seconds: float, timeout: float) -> str:
    if seconds >= AD16_FLOOR:
        return "over 150 s floor"
    if seconds >= timeout:
        return f"over {timeout:.0f} s timeout"
    if seconds >= 0.8 * timeout:
        return "near timeout"
    return "ok"


def table(results: list[Result], timeout: float) -> str:
    lines = [
        "| File | Run | Pages | Chars | In tok | Out tok | Seconds | Time check | Outcome | KC | FC | MC | FT | Dropped | Removed |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        c = r.counts
        lines.append(
            f"| {r.file} | {r.run}{' (cold)' if r.run == 1 and r is results[0] else ''} | {r.pages} | {r.chars} "
            f"| {r.input_tokens or '–'} | {r.output_tokens or '–'} | {r.seconds:.1f} | {verdict(r.seconds, timeout)} "
            f"| {r.outcome} | {c.get('key_concepts', '–')} | {c.get('flashcards', '–')} | {c.get('mc', '–')} "
            f"| {c.get('free_text', '–')} | {c.get('dropped', '–')} | {c.get('removed', '–')} |"
        )
    return "\n".join(lines)


def rate_limit_lines(results: list[Result]) -> str:
    seen = next((r.rate_limits for r in results if r.rate_limits), {})
    if not seen:
        return "Rate-limit headers: none returned."
    return "Rate-limit headers (from the first successful call):\n" + "\n".join(
        f"- `{name}`: {value}" for name, value in seen.items()
    )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="OQ-2: time Real-mode generation (costs money).")
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--detail", choices=["short", "medium", "detailed"], default="medium")
    parser.add_argument("--effort", choices=["low", "medium", "high"])
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--yes", action="store_true")
    args = parser.parse_args(argv)

    setup_django()
    from django.conf import settings

    from ai import anthropic_adapter as adapter

    if not settings.ANTHROPIC_API_KEY:
        print("No ANTHROPIC_API_KEY in .env: nothing to measure (the app would run in Mock mode).")
        return 2
    missing = [str(f) for f in args.files if not f.is_file()]
    if missing:
        print("Not found: " + ", ".join(missing))
        return 2
    effort = args.effort or adapter.EFFORT_GENERATE
    calls = len(args.files) * args.runs
    print(f"{calls} call(s) to {adapter.MODEL}, Detail level {args.detail}, effort {effort}. This costs money on your Key.")
    if not args.yes and input("Continue? [y/N] ").strip().lower() not in ("y", "j", "ja", "yes"):
        print("Nothing sent.")
        return 1

    results = []
    for path in args.files:
        for run in range(1, args.runs + 1):
            print(f"… {path.name}, run {run}", flush=True)
            results.append(measure(path, run, args.detail, effort))

    timeout = adapter.GENERATE_TIMEOUT
    output = (
        f"### {date.today().isoformat()} · {adapter.MODEL} · effort {effort} · Detail level {args.detail}\n\n"
        f"{table(results, timeout)}\n\n{rate_limit_lines(results)}\n\n"
        f"App limits: generation timeout {timeout:.0f} s with {adapter.GENERATE_RETRIES} retry; AD-16 floor {AD16_FLOOR:.0f} s. "
        "KC/FC/MC/FT are what survives the FR-7 and Reference checks (FR-7 wants ≥ 5 KC, ≥ 10 FC, ≥ 10 Questions of both kinds).\n"
    )
    print()
    print(output)
    if args.report:
        new = not REPORT.exists()
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        with REPORT.open("a", encoding="utf-8") as handle:
            if new:
                handle.write(
                    "# OQ-2: Real-mode generation time\n\n"
                    "Measured with `scripts/measure_generation.py` (one call per row, no retry). "
                    "If generation nears 150 s or hits the rate limit, lower the FR-3 limits or pull FR-26 forward (architecture OQ-2).\n\n"
                    "## Measurements\n\n"
                )
            handle.write(output + "\n")
        print(f"Appended to {REPORT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
