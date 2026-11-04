import re
from pathlib import Path
real = {str(p.relative_to("docs")) for p in Path("docs/photos").rglob("*") if p.is_file()}
used = set(re.findall(r'photos/[^"\'\s)]+', Path("docs/index.html").read_text()))
for p in sorted(used - real):
    print("MISSING:", p)
for p in sorted(real - used):
    print("NOT USED:", p)
print("checked", len(used), "photos")
