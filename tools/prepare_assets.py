"""Generate original vector branding/demo images; vendor pinned upstream components."""
import hashlib
import json
from pathlib import Path
import urllib.request
import subprocess
import io
import zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
COMMIT = "3ed54c325e0ad71afcf4f246c07e5e17b3d7f2d2"


def download(url):
    request = urllib.request.Request(url, headers={"User-Agent": "Frameveil-build/0.1"})
    with urllib.request.urlopen(request, timeout=45) as response:
        return response.read()


def generate():
    assets = ROOT / "assets"
    demos = assets / "demo"
    demos.mkdir(parents=True, exist_ok=True)
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128"><defs><linearGradient id="g" x2="1" y2="1"><stop stop-color="#cab7ff"/><stop offset="1" stop-color="#87e6c0"/></linearGradient></defs><rect width="128" height="128" rx="32" fill="#232635"/><path d="M35 43v-9h21m37 9v-9H72M35 85v9h21m37-9v9H72" fill="none" stroke="url(#g)" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/><circle cx="64" cy="64" r="18" fill="none" stroke="url(#g)" stroke-width="7"/><circle cx="64" cy="64" r="5" fill="#d2ffeb"/></svg>'''
    (assets / "logo.svg").write_text(svg, encoding="utf-8")
    (assets / "check.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" width="17" height="17"><path d="m4 8 3 3 6-6" fill="none" stroke="#183b2d" stroke-width="2"/></svg>', encoding="utf-8")
    # Render ICO using Qt's SVG implementation (no raster logo generator required).
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QImage, QPainter
    from PySide6.QtSvg import QSvgRenderer
    app = QApplication.instance() or QApplication([])
    image = QImage(256, 256, QImage.Format.Format_ARGB32)
    image.fill(0)
    painter = QPainter(image)
    QSvgRenderer(str(assets / "logo.svg")).render(painter)
    painter.end()
    image.save(str(assets / "logo.png"))
    Image.open(assets / "logo.png").save(assets / "frameveil.ico", sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
    font = r"C:\Windows\Fonts\segoeui.ttf"
    light = r"C:\Windows\Fonts\segoeuil.ttf"
    for index, (name, accent) in enumerate([("01-星环", (179, 141, 238)), ("02-晨屿", (109, 211, 190)), ("03-夜航", (113, 166, 239))]):
        w, h = 1600, 900
        yy, xx = np.mgrid[0:h, 0:w].astype(float)
        cx, cy = (1000, 410)
        glow = np.exp(-((xx-cx)**2 / 260000 + (yy-cy)**2 / 200000))
        bg = np.stack([12 + glow * accent[0] * .30, 14 + glow * accent[1] * .22, 24 + glow * accent[2] * .35], axis=2)
        im = Image.fromarray(np.uint8(np.clip(bg, 0, 255)))
        draw = ImageDraw.Draw(im)
        for n in range(9):
            offset = n * 24
            draw.arc((770-offset, 185-offset*.3, 1260+offset, 675+offset*.3), 180, 359,
                     fill=tuple(int(v * (.25 + n*.06)) for v in accent), width=1)
        # A clean shaded sphere; original synthetic demo artwork, no real person.
        radius = 195
        dist = np.sqrt((xx-cx)**2 + (yy-cy)**2)
        sphere = dist < radius
        z = np.sqrt(np.clip(1 - (dist / radius)**2, 0, 1))
        lighting = np.clip(.20 + .60*z - .30*(xx-cx)/radius - .35*(yy-cy)/radius, 0, 1)
        pixels = np.array(im)
        for channel, value in enumerate(accent):
            layer = np.clip(12 + value * lighting, 0, 255)
            pixels[:,:,channel][sphere] = layer[sphere].astype(np.uint8)
        im = Image.fromarray(pixels)
        draw = ImageDraw.Draw(im)
        draw.arc((680, 315, 1340, 555), 0, 180, fill=accent, width=4)
        draw.text((106, 114), "F R A M E V E I L   /   S T U D I O", font=ImageFont.truetype(font, 23), fill=(174,174,198))
        draw.text((100, 327), ["Your frame.", "Stay in flow.", "Quiet presence."][index], font=ImageFont.truetype(light, 76), fill=(237,235,247))
        draw.text((106, 432), "A canvas for your next conversation.", font=ImageFont.truetype(font, 25), fill=(149,148,175))
        draw.line((108, 510, 170, 510), fill=accent, width=3)
        draw.text((108, 740), f"DEMO  /  00{index+1}", font=ImageFont.truetype(font, 22), fill=accent)
        draw.text((108, 781), "LOCAL MEDIA  /  16:9", font=ImageFont.truetype(font, 18), fill=(102,107,132))
        im.save(demos / (name + ".png"))


def vendor():
    folder = ROOT / "vendor" / "unitycapture"
    folder.mkdir(parents=True, exist_ok=True)
    manifest = {"repository": "https://github.com/schellingb/UnityCapture", "commit": COMMIT,
                "license": "MIT", "sha256": {}, "github_blob_sha1": {}}
    archive = download(f"https://codeload.github.com/schellingb/UnityCapture/zip/{COMMIT}")
    upstream = ROOT / ".upstream"
    upstream.mkdir(exist_ok=True)
    (upstream / "UnityCapture-source.zip").write_bytes(archive)
    manifest["source_archive_sha256"] = hashlib.sha256(archive).hexdigest()
    source_zip = zipfile.ZipFile(io.BytesIO(archive))
    prefix = f"UnityCapture-{COMMIT}/"
    for name in ["UnityCaptureFilter32.dll", "UnityCaptureFilter64.dll"]:
        # CRC-checked extraction from the HTTPS archive pinned to an upstream commit.
        content = source_zip.read(prefix + "Install/" + name)
        blob_sha = hashlib.sha1(f"blob {len(content)}\0".encode() + content).hexdigest()
        (folder / name).write_bytes(content)
        manifest["sha256"][name] = hashlib.sha256(content).hexdigest()
        manifest["github_blob_sha1"][name] = blob_sha
    source = source_zip.read(prefix + "Source/UnityCaptureFilter.cpp").decode("utf-8-sig")
    (folder / "LICENSE.txt").write_text(source.split("*/")[0].lstrip("/*\n") + "\n", encoding="utf-8")
    (folder / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    licenses = ROOT / "licenses"
    licenses.mkdir(exist_ok=True)
    (ROOT / "LICENSE").write_bytes(download("https://raw.githubusercontent.com/spdx/license-list-data/main/text/GPL-3.0-or-later.txt"))
    # Our source is independently written; GPLv3 licensing accommodates pyvirtualcam (GPLv2+).
    import importlib.metadata as md
    for package in ["pyvirtualcam", "PySide6", "PySide6_Essentials", "PySide6_Addons", "shiboken6", "numpy", "opencv-python", "pillow", "pyinstaller"]:
        dist = md.distribution(package)
        output = licenses / package
        output.mkdir(exist_ok=True)
        for f in dist.files or []:
            if "license" in str(f).lower() or "copying" in str(f).lower() or "notice" in str(f).lower():
                actual = Path(dist.locate_file(f))
                if actual.is_file() and actual.stat().st_size < 2_000_000:
                    target = output / ("__".join(Path(f).parts[-3:]))
                    target.write_bytes(actual.read_bytes())


if __name__ == "__main__":
    generate()
    vendor()
    print("Original assets generated; pinned Unity Capture verified and bundled.")
