"""Explicit, reversible installation of the bundled upstream DirectShow filter."""
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import winreg

UNITY_CLSID = "{5C2CD55C-92AD-4999-8666-912BD3E70010}"
OBS_CLSID = "{A3FCE0F5-3493-419F-958A-ABA1250EC20B}"


def resources():
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))


def registered_cameras():
    result = []
    keypath = r"SOFTWARE\Classes\CLSID\{860BB310-5D01-11D0-BD3B-00A0C911CE86}\Instance"
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, keypath, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
            for i in range(winreg.QueryInfoKey(key)[0]):
                with winreg.OpenKey(key, winreg.EnumKey(key, i)) as sub:
                    try:
                        result.append(winreg.QueryValueEx(sub, "FriendlyName")[0])
                    except OSError:
                        pass
    except OSError:
        pass
    return result


def install_directory():
    return Path(os.environ.get("ProgramData", r"C:\ProgramData")) / "Frameveil" / "Camera"


def verify_bundle():
    folder = resources() / "vendor" / "unitycapture"
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    for name, expected in manifest["sha256"].items():
        if hashlib.sha256((folder / name).read_bytes()).hexdigest() != expected:
            raise RuntimeError("摄像头组件校验失败：" + name)
    return folder, manifest


def perform_install(uninstall=False, backend="unitycapture"):
    """Only called by the explicitly elevated helper; never at normal launch."""
    if backend == "native":
        return perform_native_install(uninstall)
    folder, manifest = verify_bundle()
    target = install_directory()
    if uninstall:
        if not (target / "frameveil-owned.json").exists():
            raise RuntimeError("没有由帧幕安装的组件；不会更改其他软件的设备")
        # Refuse to unregister an independently reinstalled Unity Capture.
        for bits, clsid in ((64, UNITY_CLSID), (32, "{5C2CD55C-92AD-4999-8666-912BD3E70020}")):
            flag = winreg.KEY_WOW64_64KEY if bits == 64 else winreg.KEY_WOW64_32KEY
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, rf"SOFTWARE\Classes\CLSID\{clsid}\InprocServer32", 0, winreg.KEY_READ | flag) as key:
                    active = Path(winreg.QueryValueEx(key, "")[0]).resolve()
                if active != (target / f"UnityCaptureFilter{bits}.dll").resolve():
                    raise RuntimeError("组件由其他软件管理，已取消卸载")
            except FileNotFoundError:
                pass
    else:
        if "Unity Video Capture" in registered_cameras():
            # Reuse existing installation; do not take ownership.
            return
        target.mkdir(parents=True, exist_ok=True)
        for name in manifest["sha256"]:
            shutil.copy2(folder / name, target / name)
    completed = []
    try:
        for bits, system_folder in ((64, "System32"), (32, "SysWOW64")):
            tool = Path(os.environ["WINDIR"]) / system_folder / "regsvr32.exe"
            dll = target / f"UnityCaptureFilter{bits}.dll"
            args = [str(tool), "/s"] + (["/u"] if uninstall else []) + [str(dll)]
            subprocess.run(args, check=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=45)
            completed.append((tool, dll))
    except Exception:
        if not uninstall:
            for tool, dll in reversed(completed):
                subprocess.run([str(tool), "/s", "/u", str(dll)], creationflags=subprocess.CREATE_NO_WINDOW, timeout=45)
        raise
    if not uninstall:
        if "Unity Video Capture" not in registered_cameras():
            raise RuntimeError("注册后未找到设备，请查看日志")
        (target / "frameveil-owned.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    else:
        # Leave DLLs in place in case a meeting client still has them loaded.
        (target / "frameveil-owned.json").unlink(missing_ok=True)


def perform_native_install(uninstall=False):
    from .native_camera import NATIVE_CLSID, CAPACITY, HEADER_SIZE, transport_path, supported
    if not supported():
        raise RuntimeError("Windows 原生摄像头需要 Windows 11 build 22000 或更新")
    folder = resources() / "vendor" / "native"
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    for name, digest in manifest["sha256"].items():
        if hashlib.sha256((folder / name).read_bytes()).hexdigest() != digest:
            raise RuntimeError("原生摄像头组件校验失败：" + name)
    base = install_directory().parent / "Native"
    ownership = base / "frameveil-native-owned.json"
    target = base / manifest["sha256"]["FrameveilMediaSource.dll"][:12]
    tool = Path(os.environ["WINDIR"]) / "System32" / "regsvr32.exe"
    if uninstall:
        if not ownership.exists():
            raise RuntimeError("没有由帧幕管理的原生组件")
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, rf"SOFTWARE\Classes\CLSID\{NATIVE_CLSID}\InprocServer32", 0,
                            winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
            active = Path(winreg.QueryValueEx(key, "")[0]).resolve()
        if not active.is_relative_to(base.resolve()):
            raise RuntimeError("当前组件由其他程序管理，已取消卸载")
        subprocess.run([str(tool), "/s", "/u", str(active)], check=True,
                       creationflags=subprocess.CREATE_NO_WINDOW, timeout=45)
        ownership.unlink(missing_ok=True)
        return
    target.mkdir(parents=True, exist_ok=True)
    dll = target / "FrameveilMediaSource.dll"
    if not dll.exists():
        shutil.copy2(folder / dll.name, dll)
    transport = transport_path()
    transport.parent.mkdir(parents=True, exist_ok=True)
    if not transport.exists():
        with transport.open("wb") as f:
            f.truncate(HEADER_SIZE + CAPACITY)
    # Grant write access only to the application's one frame buffer, not its COM binaries.
    subprocess.run(["icacls.exe", str(transport), "/grant", "*S-1-5-32-545:(R,W)"],
                   check=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=15)
    subprocess.run([str(tool), "/s", str(dll)], check=True,
                   creationflags=subprocess.CREATE_NO_WINDOW, timeout=45)
    ownership.write_text(json.dumps({"dll": str(dll), **manifest}, indent=2), encoding="utf-8")


def elevate_helper(uninstall=False, backend="unitycapture"):
    class SHELLEXECUTEINFOW(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.DWORD), ("fMask", wintypes.ULONG), ("hwnd", wintypes.HWND),
                    ("lpVerb", wintypes.LPCWSTR), ("lpFile", wintypes.LPCWSTR), ("lpParameters", wintypes.LPCWSTR),
                    ("lpDirectory", wintypes.LPCWSTR), ("nShow", ctypes.c_int), ("hInstApp", wintypes.HINSTANCE),
                    ("lpIDList", ctypes.c_void_p), ("lpClass", wintypes.LPCWSTR), ("hkeyClass", wintypes.HKEY),
                    ("dwHotKey", wintypes.DWORD), ("hIcon", wintypes.HANDLE), ("hProcess", wintypes.HANDLE)]
    args = [] if getattr(sys, "frozen", False) else [str(resources() / "main.py")]
    if backend == "native":
        args.append("--uninstall-native-driver" if uninstall else "--install-native-driver")
    else:
        args.append("--uninstall-driver" if uninstall else "--install-driver")
    info = SHELLEXECUTEINFOW()
    info.cbSize = ctypes.sizeof(info)
    info.fMask = 0x40  # SEE_MASK_NOCLOSEPROCESS
    info.lpVerb, info.lpFile = "runas", sys.executable
    info.lpParameters = subprocess.list2cmdline(args)
    info.lpDirectory, info.nShow = str(resources()), 0
    shell = ctypes.WinDLL("shell32", use_last_error=True)
    shell.ShellExecuteExW.argtypes = [ctypes.POINTER(SHELLEXECUTEINFOW)]
    if not shell.ShellExecuteExW(ctypes.byref(info)):
        code = ctypes.get_last_error()
        raise RuntimeError("已取消管理员授权" if code == 1223 else f"无法启动组件安装：Windows {code}")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    try:
        kernel.WaitForSingleObject(info.hProcess, 0xFFFFFFFF)
        code = wintypes.DWORD()
        kernel.GetExitCodeProcess(info.hProcess, ctypes.byref(code))
        if code.value:
            raise RuntimeError(f"组件操作未完成（{code.value}），请查看日志后重试")
    finally:
        kernel.CloseHandle(info.hProcess)
