package app.frameveil.android.output;

import android.view.Surface;

public final class UnavailableOutput implements CameraOutput {
    public boolean isAvailable() { return false; }
    public String unavailableReason() { return "此原型仅提供本地预览，尚未实现手机微信／钉钉摄像头输出。"; }
    public Surface inputSurface() { throw new IllegalStateException(unavailableReason()); }
    public void close() { }
}
