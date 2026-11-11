"""Named native-camera round trip. Does not activate physical cameras."""
from pathlib import Path
import json
import subprocess
import sys
import threading
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cv2
import numpy as np
from PIL import Image
from frameveil.native_camera import NativeCamera
from frameveil.driver import resources

root = Path(__file__).resolve().parents[1]
artifacts = root / 'artifacts'
artifacts.mkdir(exist_ok=True)
report = {'date':'2026-11-11', 'device':'Frameveil Camera', 'captures':[]}
pattern = np.zeros((720, 1280, 3), np.uint8)
pattern[:, :426] = [220, 45, 30]
pattern[:, 426:852] = [35, 210, 70]
pattern[:, 852:] = [40, 75, 225]
cv2.putText(pattern, 'FRAMEVEIL NATIVE CAMERA TEST', (80,360), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255,255,255), 3)
current = [pattern]
camera = NativeCamera(1280,720,30)
stop = threading.Event()
errors = []
def produce():
    try:
        while not stop.is_set():
            camera.send(current[0]); stop.wait(1/30)
    except Exception as exc:
        errors.append(str(exc))
thread = threading.Thread(target=produce)
thread.start()
try:
    time.sleep(2)
    for width,height in [(1280,720),(640,480),(1920,1080)]:
        filename = artifacts / f'native-{width}x{height}.nv12'
        result = subprocess.run([str(resources() / 'vendor/native/FrameveilCameraProbe.exe'), str(filename), str(width)],
            capture_output=True, timeout=20, creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode: raise RuntimeError(f'probe exit {result.returncode:#x}: ' + result.stdout.decode(errors='replace') + result.stderr.decode(errors='replace'))
        raw = np.fromfile(filename, np.uint8)
        if raw.size != width*height*3//2: raise RuntimeError('Unexpected frame length: ' + str(raw.size))
        rgb = cv2.cvtColor(raw.reshape(height*3//2,width), cv2.COLOR_YUV2RGB_NV12)
        Image.fromarray(rgb).save(filename.with_suffix('.png'))
        item = {'width':width,'height':height,'bytes':int(raw.size),'mean':float(rgb.mean())}
        if width == 1280:
            item['mae'] = float(np.abs(rgb.astype(float) - pattern.astype(float)).mean())
            assert item['mae'] < 8, item
        assert rgb.mean() > 10, item
        report['captures'].append(item)
    current[0] = np.zeros_like(pattern)
    time.sleep(.3)
    filename = artifacts / 'native-blackout.nv12'
    result = subprocess.run([str(resources() / 'vendor/native/FrameveilCameraProbe.exe'),str(filename),'1280'],
        capture_output=True,timeout=20,creationflags=subprocess.CREATE_NO_WINDOW)
    if result.returncode: raise RuntimeError(result.stdout.decode(errors='replace'))
    raw = np.fromfile(filename,np.uint8)
    rgb = cv2.cvtColor(raw.reshape(1080,1280),cv2.COLOR_YUV2RGB_NV12)
    Image.fromarray(rgb).save(filename.with_suffix('.png'))
    assert rgb.max() < 3, int(rgb.max())
    report['blackout_max'] = int(rgb.max())
    if errors: raise RuntimeError(str(errors))
finally:
    stop.set(); thread.join(timeout=2); camera.close()
report['passed'] = True
(artifacts/'native-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
