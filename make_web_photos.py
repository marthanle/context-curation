from pathlib import Path
from PIL import Image, ImageOps
for p in Path("postcards/trips").rglob("*"):
    if p.suffix.lower() in {".jpg", ".jpeg"}:
        dest = Path("docs/photos") / p.relative_to("postcards/trips")
        dest.parent.mkdir(parents=True, exist_ok=True)
        img = ImageOps.exif_transpose(Image.open(p)).convert("RGB")
        img.thumbnail((1600, 1600))
        img.save(dest, "JPEG", quality=82, optimize=True)
        print("saved", dest)
