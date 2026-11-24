"""Have Gemini write postcards for any photos that don't have one yet.

  python write_postcards.py                      # new photos only (the normal way)
  python write_postcards.py --redo japan-2026    # rewrite every note for one trip
  python write_postcards.py --dry-run            # show what it would ask, without calling Gemini

This is still Level 1 context stuffing: it sends Gemini the saved context
(prepared_postcards/trip.txt, made by update_context.py) plus a short brief, and
Gemini answers with postcard content as JSON. It never touches the page design,
so adding a trip can't break the layout. Postcards you already have are left
alone unless you use --redo.
"""
import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

import build_site

DATA = Path("postcards/postcards.json")
CONTEXT = Path("prepared_postcards/trip.txt")
PHOTOS = Path("docs/photos")
IMAGE_TYPES = {".jpg", ".jpeg", ".png"}
CONTINENTS = {"north america", "south america", "europe", "asia", "africa", "oceania"}

BRIEF = """You are writing the content for my travel postcard website. Everything you need is in the context:
my notes for each trip and city, my itineraries, my style guide, and a description of every photo.

Write postcards ONLY for the photos listed at the bottom. Each photo becomes one postcard.

The note on the back of each postcard:
- Written the way I would actually text a friend: first person (i, we, me), casual, warm, specific.
- Use real details from my notes for that city and what is in that specific photo's description.
- 10 to 30 words, all lowercase.
- Never sound like a photo caption. Good: "we got soft serve in the snow and it was so worth it".
  Bad: "savoring delicious ice cream cones in a cozy casual setting".
- Never include anyone's name, last names, addresses, booking or confirmation numbers, prices,
  phone numbers, homework, or classes. Say "we" instead of naming who I was with.
- Never use em dashes or en dashes.
- Only talk about the place in that folder. If an itinerary mentions other places (like a city I
  flew through), ignore them.

For each city, also give:
- "name": the city name shown on the tab, lowercase, like "annecy". If my notes give a
  "Postcard caption", use the place from it.
- "caption": the place and country, lowercase, like "annecy, france". If my notes for that city
  give a "Postcard caption", use exactly that. If the folder covers a whole country, use just the
  country, like "japan".
- "lat" and "lng": coordinates for the place, as numbers. For a whole country, use the middle of it.
- "stamp": one of: mountain, lake, eiffel, fuji, palm-waves, palm-sun, matterhorn, city.
  Pick the one that fits the place best.
And for each trip, "continent": one of: north america, south america, europe, asia, africa, oceania.

Copy every folder and photo filename exactly as listed below, character for character.

Answer with ONLY this JSON, inside one ```json code block:
{"trips": [{"folder": "TRIP-FOLDER", "continent": "...", "cities": [
  {"folder": "CITY-FOLDER", "name": "...", "caption": "...", "lat": 0, "lng": 0, "stamp": "...",
   "postcards": [{"photo": "FILENAME", "note": "..."}]}]}]}

Photos that need a postcard:
"""


def load():
    if DATA.exists():
        return json.loads(DATA.read_text(encoding="utf-8"))
    return {"trips": []}


def find(items, folder):
    return next((x for x in items if x.get("folder") == folder), None)


def photos_on_disk():
    """{(trip, city): [filenames]} for every web photo, in filename order."""
    found = {}
    for f in sorted(PHOTOS.glob("*/*/*")):
        if f.is_file() and f.suffix.lower() in IMAGE_TYPES and not f.name.startswith("."):
            found.setdefault((f.parent.parent.name, f.parent.name), []).append(f.name)
    return found


def answer_json(results_file):
    """Pull Gemini's JSON answer out of the Level 1 results file."""
    texts = []

    def walk(x):
        if isinstance(x, str):
            texts.append(x)
        elif isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)

    walk(json.loads(results_file.read_text(encoding="utf-8")))
    for text in sorted((t for t in texts if '"trips"' in t), key=len, reverse=True):
        m = re.search(r"```(?:json)?\s*\n(.*?)```", text, re.S)
        candidate = m.group(1) if m else text[text.find("{"):text.rfind("}") + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    return None


def clean_note(note):
    note = re.sub(r"\s*[—–]\s*", ", ", str(note)).strip()
    return note[:1].lower() + note[1:]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--redo", metavar="TRIP-FOLDER", help="rewrite every note for this trip, like japan-2026")
    ap.add_argument("--model", default="gemini-3.5-flash-lite")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    data = load()
    on_disk = photos_on_disk()
    needed = {}
    for (trip, city), files in on_disk.items():
        t = find(data["trips"], trip)
        c = find(t["cities"], city) if t else None
        have = {p["photo"] for p in c["postcards"]} if c else set()
        todo = files if args.redo == trip else [f for f in files if f not in have]
        if todo:
            needed[(trip, city)] = todo

    if args.redo and not any(t == args.redo for t, _ in needed):
        sys.exit(f"No photos found for '{args.redo}'. Check the folder name in docs/photos.")
    if not needed:
        print("Every photo already has a postcard.")
        build_site.main()
        return

    lines = []
    for (trip, city), files in sorted(needed.items()):
        lines.append(f"- trip folder {trip}, city folder {city}: " + ", ".join(files))
    query = BRIEF + "\n".join(lines)
    count = sum(len(v) for v in needed.values())
    print(f"Asking Gemini for {count} postcards:")
    print("\n".join(lines))
    if args.dry_run:
        print("\n(dry run, Gemini was not called)")
        return
    if not CONTEXT.exists():
        sys.exit(f"{CONTEXT} is missing. Run: python update_context.py")

    results = Path("results") / f"postcards-content-{time.strftime('%Y%m%d-%H%M%S')}.json"
    results.parent.mkdir(exist_ok=True)
    cmd = [sys.executable, "level1_raw_context.py", "--context-file", str(CONTEXT),
           "--provider", "gemini", "--model", args.model, "--max-output-tokens", "16384",
           "--query", query, "--results", str(results)]
    subprocess.run(cmd)
    if not results.exists():
        sys.exit("Gemini didn't save an answer. If you saw a 503 or 504 above, wait a minute and run this again.")
    answer = answer_json(results)
    if not answer:
        sys.exit(f"Couldn't find postcard JSON in Gemini's answer. Look at {results}, then run this again.")

    added, skipped = 0, []
    for at in answer.get("trips", []):
        tf = at.get("folder")
        if not any(t == tf for t, _ in needed):
            continue
        trip = find(data["trips"], tf)
        if not trip:
            m = re.match(r"(.+)-(\d{4})$", tf)
            trip = {"folder": tf, "name": (m.group(1) if m else tf).replace("-", " "),
                    "year": int(m.group(2)) if m else 0, "cities": []}
            data["trips"].append(trip)
        cont = str(at.get("continent", "")).lower()
        if not trip.get("continent") and cont in CONTINENTS:
            trip["continent"] = cont
        for ac in at.get("cities", []):
            cf = ac.get("folder")
            want = needed.get((tf, cf))
            if not want:
                continue
            city = find(trip["cities"], cf)
            if not city:
                city = {"folder": cf, "name": str(ac.get("name", cf.split("-", 1)[-1])).lower(),
                        "caption": str(ac.get("caption", "")).lower(),
                        "lat": ac.get("lat"), "lng": ac.get("lng"), "stamp": ac.get("stamp"),
                        "postcards": []}
                trip["cities"].append(city)
                trip["cities"].sort(key=lambda c: c["folder"])
            notes = {p.get("photo"): clean_note(p.get("note", "")) for p in ac.get("postcards", [])}
            for photo in want:
                if not notes.get(photo):
                    skipped.append(f"{tf}/{cf}/{photo}")
                    continue
                existing = next((p for p in city["postcards"] if p["photo"] == photo), None)
                if existing:
                    existing["note"] = notes[photo]
                else:
                    city["postcards"].append({"photo": photo, "note": notes[photo]})
                added += 1

    data["trips"].sort(key=lambda t: (t.get("year", 0), t.get("name", "")))
    DATA.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nSaved {added} postcards to {DATA}")
    if skipped:
        print("Gemini skipped these, so run write_postcards.py again to fill them in:")
        for s in skipped:
            print("  ", s)
    print("Read through the new notes in postcards/postcards.json and edit anything that doesn't sound like you.\n")
    build_site.main()


if __name__ == "__main__":
    main()
