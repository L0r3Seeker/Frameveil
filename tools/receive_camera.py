"""Development-only named DirectShow loopback check; never opens a real camera."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import imageio_ffmpeg
import numpy as np
from PIL import Image
from frameveil.engine import read_image, compose, Settings

parser = argparse.ArgumentParser()
parser.add_argument("--device", default="OBS Virtual Camera", choices=["OBS Virtual Camera", "Unity Video Capture"])
parser.add_argument("--reference")
parser.add_argument("--black", action="store_true")
parser.add_argument("--output", required=True)
args = parser.parse_args()
command = [imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-f", "dshow",
           "-video_size", "1280x720", "-framerate", "30", "-rtbufsize", "64M", "-i", "video=" + args.device,
           "-an", "-frames:v", "1", "-pix_fmt", "rgb24", "-f", "rawvideo", "pipe:1"]
result = subprocess.run(command, capture_output=True, timeout=20, creationflags=subprocess.CREATE_NO_WINDOW)
if result.returncode:
    raise RuntimeError(result.stderr.decode(errors="replace"))
rgb = np.frombuffer(result.stdout, np.uint8).reshape(720, 1280, 3)
Image.fromarray(rgb).save(args.output)
report = {"device": args.device, "shape": list(rgb.shape), "mean": float(rgb.mean()), "max": int(rgb.max())}
if args.reference:
    expected = compose(read_image(args.reference), Settings())
    report["mae_against_reference"] = float(np.abs(rgb.astype(float) - expected.astype(float)).mean())
    assert report["mae_against_reference"] < 8, report
if args.black:
    assert rgb.max() < 16, report
Path(args.output).with_suffix(".json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report))
