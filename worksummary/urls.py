import re

_URL_RE = re.compile(r"https?://\S+")
_TRAILING_PUNCT = ".,;:!?)]}\"'"


def _strip_trailing_punct(url: str) -> str:
    while url and url[-1] in _TRAILING_PUNCT:
        url = url[:-1]
    return url


def extract_urls(text: str) -> list[str]:
    """Return all URLs found in `text`, with trailing punctuation stripped."""
    return [_strip_trailing_punct(m.group(0)) for m in _URL_RE.finditer(text)]


def rewrite_with_footnotes(text: str, start_n: int) -> tuple[str, list[str], int]:
    """Replace URLs in `text` with sequential `[N]` references.

    Returns the rewritten text, the extracted URLs in order, and the next
    available footnote number. Adjacent URLs collapse to `[N][N+1]` without
    extra whitespace between them.
    """
    extracted: list[str] = []
    next_n = start_n
    pieces: list[str] = []
    cursor = 0

    for match in _URL_RE.finditer(text):
        raw = match.group(0)
        clean = _strip_trailing_punct(raw)
        stripped_tail = raw[len(clean) :]

        pieces.append(text[cursor : match.start()])
        pieces.append(f"[{next_n}]")
        pieces.append(stripped_tail)
        extracted.append(clean)
        next_n += 1
        cursor = match.end()

    pieces.append(text[cursor:])
    rewritten = "".join(pieces)

    rewritten = re.sub(r"[ \t]+", " ", rewritten)
    rewritten = re.sub(r"\] +\[", "][", rewritten)
    rewritten = re.sub(r" ([.,;:!?])", r"\1", rewritten)

    return rewritten, extracted, next_n
