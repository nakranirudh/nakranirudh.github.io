import os
import json
from PIL import Image
from PIL.ExifTags import TAGS

IMAGE_DIR = "images/photography"
OUTPUT_JSON = os.path.join(IMAGE_DIR, "photos.json")
SUPPORTED_EXTS = (".jpg", ".jpeg", ".png", ".webp")

def get_exif_data(image_path):
    try:
        img = Image.open(image_path)
        exif = img._getexif()
        if not exif:
            return "STANDARD EXPOSURE"

        exif_data = {TAGS.get(tag, tag): val for tag, val in exif.items()}

        focal = exif_data.get("FocalLength")
        aperture = exif_data.get("FNumber")
        shutter = exif_data.get("ExposureTime")
        iso = exif_data.get("ISOSpeedRatings")

        focal_str = f"{int(focal)}mm" if focal else ""
        aperture_str = f"f/{float(aperture):.1f}" if aperture else ""
        
        if shutter:
            s_val = float(shutter)
            shutter_str = f"1/{int(1/s_val)}s" if s_val < 1 else f"{s_val}s"
        else:
            shutter_str = ""

        iso_str = f"ISO {iso}" if iso else ""

        parts = [p for p in [focal_str, aperture_str, shutter_str, iso_str] if p]
        return " • ".join(parts) if parts else "35mm • f/5.6 • ISO 100"

    except Exception:
        return "STANDARD EXPOSURE"

def build_manifest():
    photos = []
    if not os.path.exists(IMAGE_DIR):
        os.makedirs(IMAGE_DIR)

    files = sorted([f for f in os.listdir(IMAGE_DIR) if f.lower().endswith(SUPPORTED_EXTS)])

    for idx, fname in enumerate(files, 1):
        full_path = os.path.join(IMAGE_DIR, fname)
        exif_info = get_exif_data(full_path)
        
        clean_name = os.path.splitext(fname)[0].upper().replace("-", "_").replace(" ", "_")
        title = f"#{idx:02d} // {clean_name}"

        photos.append({
            "title": title,
            "exif": exif_info,
            "src": f"{IMAGE_DIR}/{fname}"
        })

    with open(OUTPUT_JSON, "w") as f:
        json.dump(photos, f, indent=2)

    print(f"Successfully generated {OUTPUT_JSON} with {len(photos)} photos.")

if __name__ == "__main__":
    build_manifest()
