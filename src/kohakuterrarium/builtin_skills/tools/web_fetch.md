---
name: web_fetch
description: Read a web page and return its content in clean markdown format
category: builtin
tags: [web, network, fetch]
---

# web_fetch

Fetch a web page and return its content in clean, readable markdown format.

## Arguments

| Arg | Type | Description |
|-----|------|-------------|
| url | string | URL to fetch (required) |

## Available Backends (in priority order)

The tool automatically tries backends in order, using the best available:

1. **crawl4ai** (optional: `pip install crawl4ai`) -- JS rendering, anti-bot
   handling, best quality. Uses headless browser.
2. **trafilatura** (optional: `pip install trafilatura`) -- Good content
   extraction from HTML, no JS rendering.
3. **Jina Reader** (built-in) -- Uses the r.jina.ai API for server-side JS
   rendering. Zero local deps but may be rate-limited.
4. **httpx + html2text** (built-in) -- Always works, lowest quality. Basic
   HTML-to-markdown conversion.

## Behavior

- URLs without a scheme are auto-prefixed with `https://`.
- Output is truncated to 100,000 characters if the page is very large.
- Timeout is 30 seconds per backend attempt.
- If one backend fails, the next is tried automatically.

## WHEN TO USE

- Reading documentation pages
- Fetching API docs or tutorials
- Checking web page content
- Extracting text from web articles

## Output

Returns the page content as clean markdown text.

## LIMITATIONS

- Content cap: 100,000 characters (truncated with notice if exceeded)
- 30-second timeout per backend
- JS-heavy pages may not render well without crawl4ai installed
- Some sites may block automated access

## TIPS

- Install `crawl4ai` for best results with JS-heavy sites.
- Install `trafilatura` for good extraction without a browser dependency.
- Use `web_search` first to find URLs, then `web_fetch` to read them.
