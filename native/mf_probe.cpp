#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <mfapi.h>
#include <mfidl.h>
#include <mfreadwrite.h>
#include <wrl/client.h>
#include <cstdio>
#include <string>
#include <vector>
using Microsoft::WRL::ComPtr;
#pragma comment(lib, "mf")
#pragma comment(lib, "mfplat")
#pragma comment(lib, "mfreadwrite")
#pragma comment(lib, "mfuuid")
#pragma comment(lib, "ole32")

int wmain(int argc, wchar_t** argv) {
    CoInitializeEx(nullptr, COINIT_MULTITHREADED);
    MFStartup(MF_VERSION);
    ComPtr<IMFAttributes> attributes;
    MFCreateAttributes(&attributes, 1);
    attributes->SetGUID(MF_DEVSOURCE_ATTRIBUTE_SOURCE_TYPE, MF_DEVSOURCE_ATTRIBUTE_SOURCE_TYPE_VIDCAP_GUID);
    IMFActivate** devices = nullptr; UINT32 count = 0;
    HRESULT hr = MFEnumDeviceSources(attributes.Get(), &devices, &count);
    if (FAILED(hr)) { fprintf(stderr,"ERROR MFEnumDeviceSources %08X\n", unsigned(hr)); return 2; }
    ComPtr<IMFActivate> selected;
    for (UINT32 i = 0; i < count; ++i) {
        WCHAR* name = nullptr; UINT32 size = 0;
        if (SUCCEEDED(devices[i]->GetAllocatedString(MF_DEVSOURCE_ATTRIBUTE_FRIENDLY_NAME, &name, &size))) {
            wprintf(L"DEVICE %s\n", name);
            if (wcsstr(name, L"Frameveil Camera") != nullptr) selected = devices[i];
            CoTaskMemFree(name);
        }
        devices[i]->Release();
    }
    CoTaskMemFree(devices);
    if (argc < 2) return 0;
    // Only capture our own virtual camera; never fall back to physical devices.
    if (!selected) { fprintf(stderr,"ERROR Frameveil camera not enumerated\n"); return 3; }
    ComPtr<IMFMediaSource> source;
    hr = selected->ActivateObject(IID_PPV_ARGS(&source));
    if (FAILED(hr)) { fprintf(stderr,"ERROR ActivateObject %08X\n", unsigned(hr)); return 4; }
    ComPtr<IMFSourceReader> reader;
    hr = MFCreateSourceReaderFromMediaSource(source.Get(), nullptr, &reader);
    if (FAILED(hr)) { fprintf(stderr,"ERROR SourceReader %08X\n", unsigned(hr)); return 5; }
    UINT32 width = argc > 2 ? _wtoi(argv[2]) : 1280;
    UINT32 height = width == 640 ? 480 : (width == 1920 ? 1080 : 720);
    ComPtr<IMFMediaType> type;
    MFCreateMediaType(&type);
    type->SetGUID(MF_MT_MAJOR_TYPE, MFMediaType_Video);
    type->SetGUID(MF_MT_SUBTYPE, MFVideoFormat_NV12);
    MFSetAttributeSize(type.Get(), MF_MT_FRAME_SIZE, width, height);
    MFSetAttributeRatio(type.Get(), MF_MT_FRAME_RATE, 30, 1);
    hr = reader->SetCurrentMediaType(MF_SOURCE_READER_FIRST_VIDEO_STREAM, nullptr, type.Get());
    if (FAILED(hr)) { fprintf(stderr,"ERROR SetMediaType %08X\n", unsigned(hr)); return 6; }
    ComPtr<IMFSample> sample;
    DWORD flags = 0, stream = 0; LONGLONG timestamp = 0;
    for (int i = 0; i < 10; ++i) {
        sample.Reset();
        hr = reader->ReadSample(MF_SOURCE_READER_FIRST_VIDEO_STREAM, 0, &stream, &flags, &timestamp, &sample);
        if (FAILED(hr)) { fprintf(stderr,"ERROR ReadSample %08X\n", unsigned(hr)); return 7; }
        if (sample) break;
    }
    if (!sample) return 8;
    ComPtr<IMFMediaBuffer> buffer;
    sample->ConvertToContiguousBuffer(&buffer);
    BYTE* data = nullptr; DWORD length = 0;
    buffer->Lock(&data, nullptr, &length);
    FILE* output = nullptr;
    _wfopen_s(&output, argv[1], L"wb");
    if (!output) { buffer->Unlock(); return 9; }
    fwrite(data, 1, length, output); fclose(output); buffer->Unlock();
    wprintf(L"CAPTURE %u %u %lu %lld\n", width, height, length, timestamp);
    // Samples/buffers and proxy objects must be released while MF and COM are
    // still initialized. The SourceReader owns media-source shutdown.
    buffer.Reset(); sample.Reset(); type.Reset();
    reader->Flush(MF_SOURCE_READER_FIRST_VIDEO_STREAM);
    reader.Reset(); source.Reset(); selected.Reset(); attributes.Reset();
    MFShutdown(); CoUninitialize();
    return 0;
}
