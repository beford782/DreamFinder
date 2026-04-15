#!/usr/bin/env python3
"""
Generate a PDF version of onboarding/Onboarding_Guide.md.

Usage:
    python tools/md_to_pdf.py

Writes to onboarding/DreamFinder_Onboarding_Guide.pdf
"""
import os
import sys
import markdown
from weasyprint import HTML, CSS

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO_ROOT, 'onboarding', 'Onboarding_Guide.md')
OUT = os.path.join(REPO_ROOT, 'onboarding', 'DreamFinder_Onboarding_Guide.pdf')

CSS_STYLES = """
@page {
  size: Letter;
  margin: 0.75in;
  @bottom-right {
    content: "Page " counter(page) " of " counter(pages);
    font-family: 'Helvetica', sans-serif;
    font-size: 9pt;
    color: #888;
  }
  @bottom-left {
    content: "DreamFinder Onboarding";
    font-family: 'Helvetica', sans-serif;
    font-size: 9pt;
    color: #888;
  }
}
body {
  font-family: 'Helvetica', 'Arial', sans-serif;
  font-size: 10.5pt;
  line-height: 1.5;
  color: #1a1a1a;
}
h1 {
  font-size: 22pt;
  color: #0f1f33;
  border-bottom: 3px solid #d4a84b;
  padding-bottom: 0.3em;
  margin-top: 0;
}
h2 {
  font-size: 15pt;
  color: #0f1f33;
  margin-top: 1.5em;
  border-bottom: 1px solid #ddd;
  padding-bottom: 0.2em;
}
h3 {
  font-size: 12pt;
  color: #1f3a5c;
  margin-top: 1.2em;
}
hr {
  border: none;
  border-top: 1px solid #ccc;
  margin: 1.5em 0;
}
a { color: #1f3a5c; text-decoration: none; }
code {
  background: #f4f1e8;
  padding: 1px 5px;
  border-radius: 3px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 9.5pt;
  color: #8B1A1A;
}
pre {
  background: #f4f1e8;
  padding: 0.75em;
  border-radius: 6px;
  border-left: 3px solid #d4a84b;
  font-size: 9pt;
  overflow-x: auto;
}
pre code { background: none; padding: 0; color: #1a1a1a; }
table {
  border-collapse: collapse;
  width: 100%;
  margin: 0.75em 0;
  font-size: 10pt;
}
th, td {
  border: 1px solid #ccc;
  padding: 0.5em 0.7em;
  text-align: left;
  vertical-align: top;
}
th {
  background: #0f1f33;
  color: #fff;
  font-weight: 600;
}
tr:nth-child(even) td { background: #fafaf6; }
ul, ol { padding-left: 1.5em; }
li { margin-bottom: 0.25em; }
blockquote {
  border-left: 3px solid #d4a84b;
  background: #fefcf6;
  padding: 0.5em 1em;
  margin: 1em 0;
  color: #555;
  font-style: italic;
}
strong { color: #0f1f33; }
"""

def main():
    with open(SRC, 'r', encoding='utf-8') as f:
        md_text = f.read()

    html_body = markdown.markdown(
        md_text,
        extensions=['extra', 'sane_lists', 'tables', 'fenced_code'],
    )
    html_doc = f"<!DOCTYPE html><html><head><meta charset='utf-8'></head><body>{html_body}</body></html>"

    HTML(string=html_doc, base_url=os.path.dirname(SRC)).write_pdf(
        OUT,
        stylesheets=[CSS(string=CSS_STYLES)],
    )
    size_kb = os.path.getsize(OUT) / 1024
    print(f"Wrote {OUT} ({size_kb:.0f} KB)")

if __name__ == '__main__':
    main()
