"""Update the postcard context without re-describing photos that are already done.
Notes, itineraries, and style files are always re-read. Photos only go through
LLaVA if they don't have a description yet. Removed files drop out automatically.

  python update_context.py
  python update_context.py --redo trips/japan-2026/01-japan/R0001381.JPG
"""
import argparse, re
from pathlib import Path
from universal_context import Document, source_label

HEADER = re.compile(r"^--- Source: (.+) ---\s*$", re.MULTILINE)
PROMPT = "Describe this image in detail and extract visible text. State uncertainty."

def read_snapshot(path):
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    matches = list(HEADER.finditer(text))
    saved = {}
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        saved[m.group(1)] = text[m.end():end].strip()
    return saved

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", default="postcards")
    parser.add_argument("--snapshot", default="prepared_postcards/trip.txt")
    parser.add_argument("--redo", nargs="*", default=[])
    args = parser.parse_args()
    root = Path(args.folder).resolve()
    snapshot = Path(args.snapshot)
    saved = read_snapshot(snapshot)
    redo = set(args.redo)
    docs, reused, described = [], 0, 0
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if any(p.startswith(".") for p in rel.parts) or path.is_symlink() or not path.is_file():
            continue
        source = rel.as_posix()
        suffix = path.suffix.lower()
        if suffix in {".txt", ".md"}:
            docs.append(Document(source, "text", path.read_text(encoding="utf-8")))
        elif suffix == ".pdf":
            from pypdf import PdfReader
            for n, page in enumerate(PdfReader(path).pages, 1):
                docs.append(Document(source, "pdf", page.extract_text() or "", n))
        elif suffix in {".jpg", ".jpeg", ".png"}:
            label = f"{source} (image)"
            if label in saved and source not in redo:
                docs.append(Document(source, "image", saved[label]))
                reused += 1
            else:
                import ollama
                print("describing", source, flush=True)
                reply = ollama.chat(model="llava", messages=[
                    {"role": "user", "content": PROMPT, "images": [str(path)]}])
                docs.append(Document(source, "image", reply["message"]["content"]))
                described += 1
    docs = [d for d in docs if d.text.strip()]
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    snapshot.write_text("\n\n".join(
        f"--- Source: {source_label(d)} ---\n{d.text}" for d in docs), encoding="utf-8")
    print(f"Saved {snapshot}: {reused} photos reused, {described} newly described")

if __name__ == "__main__":
    main()
