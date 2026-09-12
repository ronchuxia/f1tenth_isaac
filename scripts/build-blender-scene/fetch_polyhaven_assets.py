"""Download the CC0 Poly Haven assets used by the final atrium and Tepper builders.

Reads MANIFEST, fetches every file with the Poly Haven files API, writes them
under blender/assets/polyhaven/<type>/<id>/, and records sizes and md5 in
blender/assets/polyhaven/manifest.json. Existing files with a matching size are skipped.
Model .blend files keep their bundled texture paths relative to the .blend.
"""
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "blender" / "assets" / "polyhaven"
API = "https://api.polyhaven.com/files/"
HEADERS = {"User-Agent": "Mozilla/5.0 (f1tenth-isaac blender scene builder)"}
RESOLUTION = "2k"
ATRIUM_MAPS = ("Diffuse", "nor_gl", "Rough", "AO")
TEPPER_MAPS = ("Diffuse", "nor_gl", "Rough")

MANIFEST = {
    "textures": {
        "dirty_carpet": ("Diffuse",),
        "oak_veneer_01": ("Diffuse", "nor_gl"),
        "denim_fabric": ATRIUM_MAPS,
        "white_plaster_02": TEPPER_MAPS,
        "concrete_floor_worn_001": TEPPER_MAPS,
        "okoume_veneer": TEPPER_MAPS,
    },
    "models": ("SchoolChair_01", "tree_small_02", "fire_alarm"),
}


def fetch_json(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=60) as response:
        return json.load(response)


def download(url, path, size):
    if path.exists() and path.stat().st_size == size:
        return "cached"
    path.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=300) as response:
        path.write_bytes(response.read())
    return "downloaded"


def record(entries, asset_id, kind, path, info):
    entries.append({
        "asset": asset_id,
        "type": kind,
        "file": str(path.relative_to(ROOT)),
        "size": info["size"],
        "md5": info.get("md5"),
        "url": info["url"],
    })


def main():
    entries = []
    for asset_id, maps in MANIFEST["textures"].items():
        files = fetch_json(API + asset_id)
        for map_name in maps:
            variants = files[map_name][RESOLUTION]
            info = variants.get("jpg") or variants["png"]
            path = OUT / "textures" / asset_id / Path(info["url"]).name
            print(asset_id, map_name, download(info["url"], path, info["size"]))
            record(entries, asset_id, "texture", path, info)

    for asset_id in MANIFEST["models"]:
        files = fetch_json(API + asset_id)
        info = files["blend"][RESOLUTION]["blend"]
        folder = OUT / "models" / asset_id
        path = folder / Path(info["url"]).name
        print(asset_id, "blend", download(info["url"], path, info["size"]))
        record(entries, asset_id, "model", path, info)
        for relative, texture in info.get("include", {}).items():
            texture_path = folder / relative
            print(asset_id, relative, download(texture["url"], texture_path, texture["size"]))
            record(entries, asset_id, "model_texture", texture_path, texture)

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "manifest.json").write_text(json.dumps({
        "license": "CC0 1.0 (https://polyhaven.com/license)",
        "source": "https://polyhaven.com",
        "files": entries,
    }, indent=2))
    total = sum(entry["size"] for entry in entries)
    print(f"{len(entries)} files, {total / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
