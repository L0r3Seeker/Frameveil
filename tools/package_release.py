from pathlib import Path
import hashlib
import json
import zipfile
import sys

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))
from frameveil import __version__
release = root / "release"
release.mkdir(exist_ok=True)
sources = [root / f for f in ["main.py", "README.md", "VALIDATION.md", "COMPATIBILITY.md", "THIRD_PARTY.md", "LICENSE", "requirements.txt", "build.ps1", ".gitignore"]]
for folder in ["frameveil", "tools", "tests", "assets", "vendor", "licenses", "native", "delivery", "android", "publishing"]:
    sources += [f for f in (root / folder).rglob("*") if f.is_file()
                and not any(part in {"__pycache__", ".gradle", ".idea", "build"} for part in f.relative_to(root / folder).parts)
                and f.name not in {"local.properties", "keystore.properties"}
                and f.suffix not in {".jks", ".keystore"}]
source_zip = release / f"Frameveil-{__version__}-source.zip"
with zipfile.ZipFile(source_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as out:
    for path in sources:
        out.write(path, "Frameveil-source/" + path.relative_to(root).as_posix())
portable = release / f"Frameveil-{__version__}-Windows-x64.zip"
with zipfile.ZipFile(portable, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as out:
    for path in (root / "dist" / "Frameveil").rglob("*"):
        if path.is_file():
            out.write(path, "Frameveil/" + path.relative_to(root / "dist" / "Frameveil").as_posix())
    for path in (root / "delivery").iterdir():
        if path.is_file():
            out.write(path, "Frameveil/" + path.name)
    out.write(root / "LICENSE", "Frameveil/LICENSE")
    out.write(source_zip, "Frameveil/" + source_zip.name)
report = {path.name: {"bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
          for path in [portable, source_zip, root / "dist" / "Frameveil" / "Frameveil.exe"]}
(release / "SHA256.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
