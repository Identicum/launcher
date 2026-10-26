#!/usr/bin/env python3
"""Download the bundled front-end libraries into launcher/static/vendor.

The image serves them itself (no CDN), so the launcher works on isolated networks.
To upgrade, change the versions below, run `python3 scripts/update_vendor.py` and commit the result.
"""

import io
import json
import shutil
import tarfile
import urllib.request
from pathlib import Path

BOOTSTRAP = "5.3.8"
FONTAWESOME = "7.3.1"

VENDOR = Path(__file__).resolve().parent.parent / "launcher" / "static" / "vendor"
STYLE_CODES = {"solid": "s", "regular": "r", "brands": "b"}


def npm_package(name: str, version: str) -> tarfile.TarFile:
    url = f"https://registry.npmjs.org/{name}/-/{name.split('/')[-1]}-{version}.tgz"
    print(f"Downloading {url}")
    with urllib.request.urlopen(url) as response:
        return tarfile.open(fileobj=io.BytesIO(response.read()), mode="r:gz")


def extract(package: tarfile.TarFile, member: str, destination: Path) -> bytes:
    data = package.extractfile(f"package/{member}").read()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    return data


def icon_index(metadata: bytes) -> list:
    """[[name, styles, search text]] for the free icons, e.g. ["cloud", "s", "Cloud atmosphere fog ..."]."""
    icons = []
    for name, icon in json.loads(metadata).items():
        styles = "".join(STYLE_CODES[s["style"]] for s in icon["familyStylesByLicense"]["free"] if s["family"] == "classic")
        if styles:
            icons.append([name, styles, " ".join([icon["label"], *icon["search"]["terms"]])])
    return sorted(icons)


def main() -> None:
    shutil.rmtree(VENDOR, ignore_errors=True)

    bootstrap = npm_package("bootstrap", BOOTSTRAP)
    for member in ("dist/css/bootstrap.min.css", "dist/js/bootstrap.bundle.min.js"):
        extract(bootstrap, member, VENDOR / "bootstrap" / Path(member).name)

    fontawesome = npm_package("@fortawesome/fontawesome-free", FONTAWESOME)
    extract(fontawesome, "css/all.min.css", VENDOR / "fontawesome" / "css" / "all.min.css")
    extract(fontawesome, "LICENSE.txt", VENDOR / "fontawesome" / "LICENSE.txt")
    for member in fontawesome.getnames():
        if member.startswith("package/webfonts/") and member.endswith(".woff2"):
            extract(fontawesome, member.removeprefix("package/"), VENDOR / "fontawesome" / member.removeprefix("package/"))
    metadata = fontawesome.extractfile("package/metadata/icon-families.json").read()
    icons = icon_index(metadata)
    (VENDOR / "fontawesome" / "icons.json").write_text(json.dumps(icons, separators=(",", ":")))

    (VENDOR / "VERSIONS").write_text(f"bootstrap {BOOTSTRAP}\n@fortawesome/fontawesome-free {FONTAWESOME}\n")
    print(f"Done: {len(icons)} free icons indexed")


if __name__ == "__main__":
    main()
