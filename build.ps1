$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (!(Test-Path -LiteralPath 'vendor/native/manifest.json')) { throw 'Build native adapter first: python tools/build_native.py' }
python -m PyInstaller --noconfirm --clean --windowed --onedir --name Frameveil --icon assets/frameveil.ico --add-data 'assets;assets' --add-data 'vendor;vendor' --add-data 'licenses;licenses' --add-data 'LICENSE;.' --hidden-import pyvirtualcam._native_windows_obs --hidden-import pyvirtualcam._native_windows_unity_capture --exclude-module PySide6.QtWebEngineCore --exclude-module PySide6.QtWebEngineWidgets --exclude-module PySide6.QtQml --exclude-module PySide6.QtQuick --exclude-module matplotlib --exclude-module tkinter main.py
if ($LASTEXITCODE -ne 0) { throw 'Build failed' }
python tools/finalize_bundle.py
if ($LASTEXITCODE -ne 0) { throw 'Runtime finalization failed' }
Copy-Item -LiteralPath README.md -Destination dist/Frameveil/使用说明.md
Copy-Item -LiteralPath THIRD_PARTY.md -Destination dist/Frameveil/THIRD_PARTY.md
Copy-Item -LiteralPath VALIDATION.md -Destination dist/Frameveil/本地验证记录.md
Copy-Item -LiteralPath COMPATIBILITY.md -Destination dist/Frameveil/兼容性与系统要求.md
Write-Output 'Ready: dist/Frameveil/Frameveil.exe'
