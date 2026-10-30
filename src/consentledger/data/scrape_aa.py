"""Download the AA corpus in data/aa/manifest.csv into data/aa/raw/ (scrape once, then work from the cache).

Live company pages: one polite GET each (delay + timeout), raw bytes saved verbatim. Status, bytes, sha256 and
date go to data/aa/raw/scrape_log.csv so a re-scrape returning a different hash is noticeable.

Usage:
    python -m consentledger.data.scrape_aa            # skip docs already downloaded
    python -m consentledger.data.scrape_aa --force    # re-download everything
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import time
from datetime import date
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MANIFEST = PROJECT_ROOT / "data" / "aa" / "manifest.csv"
RAW = PROJECT_ROOT / "data" / "aa" / "raw"
LOG = RAW / "scrape_log.csv"
UA = "Mozilla/5.0 (ConsentLedger research crawler; academic use; contact: project team)"


def out_path(doc_id: str, fmt: str) -> Path:
    return RAW / ("pdf" if fmt == "pdf" else "html") / f"{doc_id}.{ 'pdf' if fmt=='pdf' else 'html'}"


def main() -> None:
    ap = argparse.ArgumentParser(description="Scrape AA corpus from the manifest.")
    ap.add_argument("--force", action="store_true", help="re-download even if the file already exists")
    ap.add_argument("--delay", type=float, default=1.5, help="seconds between requests (politeness)")
    ap.add_argument("--timeout", type=float, default=30.0)
    args = ap.parse_args()

    if not MANIFEST.is_file():
        raise SystemExit(f"Missing {MANIFEST}. Build it first (see README).")

    rows = list(csv.DictReader(MANIFEST.open(encoding="utf-8")))
    (RAW / "html").mkdir(parents=True, exist_ok=True)
    (RAW / "pdf").mkdir(parents=True, exist_ok=True)

    log_rows, ok, skipped, failed = [], 0, 0, []
    sess = requests.Session()
    sess.headers.update({"User-Agent": UA})

    for r in rows:
        doc_id, url, fmt = r["doc_id"], r["url"], r["format"]
        dest = out_path(doc_id, fmt)
        if dest.exists() and not args.force:
            skipped += 1
            print(f"skip   {doc_id} (cached)")
            continue
        try:
            resp = sess.get(url, timeout=args.timeout, allow_redirects=True)
            status = resp.status_code
            if status == 200 and resp.content:
                dest.write_bytes(resp.content)
                sha = hashlib.sha256(resp.content).hexdigest()[:16]
                ok += 1
                print(f"OK     {doc_id}  {status}  {len(resp.content):>8} B")
                log_rows.append(dict(doc_id=doc_id, url=url, status=status, bytes=len(resp.content),
                                     sha256=sha, format=fmt, date=date.today().isoformat(), result="ok"))
            else:
                failed.append((doc_id, f"HTTP {status}"))
                print(f"FAIL   {doc_id}  HTTP {status}")
                log_rows.append(dict(doc_id=doc_id, url=url, status=status, bytes=0, sha256="",
                                     format=fmt, date=date.today().isoformat(), result=f"http_{status}"))
        except requests.RequestException as e:
            failed.append((doc_id, type(e).__name__))
            print(f"FAIL   {doc_id}  {type(e).__name__}")
            log_rows.append(dict(doc_id=doc_id, url=url, status=0, bytes=0, sha256="",
                                 format=fmt, date=date.today().isoformat(), result=type(e).__name__))
        time.sleep(args.delay)

    # append/refresh log
    write_header = not LOG.exists()
    with LOG.open("a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["doc_id", "url", "status", "bytes", "sha256", "format", "date", "result"])
        if write_header:
            w.writeheader()
        w.writerows(log_rows)

    print(f"\n=== scrape summary ===  ok {ok} | cached {skipped} | failed {len(failed)} / {len(rows)} total")
    if failed:
        print("failed (retry manually or note as unavailable):")
        for doc_id, why in failed:
            print(f"  {doc_id}: {why}")
    print(f"log: {LOG.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
