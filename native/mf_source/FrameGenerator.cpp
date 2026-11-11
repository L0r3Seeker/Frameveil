#include "pch.h"
#include "Undocumented.h"
#include "Tools.h"
#include "EnumNames.h"
#include "MFTools.h"
#include "FrameGenerator.h"

struct FrameHeader {
    UINT32 magic, version, width, height, stride, bytes;
    UINT64 tick;
    UINT32 sequence;
    BYTE reserved[28];
};
static_assert(sizeof(FrameHeader) == 64);
constexpr UINT32 FRAME_MAGIC = 0x32564d46;
constexpr SIZE_T FRAME_CAPACITY = 1920ull * 1080 * 4;

FrameGenerator::~FrameGenerator() {
    if (_view) UnmapViewOfFile(_view);
    if (_mapping) CloseHandle(_mapping);
    if (_file != INVALID_HANDLE_VALUE) CloseHandle(_file);
}

HRESULT FrameGenerator::EnsureRenderTarget(UINT width, UINT height) {
    RETURN_HR_IF(E_INVALIDARG, !width || !height || width > 1920 || height > 1080);
    _width = width; _height = height;
    _pixels.assign(static_cast<size_t>(width) * height * 4, 0);
    return S_OK;
}

bool FrameGenerator::ReadFrame(UINT& width, UINT& height) {
    if (!_view) {
        if (_file != INVALID_HANDLE_VALUE) { CloseHandle(_file); _file = INVALID_HANDLE_VALUE; }
        wil::unique_cotaskmem_string programData;
        if (FAILED(SHGetKnownFolderPath(FOLDERID_ProgramData, 0, nullptr, &programData))) return false;
        auto path = std::wstring(programData.get()) + L"\\Frameveil\\Transport\\current.frame";
        _file = CreateFileW(path.c_str(), GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE,
                            nullptr, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr);
        if (_file == INVALID_HANDLE_VALUE) return false;
        LARGE_INTEGER size;
        if (!GetFileSizeEx(_file, &size) || size.QuadPart < sizeof(FrameHeader) + FRAME_CAPACITY) return false;
        _mapping = CreateFileMappingW(_file, nullptr, PAGE_READONLY, 0, 0, nullptr);
        if (!_mapping) return false;
        _view = static_cast<const BYTE*>(MapViewOfFile(_mapping, FILE_MAP_READ, 0, 0, 0));
        if (!_view) { CloseHandle(_mapping); _mapping = nullptr; return false; }
    }
    // Bounded seqlock: never block the Windows camera service waiting for a GUI.
    for (int attempt = 0; attempt < 3; ++attempt) {
        UINT32 sequence = reinterpret_cast<const volatile FrameHeader*>(_view)->sequence;
        if (sequence & 1) continue;
        MemoryBarrier();
        FrameHeader copy;
        memcpy(&copy, _view, sizeof(copy));
        if (copy.magic != FRAME_MAGIC || copy.version != 1 || !copy.width || !copy.height ||
            copy.width > 1920 || copy.height > 1080 || copy.stride != copy.width * 4 ||
            copy.bytes != copy.width * copy.height * 4 || copy.bytes > FRAME_CAPACITY ||
            !copy.tick || GetTickCount64() - copy.tick > 2000) return false;
        _pending.resize(copy.bytes);
        memcpy(_pending.data(), _view + sizeof(FrameHeader), copy.bytes);
        MemoryBarrier();
        if (sequence == reinterpret_cast<const volatile FrameHeader*>(_view)->sequence) {
            _input.swap(_pending);
            width = copy.width; height = copy.height;
            _lastWidth = width; _lastHeight = height; _lastTick = copy.tick;
            return true;
        }
    }
    if (!_input.empty() && _lastTick && GetTickCount64() - _lastTick < 2000) {
        width = _lastWidth; height = _lastHeight;
        return true;
    }
    return false;
}

HRESULT FrameGenerator::Generate(IMFSample* sample, REFGUID format, IMFSample** outSample) {
    RETURN_HR_IF_NULL(E_POINTER, sample);
    RETURN_HR_IF_NULL(E_POINTER, outSample);
    *outSample = nullptr;
    UINT iw = 0, ih = 0;
    bool valid = ReadFrame(iw, ih);
    std::fill(_pixels.begin(), _pixels.end(), 0);
    if (valid && iw == _width && ih == _height) {
        memcpy(_pixels.data(), _input.data(), _pixels.size());
    } else if (valid) {
        double scale = (std::min)(double(_width) / iw, double(_height) / ih);
        UINT w = (std::max)(1u, UINT(iw * scale)), h = (std::max)(1u, UINT(ih * scale));
        UINT left = (_width - w) / 2, top = (_height - h) / 2;
        for (UINT y = 0; y < h; ++y) {
            UINT sy = UINT(static_cast<UINT64>(y) * ih / h);
            for (UINT x = 0; x < w; ++x) {
                UINT sx = UINT(static_cast<UINT64>(x) * iw / w);
                memcpy(&_pixels[(static_cast<size_t>(y + top) * _width + x + left) * 4],
                       &_input[(static_cast<size_t>(sy) * iw + sx) * 4], 4);
            }
        }
    }
    wil::com_ptr_nothrow<IMFMediaBuffer> buffer;
    RETURN_IF_FAILED(sample->GetBufferByIndex(0, &buffer));
    wil::com_ptr_nothrow<IMF2DBuffer2> buffer2D;
    RETURN_IF_FAILED(buffer->QueryInterface(IID_PPV_ARGS(&buffer2D)));
    BYTE *scanline = nullptr, *start = nullptr;
    LONG pitch = 0;
    DWORD length = 0;
    RETURN_IF_FAILED(buffer2D->Lock2DSize(MF2DBuffer_LockFlags_Write, &scanline, &pitch, &start, &length));
    HRESULT hr = S_OK;
    if (format == MFVideoFormat_NV12) {
        hr = RGB32ToNV12(_pixels.data(), UINT(_pixels.size()), _width * 4, _width, _height,
                         scanline, length, pitch);
    } else if (format == MFVideoFormat_RGB32 && abs(pitch) >= LONG(_width * 4)) {
        for (UINT y = 0; y < _height; ++y)
            memcpy(scanline + static_cast<ptrdiff_t>(y) * pitch, &_pixels[static_cast<size_t>(y) * _width * 4], _width * 4);
    } else hr = MF_E_INVALIDMEDIATYPE;
    buffer2D->Unlock2D();
    RETURN_IF_FAILED(hr);
    RETURN_IF_FAILED(buffer->SetCurrentLength(format == MFVideoFormat_NV12 ? _width * _height * 3 / 2 : _width * _height * 4));
    sample->AddRef(); *outSample = sample;
    return S_OK;
}
