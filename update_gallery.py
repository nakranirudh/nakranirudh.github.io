import os
import json
from PIL import Image
from PIL.ExifTags import TAGS
import pillow_heif

# Register HEIC / HEIF format support in Pillow
pillow_heif.register_heif_opener()

IMAGE_DIR = "images/photography"
OUTPUT_JSON = os.path.join(IMAGE_DIR, "photos.json")
SUPPORTED_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif")

def get_exif_data(img):
    """Extract focal length, aperture, shutter speed, and ISO from photo EXIF."""
    try:
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
        return " • ".join(parts) if parts else "IPHONE EXPOSURE"

    except Exception:
        return "STANDARD EXPOSURE"

def build_manifest():
    photos = []
    if not os.path.exists(IMAGE_DIR):
        os.makedirs(IMAGE_DIR)

    files = sorted([f for f in os.listdir(IMAGE_DIR) if f.lower().endswith(SUPPORTED_EXTS)])

    for idx, fname in enumerate(files, 1):
        full_path = os.path.join(IMAGE_DIR, fname)
        base_name, ext = os.path.splitext(fname)

        try:
            img = Image.open(full_path)
            exif_info = get_exif_data(img)

            # Auto-convert HEIC/HEIF to JPG for browser display
            if ext.lower() in (".heic", ".heif"):
                jpg_filename = f"{base_name}.jpg"
                jpg_path = os.path.join(IMAGE_DIR, jpg_filename)
                
                # Convert color mode if necessary & save as JPEG
                if img.mode != "RGB":
                    img = img.convert("RGB")
                img.save(jpg_path, "JPEG", quality=85)
                
                # Update reference to converted JPG file
                fname = jpg_filename
                full_path = jpg_path

            clean_name = base_name.upper().replace("-", "_").replace(" ", "_")
            title = f"#{idx:02d} // {clean_name}"

            photos.append({
                "title": title,
                "exif": exif_info,
                "src": f"{IMAGE_DIR}/{fname}"
            })

        except Exception as e:
            print(f"Skipping {fname} due to error: {e}")

    with open(OUTPUT_JSON, "w") as f:
        json.dump(photos, f, indent=2)

    print(f"Successfully processed gallery with {len(photos)} photos.")

if __name__ == "__main__":
    build_manifest()
