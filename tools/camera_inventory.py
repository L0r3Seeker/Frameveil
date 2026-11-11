"""Read-only DirectShow registration, binary architecture, and dependency inventory."""
from pathlib import Path
import json
import os
import winreg
import pefile

def binary(path):
    path = Path(os.path.expandvars(str(path).strip('"')))
    result = {"path": str(path), "exists": path.is_file()}
    if path.is_file():
        pe = pefile.PE(str(path), fast_load=True)
        pe.parse_data_directories(directories=[1])
        result.update(machine=hex(pe.FILE_HEADER.Machine), imports=[d.dll.decode() for d in getattr(pe, "DIRECTORY_ENTRY_IMPORT", [])])
        pe.close()
    return result

def inventory():
    result = {}
    for bits, flag in [(64, winreg.KEY_WOW64_64KEY), (32, winreg.KEY_WOW64_32KEY)]:
        devices = []
        category = r"SOFTWARE\Classes\CLSID\{860BB310-5D01-11D0-BD3B-00A0C911CE86}\Instance"
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, category, 0, winreg.KEY_READ | flag) as key:
                for i in range(winreg.QueryInfoKey(key)[0]):
                    name = winreg.EnumKey(key, i)
                    with winreg.OpenKey(key, name) as sub:
                        values = {winreg.EnumValue(sub, n)[0]:winreg.EnumValue(sub, n)[1] for n in range(winreg.QueryInfoKey(sub)[1])}
                    entry = {"key": name, "values": values}
                    try:
                        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, rf"SOFTWARE\Classes\CLSID\{values['CLSID']}\InprocServer32", 0, winreg.KEY_READ | flag) as com:
                            entry["binary"] = binary(winreg.QueryValueEx(com, "")[0])
                    except (KeyError, OSError):
                        pass
                    devices.append(entry)
        except OSError:
            pass
        result[str(bits)] = devices
    return result

if __name__ == "__main__":
    report = {"directshow":inventory(), "clients": [binary(p) for p in [
        r"C:\Program Files\Tencent\Weixin\Weixin.exe",
        r"C:\Program Files (x86)\DingDing\main\current_new\DingTalk.exe"]]}
    serialized = json.dumps(report, ensure_ascii=False, indent=2, default=lambda b: b.hex() if isinstance(b, bytes) else str(b))
    Path("artifacts/camera-inventory.json").write_text(serialized, encoding="utf-8")
    print(serialized)
