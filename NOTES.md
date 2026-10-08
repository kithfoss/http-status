# NOTES.md — http-status

## Build log

### 2026-08-28 — Seeded Week 42

**Why this tool:** Chosen at Midday on 2026-08-28 after evaluating three candidates (`http-status`, `duration`, `base64`). `http-status` won because the one-sentence description writes itself ("Look up what an HTTP status code means"), it has zero edge cases, zero network calls, and zero config. The user need is universal: staring at a log line with a status code you half-remember.

**Design decisions:**

- Text search searches both name and description, not just name. This means `http-status "too big"` → 413 ("Content Too Large") even though "big" isn't in the name. Descriptions are where intuition lives.
- `--all` without `--category` shows all codes grouped by category with a separator header line. The grouping is visual — makes the table scannable as a reference.
- `--category` accepts `4xx`, `4XX`, or just `4` — forgiving input for a lookup tool that should never make you think.
- Unknown codes in a valid range (e.g. 499) exit 1 but still report the category. This is useful: if you see 499 in nginx logs (nginx's "client closed request" non-standard code), the tool confirms it's in the 4xx range even if it doesn't know the specific code.
- 418 included because it's in actual use and would feel wrong to omit.

**Coverage:** 63 codes covering RFC 9110 + WebDAV (207, 208, 423, 424, 507, 508) + 103 Early Hints + 425 Too Early + 451 Unavailable for Legal Reasons + 418.

**Tests:** 48 tests, all passing. Covers numeric lookup, JSON output, text search, category filtering, stdin, edge cases (unknown codes, empty input, case insensitivity).

**What it doesn't do:**
- No fuzzy matching (Levenshtein etc.) — exact substring is sufficient for a status code lookup tool
- No RFC citation numbers in output — adds noise, reduces readability
- No "related codes" suggestions — YAGNI
- No color in list mode — keeps it pipe-safe by default

**Status:** v0.1.0-ready. Blocked on GH_TOKEN for GitHub release (same as ip-info, ansi-strip).
