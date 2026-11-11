"""Use the Qt-shipped matching MSVC runtime for the entire portable process."""
from pathlib import Path
import shutil
import sys
import PySide6

ROOT = Path(__file__).resolve().parent.parent
target = ROOT / "dist" / "Frameveil" / "_internal"
qt = Path(PySide6.__file__).parent
for name in ["vcruntime140.dll", "vcruntime140_1.dll", "msvcp140.dll", "msvcp140_1.dll", "msvcp140_2.dll", "concrt140.dll", "msvcp140_codecvt_ids.dll"]:
    shutil.copy2(qt / name, target / name)
# PyInstaller can resolve Qt's Windows ICU shim to an unrelated Poppler ICU
# on the build machine's PATH. Qt uses the ICU API shipped with Windows.
# Do not redistribute that unrelated DLL or shadow Windows' implementation.
for name in ["icuuc.dll", "icudt78.dll"]:
    (target / name).unlink(missing_ok=True)
python_license = Path(sys.base_prefix) / "LICENSE.txt"
if python_license.exists():
    shutil.copy2(python_license, target / "licenses" / "Python-LICENSE.txt")
print("Bundled matching Qt MSVC runtime and Python notices.")
