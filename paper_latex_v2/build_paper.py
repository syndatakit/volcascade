#!/usr/bin/env python3
"""
Build script for the LaTeX paper. Downloads figures from S3 to figures/ and compiles.

Usage:
    python3 build_paper.py            # download figures + compile
    python3 build_paper.py no-compile # download figures only
"""
import base64
import json
import os
import subprocess
import sys
import urllib.request

PAPER_DIR = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.join(PAPER_DIR, "figures")
URLS_FILE = os.path.join(PAPER_DIR, "figures_urls.json")

# Figure URLs (these are stable S3 URLs)
FIGURE_URLS = {
    "fig1_pipeline.pdf": "https://backend.composio.dev/api/v3/sl/1ae0QMyaWR",
    "fig2_benchmark.pdf": "https://backend.composio.dev/api/v3/sl/EM1SIFEUsb",
    "fig3_nested_reg.pdf": "https://backend.composio.dev/api/v3/sl/jcW2cNfrrM",
    "fig4_dm_test.pdf": "https://backend.composio.dev/api/v3/sl/yOuCeSxVMf",
    "fig5_calibration.pdf": "https://backend.composio.dev/api/v3/sl/WxPmV8onvI",
    "fig6_fno_explain.pdf": "https://backend.composio.dev/api/v3/sl/T2lj3Of73H",
    "fig7_rolling.pdf": "https://backend.composio.dev/api/v3/sl/otvzI5_QcB",
    "fig8_strategy.pdf": "https://backend.composio.dev/api/v3/sl/MF0jtE_89i",
}

def download_figures():
    os.makedirs(FIG_DIR, exist_ok=True)
    for fname, url in FIGURE_URLS.items():
        out_path = os.path.join(FIG_DIR, fname)
        if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
            print(f"  Skipping {fname} (already exists)")
            continue
        print(f"  Downloading {fname}...")
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
            with open(out_path, 'wb') as f:
                f.write(data)
            print(f"    Saved {fname}: {len(data)} bytes")
        except Exception as e:
            print(f"    ERROR downloading {fname}: {e}")

def compile_paper():
    """Run pdflatex twice for cross-references, then optionally bibtex."""
    for run in [1, 2]:
        print(f"  pdflatex run {run}...")
        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "v2.tex"],
            cwd=PAPER_DIR, capture_output=True, text=True
        )
        print(f"    returncode={result.returncode}")
    bib_path = os.path.join(PAPER_DIR, "v2.bib")
    if os.path.exists(bib_path):
        print("  bibtex...")
        subprocess.run(["bibtex", "v2"], cwd=PAPER_DIR)
        subprocess.run(["pdflatex", "-interaction=nonstopmode", "v2.tex"], cwd=PAPER_DIR)
        subprocess.run(["pdflatex", "-interaction=nonstopmode", "v2.tex"], cwd=PAPER_DIR)
    pdf_path = os.path.join(PAPER_DIR, "v2.pdf")
    if os.path.exists(pdf_path):
        print(f"\\nDone! PDF: {pdf_path} ({os.path.getsize(pdf_path)} bytes)")
    else:
        print("\\nPDF was not generated. Check pdflatex output above.")

if __name__ == "__main__":
    print("Step 1: Downloading figures from S3...")
    download_figures()
    print("\\nStep 2: Compiling LaTeX...")
    if len(sys.argv) > 1 and sys.argv[1] == "no-compile":
        print("Skipping compile (--no-compile)")
    else:
        compile_paper()
    print("\\nDone.")
