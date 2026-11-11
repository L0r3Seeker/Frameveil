Frameveil Media Foundation source derives from qianc/stillcam-win v1.1.0 (MIT),
whose source derives from smourier/VCamSample at
ae42a88dce8e9a631998a54d36b8ad17fe2bfb1a (MIT, Simon Mourier).
Original license notices are preserved under third_party.

Frameveil modifications: new CLSID; live bounded BGRA frame transport; no image
file polling or D2D requirement; 720p/480p/1080p NV12 and RGB32 negotiation;
fixed stream-state comparison and null-type restart; per-session host lifecycle.
These modifications are licensed GPL-3.0-or-later with the application.

The source uses Microsoft WIL (MIT) and Windows SDK C++/WinRT (MIT).
Build toolchain files are development dependencies and are not redistributed.
