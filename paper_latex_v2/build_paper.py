#!/usr/bin/env python3
"""
Build script for the LaTeX paper. Downloads v2.tex, figures, and compiles.

Usage:
    python3 build_paper.py            # download everything + compile
    python3 build_paper.py no-compile # download only
"""
import os
import subprocess
import sys
import urllib.request

PAPER_DIR = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.join(PAPER_DIR, "figures")
TEX_FILE = os.path.join(PAPER_DIR, "v2.tex")

# S3 URLs
V2_TEX_URL = "https://backend.composio.dev/api/v3/sl/-nLcNuenpl"
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

def download_file(url, out_path):
    if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
        print(f"  Skipping {os.path.basename(out_path)} (already exists)")
        return
    print(f"  Downloading {os.path.basename(out_path)}...")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    with open(out_path, 'wb') as f:
        f.write(data)
    print(f"    Saved: {len(data)} bytes")

def download_tex():
    download_file(V2_TEX_URL, TEX_FILE)

def download_figures():
    os.makedirs(FIG_DIR, exist_ok=True)
    for fname, url in FIGURE_URLS.items():
        download_file(url, os.path.join(FIG_DIR, fname))

def compile_paper():
    for run in [1, 2]:
        print(f"  pdflatex run {run}...")
        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "v2.tex"],
            cwd=PAPER_DIR, capture_output=True, text=True
        )
        print(f"    returncode={result.returncode}")
    pdf_path = os.path.join(PAPER_DIR, "v2.pdf")
    if os.path.exists(pdf_path):
        print(f"\nDone! PDF: {pdf_path} ({os.path.getsize(pdf_path)} bytes)")
    else:
        print("\nPDF was not generated. Check pdflatex output.")

if __name__ == "__main__":
    print("Step 1: Downloading v2.tex...")
    download_tex()
    print("\nStep 2: Downloading figures...")
    download_figures()
    print("\nStep 3: Compiling LaTeX...")
    if len(sys.argv) > 1 and sys.argv[1] == "no-compile":
        print("Skipping compile (--no-compile)")
    else:
        compile_paper()
    print("\nDone.")
