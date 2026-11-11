#pragma once
// Frameveil live CPU transport. No physical camera capture.
class FrameGenerator {
    UINT _width = 0, _height = 0;
    HANDLE _file = INVALID_HANDLE_VALUE, _mapping = nullptr;
    const BYTE* _view = nullptr;
    std::vector<BYTE> _input, _pending, _pixels;
    UINT _lastWidth = 0, _lastHeight = 0;
    UINT64 _lastTick = 0;
    bool ReadFrame(UINT& width, UINT& height);
public:
    FrameGenerator() = default;
    ~FrameGenerator();
    HRESULT SetD3DManager(IUnknown*, UINT, UINT) { return S_OK; }
    const bool HasD3DManager() const { return false; }
    HRESULT EnsureRenderTarget(UINT width, UINT height);
    HRESULT Generate(IMFSample* sample, REFGUID format, IMFSample** outSample);
};
