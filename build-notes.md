# Build Notes: Postcards From Places I Love

An interactive postcard collection made from my own trip photos and notes, built with context stuffing and Gemini.

For each city on a trip, every photo becomes a postcard in a carousel. Click a postcard to flip it over and read a handwritten-style note about that moment. City tabs at the bottom switch between stops. Right now it has my France trip: Chamonix, Annecy, and Paris.

## How to view it

**Live site:** [paste your GitHub Pages link here]

**Or run it locally:**
```
git clone [paste your repo link here]
cd context-curation
open docs/index.html
```
On Windows, just double-click `docs/index.html`. No install needed to view it. The whole site is one HTML file plus the photos in `docs/photos/`.

## How to rebuild it with your own trip

My original photos and itinerary PDF aren't in the repo (they're large and the PDF has booking info), so to regenerate the site you'd use your own trip.

**1. Setup** (Python 3.12, Ollama running, and a Gemini API key)
```
python3.12 -m venv .venv-mcp
source .venv-mcp/bin/activate
python -m pip install -r requirements.txt pillow
python -m pip install --upgrade "google-genai>=1.55,<2"
ollama pull llava
export GEMINI_API_KEY="your-key"
```

**2. Add a trip.** Make a folder for the trip with one folder per stop. Put photos (.jpg or .png) and a `notes.md` in each stop. An optional `itinerary.md` or `.pdf` goes at the trip level.
```
postcards/
  style/                 my style guide and dislikes
  trips/
    your-trip/
      itinerary.md
      01-first-city/
        notes.md
        photo1.jpg
      02-second-city/
        notes.md
        photo1.jpg
```

**3. Make web-sized photos.** Resizes them and strips hidden GPS data.
```
python make_web_photos.py
```

**4. Prepare the context.** LLaVA looks at every photo locally and writes a description. Takes a few minutes.
```
python level1_raw_context.py --folder postcards --save-context prepared_postcards/trip.txt --prepare-only
```

**5. Have Gemini build the site.** The design brief is sent as the question.
```
python level1_raw_context.py --context-file prepared_postcards/trip.txt --provider gemini --model gemini-3.5-flash-lite --max-output-tokens 16384 --query "$(cat postcards_brief.md)" --results results/postcards.json
```
Wait for `Finish: STOP`. If you get a 503 or 504, Gemini is busy, just wait and rerun.

**6. Pull out the HTML, check the photos, and open it.**
```
python extract_html.py results/postcards.json docs/index.html
python check_photos.py
open docs/index.html
```
`check_photos.py` lists any photo the page points to that doesn't exist. If it shows a MISSING line, Gemini mistyped a filename. Fix it in `docs/index.html` or rerun step 5.

## What's in the repo

| File | What it does |
|---|---|
| `postcards/style/` | My style guide and dislikes, the same taste files from my matcha poster |
| `postcards/trips/` | My notes for each city (photos and PDF stay local) |
| `postcards_brief.md` | The design brief Gemini follows. This is where all the design decisions live |
| `make_web_photos.py` | Resizes photos for the web and removes location data |
| `extract_html.py` | Pulls the HTML out of Gemini's answer |
| `check_photos.py` | Catches broken or made-up photo filenames |
| `docs/` | The finished site, which GitHub Pages serves publicly |

## Why I made this

I travel a lot and I wanted something more personal than a camera roll. Postcards felt right because they're small, a little nostalgic, and each one is about one moment. It also fits my taste: soft, minimal, editorial, with lots of empty space.

The context stuffing is what makes it mine. Gemini can't write a note about my afternoon in Annecy unless it knows what I actually did there, so every card comes from my own notes, my photos, and my style files.

## How it evolved

I changed one thing at a time in the brief and regenerated each time.

- **v1:** Worked, but every photo was tinted green. My brief asked for a risograph look, and Gemini took that literally. The small photos under each card also didn't do anything.
- **v2:** Told it to keep photos in their real colors and added a lightbox for the small photos.
- **v3:** Changed captions from "annecy, august" to "annecy, france" and fixed the flip so you could turn the card back over.
- **v4:** The cards suddenly turned into squares that looked like polaroids, so I locked in a real 6 x 4 postcard shape.
- **v5:** Rebuilt it as a carousel per city, based on a mockup I made of how I pictured it.
- **v6:** Redesigned the back to look like a real vintage postcard, with a blush stamp, a curved postmark, and address lines.

## Failures and what fixed them

**Everything I didn't specify kept changing.** Gemini rebuilds the whole page from scratch every time, so fixing one thing sometimes changed something else, like the card shape. The fix was writing every decision I liked into the brief so it couldn't drift.

**It made up a photo.** One Paris card was blank because Gemini invented a filename that didn't exist and skipped a real photo. I wrote `check_photos.py` to catch this and added a rule to the brief to copy filenames exactly.

**The flip only worked one way.** The click was attached to the front of the card, so once it flipped there was nothing to click. I described exactly how to wire the click in the brief.

**Gemini Flash kept timing out**, so I used Flash-Lite.

## What I learned

- Being specific beats being descriptive. "Risograph look" got me green photos. "aspect-ratio: 3 / 2" got me exactly a postcard.
- When AI regenerates everything, anything you don't lock down is up for grabs.
- AI will confidently make things up, even filenames, so it's worth building small checks.
- Personal context is what makes the output feel like mine. The messages on the back only work because they come from my real notes.

## Next steps

- Add my Japan and Switzerland trips
- Separate the postcard content from the page design, so I can edit one card without regenerating the whole site
- Add a download button for each postcard
