"""Move a photo to the front of a city's carousel.
  python reorder.py banff-2025/01-banff=2 france-2026/01-chamonix=5
The number is the photo's current position (1 = first). Each change is also
added to postcards_brief.md so future regenerates keep the same first photo.
"""
import re, sys
from pathlib import Path
page = Path("docs/index.html")
lines = page.read_text().split("\n")
brief_lines = []
for arg in sys.argv[1:]:
    folder, n = arg.split("=")
    n = int(n)
    idx = [i for i, l in enumerate(lines) if re.search(r'["\']photos/' + re.escape(folder) + r'/[^"\']+["\']', l)]
    if n < 1 or n > len(idx):
        print(f"{folder}: found {len(idx)} photos, can't move #{n}. Skipped.")
        continue
    def split_comma(s):
        t = s.rstrip()
        return (t[:-1], True) if t.endswith(",") else (t, False)
    parts = [split_comma(lines[i]) for i in idx]
    texts = [p[0] for p in parts]
    texts.insert(0, texts.pop(n - 1))
    for i, (t, (_, comma)) in zip(idx, zip(texts, parts)):
        lines[i] = t + ("," if comma else "")
    first = re.search(r'photos/[^"\']+', lines[idx[0]]).group(0)
    name = first.rsplit("/", 1)[1]
    print(f"{folder}: now starts on {name}")
    brief_lines.append(f"- {folder} starts on {name}")
page.write_text("\n".join(lines))
if brief_lines:
    with open("postcards_brief.md", "a") as f:
        f.write("\n\nFirst photo order (required): each city's carousel starts on this photo, and the rest follow in their original order:\n" + "\n".join(brief_lines) + "\n")
    print("Saved to postcards_brief.md")
