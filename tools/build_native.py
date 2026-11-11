"""Build the Windows 11 adapter with a locally scoped Microsoft toolchain."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
TOOLCHAIN = Path(os.environ.get('FRAMEVEIL_TOOLCHAIN', ROOT / '.build-tools/msvc'))
msvc = sorted((TOOLCHAIN / 'VC/Tools/MSVC').glob('*'))[-1]
sdk = TOOLCHAIN / 'Windows Kits/10'
sdk_version = sorted((sdk / 'Include').glob('*'))[-1].name
bin_dir = msvc / 'bin/Hostx64/x64'
include = [msvc / 'include'] + [sdk / 'Include' / sdk_version / n for n in ['ucrt', 'shared', 'um', 'winrt', 'cppwinrt']]
include += [ROOT / '.build-tools/wil/include']
libs = [msvc / 'lib/x64', sdk / 'Lib' / sdk_version / 'ucrt/x64', sdk / 'Lib' / sdk_version / 'um/x64']
env = os.environ.copy()
env['PATH'] = str(bin_dir) + os.pathsep + env['PATH']
env['INCLUDE'] = ';'.join(map(str, include))
env['LIB'] = ';'.join(map(str, libs))
build = ROOT / 'build/native'
output = ROOT / 'vendor/native'
build.mkdir(parents=True, exist_ok=True)
output.mkdir(parents=True, exist_ok=True)
base = [str(bin_dir / 'cl.exe'), '/nologo', '/O2', '/MT', '/EHsc', '/std:c++20', '/utf-8', '/DUNICODE', '/D_UNICODE', '/DNDEBUG']
source = ROOT / 'native/mf_source'
files = [str(p) for p in source.glob('*.cpp') if p.name != 'pch.cpp']
if '--probe-only' not in sys.argv:
 subprocess.run(base + ['/LD', *files, '/Fe:' + str(output / 'FrameveilMediaSource.dll'), '/link',
    '/DEF:' + str(source / 'StillCamSource.def'), 'mf.lib', 'mfplat.lib', 'mfuuid.lib', 'mfsensorgroup.lib',
    'ole32.lib', 'oleaut32.lib', 'advapi32.lib', 'user32.lib', 'shlwapi.lib', 'shell32.lib', 'uuid.lib', 'windowsapp.lib', '/NODEFAULTLIB:OLDNAMES.lib'],
    cwd=build, env=env, check=True)
 subprocess.run(base + [str(ROOT / 'native/mf_host.cpp'), '/Fe:' + str(output / 'FrameveilCameraHost.exe'), '/link', '/NODEFAULTLIB:OLDNAMES.lib'],
               cwd=build, env=env, check=True)
subprocess.run(base + [str(ROOT / 'native/mf_probe.cpp'), '/Fe:' + str(output / 'FrameveilCameraProbe.exe'), '/link', '/NODEFAULTLIB:OLDNAMES.lib'],
               cwd=build, env=env, check=True)
for name in ['StillCam-LICENSE', 'VCamSample-LICENSE']:
    shutil.copy2(ROOT / 'native/third_party' / name, output / name)
for name in ['WIL-LICENSE', 'CppWinRT-LICENSE']:
    if (ROOT / 'native/third_party' / name).exists():
        shutil.copy2(ROOT / 'native/third_party' / name, output / name)
shutil.copy2(ROOT / 'native/NOTICE.md', output / 'NOTICE.md')
manifest = {'version':'0.2.0', 'source':'native/', 'minimum_windows_build':22000,
    'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir() if p.suffix in {'.dll','.exe'}}}
(output / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print(json.dumps(manifest, indent=2))
