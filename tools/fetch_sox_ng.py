"""Download the pinned sox_ng Windows build into ./sox (and optionally its source).

The version and SHA-256 hashes are pinned so that CI, release builds and local
development all use the exact same, verified binary.

Usage:
    python tools/fetch_sox_ng.py                   # binary into ./sox
    python tools/fetch_sox_ng.py --source dist     # also save the source tarball into dist/
"""

from __future__ import annotations

import argparse
import hashlib
import io
import os
import urllib.request
import zipfile

SOX_NG_VERSION = "14.8.1"
BASE_URL = f"https://codeberg.org/sox_ng/sox_ng/releases/download/sox_ng-{SOX_NG_VERSION}"
# Upstream published the 14.8.1 Windows build as "sox_ng-4.8.1-win64-exe.zip" (sic).
BINARY_URL = f"{BASE_URL}/sox_ng-4.8.1-win64-exe.zip"
BINARY_SHA256 = "2df0feb097ab9d61d97193bef5cabad1dc10ce8b6f1d5b4aaec8d90bd59e2e85"
SOURCE_URL = f"{BASE_URL}/sox_ng-{SOX_NG_VERSION}.tar.gz"
SOURCE_SHA256 = "1dedd9ad574abc576bbda06743867fb778accf98a1eacde1a42913acbf072448"

# Files from the Windows build that are shipped next to RED-Spectrogram.exe.
SHIPPED_FILES = ("sox_ng.exe", "COPYING", "AUTHORS", "README.md")

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def download(url: str, expected_sha256: str) -> bytes:
    print(f"Downloading {url}")
    with urllib.request.urlopen(url, timeout=120) as response:
        data = response.read()
    digest = hashlib.sha256(data).hexdigest()
    if digest != expected_sha256:
        raise SystemExit(f"SHA-256 mismatch for {url}\n  expected {expected_sha256}\n  got      {digest}")
    return data


def fetch_binary(dest_dir: str) -> None:
    data = download(BINARY_URL, BINARY_SHA256)
    os.makedirs(dest_dir, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for name in SHIPPED_FILES:
            with archive.open(name) as src, open(os.path.join(dest_dir, name), "wb") as dst:
                dst.write(src.read())
    print(f"sox_ng {SOX_NG_VERSION} extracted to {dest_dir}")


def fetch_source(dest_dir: str) -> None:
    data = download(SOURCE_URL, SOURCE_SHA256)
    os.makedirs(dest_dir, exist_ok=True)
    path = os.path.join(dest_dir, f"sox_ng-{SOX_NG_VERSION}-source.tar.gz")
    with open(path, "wb") as f:
        f.write(data)
    print(f"Source saved to {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dest", default=os.path.join(REPO_ROOT, "sox"), help="where to extract the binary (default: ./sox)")
    parser.add_argument("--source", metavar="DIR", help="also download the source tarball into DIR")
    args = parser.parse_args()

    fetch_binary(args.dest)
    if args.source:
        fetch_source(args.source)


if __name__ == "__main__":
    main()
