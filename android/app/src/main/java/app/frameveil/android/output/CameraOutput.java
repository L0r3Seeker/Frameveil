package app.frameveil.android.output;

import android.view.Surface;

/** Future system/HAL implementation attaches its producer Surface here. */
public interface CameraOutput extends AutoCloseable {
    boolean isAvailable();
    String unavailableReason();
    Surface inputSurface();
    @Override void close();
}
