from __future__ import annotations

import argparse
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = PROJECT_ROOT / "storyseed_app" / "static" / "assets"
MANIFEST_PATH = ASSET_DIR / "manifest.json"
CSS_PATH = PROJECT_ROOT / "storyseed_app" / "static" / "app.css"
JS_PATH = PROJECT_ROOT / "storyseed_app" / "static" / "app.js"
RELEASE_VERIFY_PATH = PROJECT_ROOT / "scripts" / "verify_release_zip.ps1"

SOF_MARKERS = {
    0xC0,
    0xC1,
    0xC2,
    0xC3,
    0xC5,
    0xC6,
    0xC7,
    0xC9,
    0xCA,
    0xCB,
    0xCD,
    0xCE,
    0xCF,
}

STANDALONE_MARKERS = {0x01, *range(0xD0, 0xD8)}


def jpeg_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if len(data) < 4 or data[:2] != b"\xff\xd8":
        raise ValueError(f"{path.name} is not a JPEG file")

    index = 2
    while index < len(data):
        # Find marker prefix.
        while index < len(data) and data[index] != 0xFF:
            index += 1
        while index < len(data) and data[index] == 0xFF:
            index += 1
        if index >= len(data):
            break

        marker = data[index]
        index += 1
        if marker in STANDALONE_MARKERS:
            continue
        if marker in {0xD8, 0xD9}:
            continue
        if index + 2 > len(data):
            break

        segment_length = int.from_bytes(data[index : index + 2], "big")
        if segment_length < 2 or index + segment_length > len(data):
            break
        if marker in SOF_MARKERS:
            if segment_length < 7:
                break
            height = int.from_bytes(data[index + 3 : index + 5], "big")
            width = int.from_bytes(data[index + 5 : index + 7], "big")
            return width, height
        index += segment_length

    raise ValueError(f"Could not read JPEG dimensions for {path.name}")


def png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path.name} is not a PNG file")
    if data[12:16] != b"IHDR":
        raise ValueError(f"{path.name} does not have an IHDR chunk")
    width = int.from_bytes(data[16:20], "big")
    height = int.from_bytes(data[20:24], "big")
    return width, height


def image_dimensions(path: Path) -> tuple[int, int]:
    if path.suffix.lower() in {".jpg", ".jpeg"}:
        return jpeg_dimensions(path)
    if path.suffix.lower() == ".png":
        return png_dimensions(path)
    raise ValueError(f"{path.name} is not a supported image type")


def load_manifest(root: Path = PROJECT_ROOT) -> dict:
    manifest_path = root / "storyseed_app" / "static" / "assets" / "manifest.json"
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def validate(root: Path = PROJECT_ROOT) -> list[str]:
    asset_dir = root / "storyseed_app" / "static" / "assets"
    css = (root / "storyseed_app" / "static" / "app.css").read_text(encoding="utf-8")
    js = (root / "storyseed_app" / "static" / "app.js").read_text(encoding="utf-8")
    html = (root / "storyseed_app" / "templates" / "index.html").read_text(encoding="utf-8")
    release_verify = (root / "scripts" / "verify_release_zip.ps1").read_text(encoding="utf-8")
    manifest = load_manifest(root)
    errors: list[str] = []
    ids: set[str] = set()

    for asset in manifest.get("assets", []):
        asset_id = str(asset.get("id", "")).strip()
        filename = str(asset.get("file", "")).strip()
        css_variable = str(asset.get("css_variable", "")).strip()
        body_page = asset.get("body_page")
        path = asset_dir / filename
        web_path = f"/static/assets/{filename}"
        release_path = f"storyseed_app\\static\\assets\\{filename}"

        if not asset_id:
            errors.append(f"{filename or '<missing file>'}: missing id")
        elif asset_id in ids:
            errors.append(f"{asset_id}: duplicate id")
        ids.add(asset_id)

        if not path.exists():
            errors.append(f"{asset_id}: missing file {filename}")
            continue

        width, height = image_dimensions(path)
        size = path.stat().st_size
        if width < int(asset.get("minimum_width", 0)):
            errors.append(f"{asset_id}: width {width} is below minimum")
        if height < int(asset.get("minimum_height", 0)):
            errors.append(f"{asset_id}: height {height} is below minimum")
        if size < int(asset.get("minimum_bytes", 0)):
            errors.append(f"{asset_id}: file size {size} is below minimum")
        if size > int(asset.get("maximum_bytes", 10**9)):
            errors.append(f"{asset_id}: file size {size} is above maximum")

        if css_variable:
            css_reference = f'{css_variable}: url("{web_path}")'
            if css_reference not in css:
                errors.append(f"{asset_id}: CSS variable does not point at {web_path}")
        if asset.get("html_reference") and web_path not in html:
            errors.append(f"{asset_id}: asset is not referenced in index.html")
        if asset.get("preload") and f'"{web_path}"' not in js:
            errors.append(f"{asset_id}: asset is not preloaded in app.js")
        if asset.get("release_required") and release_path not in release_verify:
            errors.append(f"{asset_id}: release verifier does not require {filename}")
        if body_page:
            body_selector = f'body[data-page="{body_page}"]'
            page_wallpaper = f"--page-wallpaper: var({css_variable});"
            if body_selector not in css:
                errors.append(f"{asset_id}: missing CSS body page selector for {body_page}")
            if page_wallpaper not in css:
                errors.append(f"{asset_id}: body page does not use {css_variable}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify StorySeed visual asset contracts.")
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT, help="Project root to verify.")
    args = parser.parse_args()
    errors = validate(args.root.resolve())
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    count = len(load_manifest(args.root.resolve()).get("assets", []))
    print(f"StorySeed visual assets verified: {count} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
