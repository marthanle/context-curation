"""Check postcards/postcards.json and write docs/postcards-data.js for the site.

  python build_site.py

The page (docs/index.html) is a fixed template. It reads every postcard from
docs/postcards-data.js, which this script writes. Run it after any change to
postcards.json, then deploy.
"""
import json
import sys
from pathlib import Path

DATA = Path("postcards/postcards.json")
OUT = Path("docs/postcards-data.js")
PHOTOS = Path("docs/photos")
STAMPS = {"mountain", "lake", "eiffel", "fuji", "palm-waves", "palm-sun", "matterhorn", "city"}


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    problems, warnings, used = [], [], set()

    for t in data["trips"]:
        where = t.get("folder", "?")
        for key in ("folder", "name", "year", "continent", "cities"):
            if key not in t:
                problems.append(f"{where}: missing '{key}'")
        for c in t.get("cities", []):
            cw = f"{where}/{c.get('folder', '?')}"
            for key in ("folder", "name", "caption", "lat", "lng", "postcards"):
                if key not in c:
                    problems.append(f"{cw}: missing '{key}'")
            if c.get("stamp") not in STAMPS:
                warnings.append(f"{cw}: stamp '{c.get('stamp')}' isn't one of {sorted(STAMPS)}, it'll use a plain compass")
            for p in c.get("postcards", []):
                path = PHOTOS / t["folder"] / c["folder"] / p.get("photo", "")
                used.add(path.as_posix())
                # exact, case-sensitive match, because the live site cares about .JPG vs .jpg
                if not path.is_file() or path.name not in {f.name for f in path.parent.iterdir()}:
                    problems.append(f"{cw}: photo '{p.get('photo')}' doesn't exist in {path.parent}")
                note = p.get("note", "")
                if not note.strip():
                    warnings.append(f"{cw}/{p.get('photo')}: empty note")
                if "—" in note or "–" in note:
                    warnings.append(f"{cw}/{p.get('photo')}: note has a dash, you might want to reword it")

    for f in sorted(PHOTOS.rglob("*")):
        if f.is_file() and not f.name.startswith(".") and f.as_posix() not in used:
            warnings.append(f"not on a postcard yet: {f.as_posix()} (run write_postcards.py)")

    for w in warnings:
        print("note:", w)
    if problems:
        for p in problems:
            print("PROBLEM:", p)
        sys.exit("Fix the problems above, then run build_site.py again. The site was not updated.")

    OUT.write_text("/* written by build_site.py from postcards/postcards.json. edit that file, not this one. */\n"
                   "window.POSTCARDS = " + json.dumps(data, ensure_ascii=False, indent=1) + ";\n",
                   encoding="utf-8")
    count = sum(len(c["postcards"]) for t in data["trips"] for c in t["cities"])
    print(f"Built {OUT}: {len(data['trips'])} trips, {count} postcards")


if __name__ == "__main__":
    main()
