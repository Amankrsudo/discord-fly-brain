#!/usr/bin/env python3
"""Build a review-only PDF from paper/REVIEW_MANUSCRIPT.md.

This is not the journal submission build. It deliberately preserves visible
placeholders and labels the result REVIEW ONLY — NOT FOR SUBMISSION.
"""
from __future__ import annotations

import html
import os
import re
from pathlib import Path

import markdown
from weasyprint import HTML

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "paper" / "REVIEW_MANUSCRIPT.md"
BIB = ROOT / "paper" / "references.bib"
OUT_DIR = ROOT / "build" / "review-manuscript"
OUT_HTML = OUT_DIR / "REVIEW_ONLY_NOT_FOR_SUBMISSION.html"
OUT_PDF = OUT_DIR / "REVIEW_ONLY_NOT_FOR_SUBMISSION.pdf"


def bib_field(entry: str, field: str) -> str:
    match = re.search(r"^\s*" + re.escape(field) + r"\s*=\s*\{(.*?)\}\s*,?\s*$",
                      entry, re.I | re.M | re.S)
    if not match:
        return ""
    return re.sub(r"\s+", " ", match.group(1)).strip()


def bibliography() -> str:
    raw = BIB.read_text(encoding="utf-8")
    entries = re.split(r"(?=^@\w+\{)", raw, flags=re.M)
    rendered = []
    for entry in entries:
        if not entry.lstrip().startswith("@"):
            continue
        key_match = re.match(r"\s*@\w+\{([^,]+),", entry)
        if not key_match:
            continue
        key = key_match.group(1).strip()
        author = bib_field(entry, "author")
        title = bib_field(entry, "title")
        year = bib_field(entry, "year")
        journal = bib_field(entry, "journal") or bib_field(entry, "howpublished")
        doi = bib_field(entry, "doi")
        note = bib_field(entry, "note")
        pieces = [f"<strong>{html.escape(key)}</strong>."]
        if author:
            pieces.append(html.escape(author) + ".")
        if year:
            pieces.append("(" + html.escape(year) + ").")
        if title:
            pieces.append(html.escape(title) + ".")
        if journal:
            pieces.append("<em>" + html.escape(journal) + "</em>.")
        if doi:
            pieces.append("doi: " + html.escape(doi) + ".")
        if note and ("VERIFY_REQUIRED" in note or "TODO" in note):
            pieces.append("<strong>Editorial flag:</strong> " + html.escape(note))
        rendered.append("<li>" + " ".join(pieces) + "</li>")
    if not rendered:
        raise SystemExit("No BibTeX entries could be rendered.")
    return "<ol class='references'>" + "".join(rendered) + "</ol>"


def main() -> None:
    if not SOURCE.is_file() or not BIB.is_file():
        raise SystemExit("Missing review manuscript source or references.bib.")
    source = SOURCE.read_text(encoding="utf-8")
    marker = "<!-- BIBLIOGRAPHY_INSERT -->"
    if source.count(marker) != 1:
        raise SystemExit("Expected exactly one bibliography insertion marker.")
    source = source.replace(marker, bibliography())
    body = markdown.markdown(
        source,
        extensions=["tables", "fenced_code", "sane_lists"],
        output_format="html5",
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sha = os.environ.get("GITHUB_SHA", "local-build / source SHA not supplied")
    css = """
      @page { size: A4; margin: 18mm 17mm 20mm;
        @bottom-center { content: "REVIEW ONLY — NOT FOR SUBMISSION · " counter(page);
          font-size: 8pt; color: #555; } }
      body { font-family: "DejaVu Sans", sans-serif; font-size: 9.2pt;
        line-height: 1.42; color: #202124; }
      h1 { font-size: 20pt; line-height: 1.2; margin-top: 1.2em; }
      h2 { font-size: 15pt; margin-top: 1.4em; }
      h3 { font-size: 11.5pt; margin-top: 1.2em; }
      p { orphans: 3; widows: 3; }
      blockquote { border-left: 3px solid #8a8a8a; padding-left: 10px; color: #333; }
      table { border-collapse: collapse; width: 100%; font-size: 8pt; }
      th, td { border: 0.5pt solid #a0a0a0; padding: 4px; vertical-align: top; }
      th { background: #eee; }
      img { max-width: 100%; max-height: 220mm; object-fit: contain; }
      h2:has(+ p img) { break-after: avoid; }
      figure, img { break-inside: avoid; }
      pre, code { white-space: pre-wrap; overflow-wrap: anywhere; font-size: 8pt; }
      .references li { margin-bottom: 7pt; overflow-wrap: anywhere; }
      a { color: #154c79; text-decoration: none; }
      hr { border: 0; border-top: 1px solid #bbb; margin: 18pt 0; }
    """
    html_doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
      <title>REVIEW ONLY — Fly Brain 3.0 manuscript</title>
      <meta name="source-commit" content="{html.escape(sha)}">
      <style>{css}</style></head><body>
      <div style="border:2px solid #9b1c1c;padding:10px;margin-bottom:16px;font-weight:bold;">
      REVIEW ONLY — NOT FOR SUBMISSION<br>
      Source commit: {html.escape(sha)}
      </div>{body}</body></html>"""
    OUT_HTML.write_text(html_doc, encoding="utf-8")
    HTML(string=html_doc, base_url=str(ROOT)).write_pdf(
        OUT_PDF,
        presentational_hints=True,
    )
    if not OUT_PDF.is_file() or OUT_PDF.stat().st_size < 20_000:
        raise SystemExit("PDF output is missing or unexpectedly small.")
    print(f"Built {OUT_PDF} ({OUT_PDF.stat().st_size} bytes); source commit={sha}")


if __name__ == "__main__":
    main()
