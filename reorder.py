"""Choose which photo a city's carousel starts on.

  python reorder.py japan-2026/01-japan            # list that city's photos with numbers
  python reorder.py japan-2026/01-japan=3          # move photo #3 to the front
  python reorder.py banff-2025/01-banff=2 france-2026/01-chamonix=5

Each photo keeps its own note when it moves. The site is rebuilt afterward.
"""
import json
import sys
from pathlib import Path

import build_site

DATA = Path("postcards/postcards.json")


def find_city(data, path):
    trip_folder, _, city_folder = path.partition("/")
    for t in data["trips"]:
        if t["folder"] == trip_folder:
            for c in t["cities"]:
                if c["folder"] == city_folder:
                    return c
    sys.exit(f"Couldn't find '{path}'. Use the folder names, like japan-2026/01-japan.")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    data = json.loads(DATA.read_text(encoding="utf-8"))
    changed = False
    for arg in sys.argv[1:]:
        path, _, n = arg.partition("=")
        city = find_city(data, path)
        cards = city["postcards"]
        if not n:
            print(f"{path}:")
            for i, p in enumerate(cards, 1):
                print(f"  {i}. {p['photo']}  {p['note'][:60]}")
            continue
        n = int(n)
        if not 1 <= n <= len(cards):
            sys.exit(f"{path} has {len(cards)} photos, so pick a number from 1 to {len(cards)}.")
        cards.insert(0, cards.pop(n - 1))
        print(f"{path} now starts on {cards[0]['photo']}")
        changed = True
    if changed:
        DATA.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        build_site.main()


if __name__ == "__main__":
    main()
