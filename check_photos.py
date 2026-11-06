import re
from pathlib import Path
html = Path("docs/index.html").read_text()
real = [p for p in Path("docs/photos").rglob("*") if p.is_file() and not p.name.startswith(".")]
real_names = {p.name for p in real}
problems = 0
for name in sorted(set(re.findall(r'[\w-]+\.(?:jpe?g|JPE?G|png|PNG)', html))):
    if name not in real_names:
        print("MADE UP OR MISTYPED:", name); problems += 1
for p in sorted(real):
    if p.name not in html:
        print("NOT USED:", p.relative_to("docs"))
folders = {p.parent.name for p in real} | {p.parent.parent.name for p in real}
for f in sorted(folders):
    if f not in html:
        print("FOLDER NOT IN PAGE:", f); problems += 1
if "photos/trips/" in html:
    print("BAD PATH: page uses photos/trips/"); problems += 1
print("checked", len(real), "photos,", problems, "problems")
