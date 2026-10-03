import os
import json
from PIL import Image
import pillow_heif

# Register HEIC format support
pillow_heif.register_heif_opener()

IMAGE_DIR = "images/photography"
OUTPUT_JSON = os.path.join(IMAGE_DIR, "photos.json")
WEB_EXTS = (".jpg", ".jpeg", ".png", ".webp")

# EXIF Tag IDs
TAG_FOCAL = 37386
TAG_APERTURE = 33437
TAG_SHUTTER = 33434
TAG_ISO = 34855
TAG_GPS = 34853

def get_gps_location(exif):
    """Extract GPS coordinates from EXIF and format as latitude/longitude."""
    try:
        gps_ifd = exif.get_ifd(TAG_GPS)
        if not gps_ifd:
            return None

        lat_ref = gps_ifd.get(1)
        lat_tuple = gps_ifd.get(2)
        lon_ref = gps_ifd.get(3)
        lon_tuple = gps_ifd.get(4)

        if not (lat_ref and lat_tuple and lon_ref and lon_tuple):
            return None

        def convert_to_degrees(value):
            d = float(value[0])
            m = float(value[1])
            s = float(value[2])
            return d + (m / 60.0) + (s / 3600.0)

        lat = convert_to_degrees(lat_tuple)
        lon = convert_to_degrees(lon_tuple)

        lat_dir = lat_ref if lat_ref in ("N", "S") else ("N" if lat >= 0 else "S")
        lon_dir = lon_ref if lon_ref in ("E", "W") else ("E" if lon >= 0 else "W")

        return f"{abs(lat):.2f}° {lat_dir}, {abs(lon):.2f}° {lon_dir}"
    except Exception:
        return None

def get_exif_data(img):
    """Extract focal length, aperture, shutter speed, ISO, and GPS location."""
    try:
        exif = img.getexif()
        if not exif:
            return ""

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
        location_str = get_gps_location(exif)

        parts = [p for p in [focal_str, aperture_str, shutter_str, iso_str, location_str] if p]
        return " • ".join(parts)

    except Exception:
        return ""

def convert_heic_files():
    """Pass 1: Convert HEIC/HEIF files to JPG while preserving full EXIF & GPS tags."""
    if not os.path.exists(IMAGE_DIR):
        os.makedirs(IMAGE_DIR)

    for fname in os.listdir(IMAGE_DIR):
        base_name, ext = os.path.splitext(fname)
        if ext.lower() in (".heic", ".heif"):
            heic_path = os.path.join(IMAGE_DIR, fname)
            jpg_filename = f"{base_name}.jpg"
            jpg_path = os.path.join(IMAGE_DIR, jpg_filename)

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

                    print(f"Converted HEIC -> JPG (EXIF preserved): {fname}")
                except Exception as e:
                    print(f"Error converting {fname}: {e}")

def build_manifest():
    """Pass 2: Build photos.json exclusively from web-ready formats."""
    convert_heic_files()

    files = sorted([f for f in os.listdir(IMAGE_DIR) if f.lower().endswith(WEB_EXTS)])

    photos = []
    seen_bases = set()

    for fname in files:
        base_name, _ = os.path.splitext(fname)
        
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

    print(f"Successfully generated manifest with {len(photos)} photos.")

if __name__ == "__main__":
    build_manifest()
