import argparse
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import os
import sys


def main():
    parser = argparse.ArgumentParser(description="帧幕 Frameveil")
    parser.add_argument("--install-driver", action="store_true")
    parser.add_argument("--uninstall-driver", action="store_true")
    parser.add_argument("--install-native-driver", action="store_true")
    parser.add_argument("--uninstall-native-driver", action="store_true")
    parser.add_argument("--screenshot")
    args = parser.parse_args()
    folder = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Frameveil"
    folder.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", handlers=[
        RotatingFileHandler(folder / "frameveil.log", maxBytes=2_000_000, backupCount=2, encoding="utf-8")])
    if args.install_driver or args.uninstall_driver or args.install_native_driver or args.uninstall_native_driver:
        from frameveil.driver import perform_install
        try:
            perform_install(args.uninstall_driver or args.uninstall_native_driver,
                            "native" if args.install_native_driver or args.uninstall_native_driver else "unitycapture")
            return 0
        except Exception:
            logging.exception("Elevated driver helper failed")
            return 1
    from frameveil.app import run
    return run(args.screenshot)


if __name__ == "__main__":
    sys.exit(main())
