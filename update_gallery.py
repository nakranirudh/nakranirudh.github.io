import os
import json
from PIL import Image
import pillow_heif

# Register HEIC format support
pillow_heif.register_heif_opener()

IMAGE_DIR = "images/photography"
OUTPUT_JSON = os.path.join(IMAGE_DIR, "photos.json")
WEB_EXTS = (".jpg", ".jpeg", ".png", ".webp")

# Tag IDs for EXIF metadata lookup
TAG_FOCAL = 37386
TAG_APERTURE = 33437
TAG_SHUTTER = 33434
TAG_ISO = 34855

def get_exif_data(img):
    """Extract focal length, aperture, shutter speed, and ISO."""
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

def convert_heic_files():
    """Pass 1: Convert HEIC/HEIF files to JPG while keeping EXIF data."""
    if not os.path.exists(IMAGE_DIR):
        os.makedirs(IMAGE_DIR)

    for fname in os.listdir(IMAGE_DIR):
        base_name, ext = os.path.splitext(fname)
        if ext.lower() in (".heic", ".heif"):
            heic_path = os.path.join(IMAGE_DIR, fname)
            jpg_filename = f"{base_name}.jpg"
            jpg_path = os.path.join(IMAGE_DIR, jpg_filename)

            # Convert if JPG doesn't exist yet
            if not os.path.exists(jpg_path):
                try:
                    img = Image.open(heic_path)
                    raw_exif = img.info.get("exif")
                    if img.mode != "RGB":
                        img = img.convert("RGB")

                    if raw_exif:
                        img.save(jpg_path, "JPEG", quality=85, exif=raw_exif)
                    else:
                        img.save(jpg_path, "JPEG", quality=85)

                    print(f"Converted HEIC -> JPG: {fname}")
                except Exception as e:
                    print(f"Error converting {fname}: {e}")

def build_manifest():
    """Pass 2: Build photos.json exclusively from web-ready formats."""
    convert_heic_files()

    # Get only web-supported image files (ignores .heic)
    files = sorted([f for f in os.listdir(IMAGE_DIR) if f.lower().endswith(WEB_EXTS)])

    photos = []
    seen_bases = set()

    for fname in files:
        base_name, _ = os.path.splitext(fname)
        
        # Prevent duplicates if base filename is repeated
        if base_name.lower() in seen_bases:
            continue
        seen_bases.add(base_name.lower())

        full_path = os.path.join(IMAGE_DIR, fname)
        try:
            img = Image.open(full_path)
            exif_info = get_exif_data(img)

            photos.append({
                "title": f"#{len(photos) + 1:02d}",
                "exif": exif_info,
                "src": f"{IMAGE_DIR}/{fname}"
            })
        except Exception as e:
            print(f"Skipping {fname}: {e}")

    with open(OUTPUT_JSON, "w") as f:
        json.dump(photos, f, indent=2)

    print(f"Successfully generated clean manifest with {len(photos)} unique photo(s).")

if __name__ == "__main__":
    build_manifest()
