#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <mfapi.h>
#include <mfidl.h>
#include <mfvirtualcamera.h>
#include <wrl/client.h>
#include <cstdio>
using Microsoft::WRL::ComPtr;
#pragma comment(lib, "mfplat")
#pragma comment(lib, "mfsensorgroup")
#pragma comment(lib, "ole32")

int wmain() {
    CoInitializeEx(nullptr, COINIT_MULTITHREADED);
    HRESULT hr = MFStartup(MF_VERSION);
    if (FAILED(hr)) { printf("ERROR MFStartup %08X\n", unsigned(hr)); return 2; }
    ComPtr<IMFVirtualCamera> camera;
    hr = MFCreateVirtualCamera(MFVirtualCameraType_SoftwareCameraSource, MFVirtualCameraLifetime_Session,
        MFVirtualCameraAccess_CurrentUser, L"Frameveil Camera", L"{184FBC72-6B4D-41FB-9421-5976DAB0C222}",
        nullptr, 0, &camera);
    if (SUCCEEDED(hr)) hr = camera->Start(nullptr);
    if (FAILED(hr)) { printf("ERROR NativeCamera %08X\n", unsigned(hr)); fflush(stdout); return 3; }
    printf("READY Frameveil Camera\n"); fflush(stdout);
    getchar();
    camera->Stop(); camera->Shutdown(); camera.Reset();
    MFShutdown(); CoUninitialize();
    return 0;
}
