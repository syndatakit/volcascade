#!/usr/bin/env python3
"""Build theorems.tex from the 3 parts."""
import os
PARTS_DIR = os.path.dirname(os.path.abspath(__file__))
out_path = os.path.join(PARTS_DIR, "theorems.tex")
with open(out_path, 'w') as out:
    for fname in ["theorems_part1.md", "theorems_part2.md", "theorems_part3.md"]:
        path = os.path.join(PARTS_DIR, fname)
        if not os.path.exists(path):
            print(f"ERROR: {fname} not found"); exit(1)
        with open(path) as f:
            out.write(f.read())
        if fname != "theorems_part3.md":
            out.write("\n% === END OF PART ===\n\n")
print(f"Built {out_path} ({os.path.getsize(out_path)} bytes)")
print("Now run: pdflatex theorems.tex")
