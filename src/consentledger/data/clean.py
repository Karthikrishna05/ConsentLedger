"""Convert scraped AA docs (data/aa/raw/{html,pdf}) into clean plain text (data/aa/raw/text).

HTML drops scripts/nav/footers/cookie banners; PDF uses pdfplumber. Unicode is normalised before annotation,
since offsets index this text. Docs under --min-chars (JS shells, failed scrapes) are reported and skipped.

Usage:
    python -m consentledger.data.clean                 # process everything in raw/
    python -m consentledger.data.clean --min-chars 800
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW = PROJECT_ROOT / "data" / "aa" / "raw"
OUT = RAW / "text"

_DROP_TAGS = ["script", "style", "noscript", "svg", "nav", "footer", "header", "form", "button", "iframe"]
_DROP_HINTS = re.compile(r"(cookie|consent-banner|nav|navbar|menu|footer|header|sidebar|breadcrumb|"
                         r"social|share|subscribe|newsletter|modal|popup)", re.I)

# --- Unicode normalization table ---
_SPACE_CPS = [0x00A0, 0x2004, 0x2005, 0x2006, 0x2007, 0x2008, 0x2009, 0x200A,
              0x202F, 0x205F, 0x3000, 0x2028, 0x2029]                 # unicode spaces -> " "
_REMOVE_CPS = [0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF, 0x00AD,        # zero-width / soft hyphen
               0x2022, 0x25CF, 0x00B7, 0x2193, 0x26D4, 0x26A0, 0x2139]  # bullets / UI icons
_TRANS: dict[int, str | None] = {cp: " " for cp in _SPACE_CPS}
_TRANS.update({cp: None for cp in _REMOVE_CPS})
_TRANS.update({0x201C: '"', 0x201D: '"', 0x201E: '"', 0x201F: '"',    # curly double -> "
               0x2018: "'", 0x2019: "'", 0x201A: "'", 0x201B: "'"})   # curly single -> '


def clean_html(raw: bytes) -> str:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(raw, "lxml")
    for tag in soup(_DROP_TAGS):
        tag.decompose()
    for el in soup.find_all(attrs={"class": _DROP_HINTS}):
        el.decompose()
    for el in soup.find_all(attrs={"id": _DROP_HINTS}):
        el.decompose()
    root = soup.find("main") or soup.find("article") or soup.body or soup
    return _normalize(root.get_text(separator="\n"))


def clean_pdf(path: Path) -> str:
    import pdfplumber
    parts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            if t:
                parts.append(t)
    return _normalize("\n".join(parts))


def _normalize(text: str) -> str:
    text = text.translate(_TRANS)                       # unicode normalization first
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]
    out = "\n".join(lines)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip()


def main() -> None:
    ap = argparse.ArgumentParser(description="Clean scraped AA docs to plain text.")
    ap.add_argument("--min-chars", type=int, default=800, help="below this = flagged as thin/shell, skipped")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    jobs = [(p, "html") for p in sorted((RAW / "html").glob("*.html"))] + \
           [(p, "pdf") for p in sorted((RAW / "pdf").glob("*.pdf"))]
    if not jobs:
        raise SystemExit(f"No raw files under {RAW}. Run consentledger.data.scrape_aa first.")

    usable, thin, errors = [], [], []
    for path, fmt in jobs:
        doc_id = path.stem
        try:
            text = clean_html(path.read_bytes()) if fmt == "html" else clean_pdf(path)
        except Exception as e:
            errors.append((doc_id, f"{type(e).__name__}: {e}"))
            print(f"ERROR  {doc_id}: {type(e).__name__}")
            continue
        n = len(text)
        if n < args.min_chars:
            thin.append((doc_id, n))
            print(f"THIN   {doc_id}  {n} chars  (skipped - likely JS shell / failed scrape)")
            continue
        (OUT / f"{doc_id}.txt").write_text(text, encoding="utf-8")
        usable.append((doc_id, n, len(text.split())))
        print(f"OK     {doc_id}  {n} chars / {len(text.split())} words")

    print(f"\n=== clean summary ===  usable {len(usable)} | thin {len(thin)} | errors {len(errors)}")
    print(f"annotation-ready text in: {OUT.relative_to(PROJECT_ROOT)}")
    if thin:
        print("thin (dropped): " + ", ".join(f"{d}({n})" for d, n in thin))
    if errors:
        print("errors: " + ", ".join(d for d, _ in errors))
    if usable:
        words = sorted(w for _, _, w in usable)
        print(f"usable word counts: min {words[0]}, median {words[len(words)//2]}, max {words[-1]}")


if __name__ == "__main__":
    main()
