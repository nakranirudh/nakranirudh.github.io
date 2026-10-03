import os
import json
from PIL import Image
from PIL.ExifTags import TAGS
import pillow_heif

# Register HEIC format support
pillow_heif.register_heif_opener()

IMAGE_DIR = "images/photography"
OUTPUT_JSON = os.path.join(IMAGE_DIR, "photos.json")
SUPPORTED_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif")

# EXIF Tag IDs for direct lookup
TAG_FOCAL = 37386
TAG_APERTURE = 33437
TAG_SHUTTER = 33434
TAG_ISO = 34855

def get_exif_data(img):
    """Extract focal length, aperture, shutter speed, and ISO reliably."""
    try:
        exif = img.getexif()
        if not exif:
            return "STANDARD EXPOSURE"

        focal = exif.get(TAG_FOCAL)
        aperture = exif.get(TAG_APERTURE)
        shutter = exif.get(TAG_SHUTTER)
        iso = exif.get(TAG_ISO)

        focal_str = f"{int(focal)}mm" if focal else ""
        aperture_str = f"f/{float(aperture):.1f}" if aperture else ""
        
        if shutter:
            s_val = float(shutter)
            shutter_str = f"1/{int(1/s_val)}s" if s_val < 1 else f"{s_val}s"
        else:
            shutter_str = ""

        iso_str = f"ISO {iso}" if iso else ""

        parts = [p for p in [focal_str, aperture_str, shutter_str, iso_str] if p]
        return " • ".join(parts) if parts else "STANDARD EXPOSURE"

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

            # Auto-convert HEIC to JPG
            if ext.lower() in (".heic", ".heif"):
                jpg_filename = f"{base_name}.jpg"
                jpg_path = os.path.join(IMAGE_DIR, jpg_filename)
                
                if img.mode != "RGB":
                    img = img.convert("RGB")
                img.save(jpg_path, "JPEG", quality=85)
                
                fname = jpg_filename

            # Only show index string (#01, #02, etc.)
            title = f"#{idx:02d}"

            photos.append({
                "title": title,
                "exif": exif_info,
                "src": f"{IMAGE_DIR}/{fname}"
            })

        except Exception as e:
            print(f"Skipping {fname}: {e}")

    with open(OUTPUT_JSON, "w") as f:
        json.dump(photos, f, indent=2)

    print(f"Successfully processed {len(photos)} photos.")

if __name__ == "__main__":
    build_manifest()
