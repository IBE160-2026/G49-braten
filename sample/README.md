# Sample document: «Databaser: normalisering»

`normalisering.pdf` is the Sample document Mock mode generates Study material for (FR-20). It is a
20-slide lecture deck in Norwegian bokmål about database normalisation, one slide per PDF page,
written for AI Study Buddy.

| File | What it is |
| --- | --- |
| `source.md` | The slide text. `# Title` starts a slide; `- ` lines become bullets. |
| `build_sample.py` | Renders `source.md` to `normalisering.pdf` (Helvetica, WinAnsi, so æøå survive). |
| `normalisering.pdf` | The committed Sample document. |

Rebuild after editing the text:

```sh
uv run python sample/build_sample.py
uv run pytest tests/test_mock_recordings.py
```

The Mock recordings in `ai/mock/` quote the extracted page text verbatim, so a text change can break
them; the test names the quote that no longer matches. The Sample's SHA-256 is computed from the PDF
at import (`ai.mock.SAMPLE_SHA256`), so it needs no update.

## Licence

The slide text, `source.md` and `normalisering.pdf` are released by the Author under
[CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/) (public domain dedication).
You may copy, modify and distribute them, even commercially, without asking permission.
