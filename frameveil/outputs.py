"""Output-adapter boundary for future platform ports; no GUI imports."""
import logging


def open_camera(settings):
    from .native_camera import NativeCamera, registered
    backend = settings.backend
    if backend == "native" or (backend == "auto" and registered()):
        # Do not silently change a failed native selection into another device.
        return NativeCamera(settings.width, settings.height, settings.fps)
    import pyvirtualcam
    camera = pyvirtualcam.Camera(settings.width, settings.height, settings.fps,
        backend=None if backend == "auto" else backend, fmt=pyvirtualcam.PixelFormat.RGB)
    logging.info("DirectShow sender opened: backend=%s device=%s %sx%s@%s",
                 camera.backend, camera.device, settings.width, settings.height, settings.fps)
    return camera
