#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright

PAGE_URL="https://www.fantacalcio.it/quotazioni-fantacalcio"
TZ=ZoneInfo("Europe/Rome")

def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()

def main():
    if len(sys.argv)!=2:
        raise SystemExit("Uso: python tools/fetch_fantacalcio_snapshot.py <output-dir>")
    root=Path(sys.argv[1]).resolve(); root.mkdir(parents=True,exist_ok=True)
    tmp=root/"download.tmp.xlsx"
    profile=Path.home()/".fs-fantacalcio-browser"
    with sync_playwright() as p:
        ctx=p.chromium.launch_persistent_context(str(profile), headless=False, accept_downloads=True)
        page=ctx.new_page(); page.goto(PAGE_URL, wait_until="domcontentloaded", timeout=120000)
        with page.expect_download(timeout=120000) as pending:
            page.get_by_text("Scarica", exact=True).click()
        pending.value.save_as(tmp)
        (root/"quotazioni_fantacalcio_2026_27.html").write_text(page.content(),encoding="utf-8")
        ctx.close()
    digest=sha256_file(tmp)
    dest=root/digest; dest.mkdir(exist_ok=False)
    final=dest/"Quotazioni_Fantacalcio_Stagione_2026_27.xlsx"
    tmp.replace(final)
    (dest/"Quotazioni_Fantacalcio_Stagione_2026_27.xlsx.sha256").write_text(f"{digest}  {final.name}\n")
    (dest/"source_receipt.json").write_text(json.dumps({
      "schema":"FS_SOURCE_RECEIPT_V1","source":"Fantacalcio.it","page_url":PAGE_URL,
      "download_method":"authenticated_browser_official_scarica",
      "fetched_at":datetime.now(TZ).isoformat(),"sha256":digest,"bytes":final.stat().st_size,
      "filename":final.name
    },ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(final); print(digest)

if __name__=="__main__":
    main()
