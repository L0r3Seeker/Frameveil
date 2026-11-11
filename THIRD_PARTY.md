# Third party components

Frameveil original source: GPL-3.0-or-later. Copyright (c) 2026 Frameveil contributors.

The application is independently implemented. Research repositories do not imply endorsement or confirmed conferencing compatibility.

| Component | Upstream | License / notices |
| --- | --- | --- |
| pyvirtualcam 0.14.0 | https://github.com/letmaik/pyvirtualcam | GPL-2.0-or-later; license copied under licenses/pyvirtualcam |
| UnityCaptureFilter | https://github.com/schellingb/UnityCapture | MIT; vendor/unitycapture/LICENSE.txt, pinned commit in manifest.json |
| PySide6 / shiboken6 / Qt 6.11.1 | https://www.qt.io/qt-for-python | LGPLv3 / GPLv3 / commercial; distributed DLLs remain separate and replaceable; notices under licenses |
| OpenCV 5.0.0.93 | https://github.com/opencv/opencv-python | Apache-2.0 and bundled third-party notices, including FFmpeg, in licenses/opencv-python |
| NumPy 2.4.6 | https://numpy.org | BSD-3-Clause and bundled notices in licenses/numpy |
| Pillow 12.3.0 | https://python-pillow.github.io | HPND and bundled notices in licenses/pillow |
| Python 3.11 | https://www.python.org | PSF license, included in runtime/package notices |
| PyInstaller bootloader | https://pyinstaller.org | GPL with bootloader exception, licenses/pyinstaller |
| StillCam / VCamSample | https://github.com/qianc/stillcam-win / https://github.com/smourier/VCamSample | MIT; modified native source in native/mf_source, notices in native/third_party |
| Microsoft WIL / C++/WinRT | https://github.com/microsoft/wil / https://github.com/microsoft/cppwinrt | MIT; native/third_party and bundled native component notices |
| Gradle Wrapper 8.13 (Android development source only) | https://github.com/gradle/gradle/tree/v8.13.0 | Apache-2.0; android/Gradle-LICENSE.txt, wrapper provenance in android/gradle/wrapper/origin.json |

Unity Capture original source archive is retained in `.upstream/UnityCapture-source.zip` in the development workspace; its hash and individual DLL hashes are recorded. Runtime checks detect accidental modification relative to the bundled manifest; these hashes are local integrity records, not a publisher signature.

Qt for Python corresponding source: https://download.qt.io/official_releases/QtForPython/ . Qt source: https://download.qt.io/official_releases/qt/ . pyvirtualcam source: https://github.com/letmaik/pyvirtualcam/tree/v0.14.0 . Python license: https://docs.python.org/3/license.html .

Brand icon and demonstration artwork were generated locally by tools/prepare_assets.py. No photographs or other repositories' GUI assets are used.
