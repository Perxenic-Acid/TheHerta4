#!/usr/bin/env python3
"""Build an installable Blender add-on ZIP with release-matched bl_info.

The repository is left untouched: only the __init__.py stored in the ZIP has
its version tuple replaced. The Blender updater downloads Release assets.
"""
from __future__ import annotations

import hashlib
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERSION_RE = re.compile(r"^v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
INFO_RE = re.compile(
    rb'(?m)^(\s*"version"\s*:\s*)\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\)(\s*,)'
)
SKIP_FILES = {
    ".gitignore",
    "README_DEV.md",
    "Soul.md",
    "requirements.txt",
}
SKIP_DIRECTORIES = (".github/", "docs/", "tools/")


def release_files() -> list[Path]:
    tracked = subprocess.check_output(
        ["git", "-C", str(ROOT), "ls-files", "-z"]
    ).split(b"\0")
    paths: list[Path] = []
    for raw in tracked:
        if not raw:
            continue
        name = raw.decode("utf-8")
        if name in SKIP_FILES or name.startswith(SKIP_DIRECTORIES):
            continue
        path = ROOT / name
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"Invalid tracked release file: {name}")
        paths.append(Path(name))

    if Path("__init__.py") not in paths:
        raise RuntimeError("Missing Blender add-on entrypoint __init__.py")
    if Path("addon_updater_ops.py") not in paths:
        raise RuntimeError("Missing Blender add-on updater")
    return sorted(paths)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: build_release.py vMAJOR.MINOR.PATCH")
    tag = sys.argv[1]
    match = VERSION_RE.fullmatch(tag)
    if not match:
        raise SystemExit(f"Invalid release version: {tag}")
    version = ", ".join(str(int(value)) for value in match.groups())

    dest = ROOT / "dist"
    dest.mkdir(exist_ok=True)
    archive = dest / f"TheHerta4-{tag}.zip"
    files = release_files()
    with zipfile.ZipFile(
        archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=8
    ) as result:
        for path in files:
            payload = (ROOT / path).read_bytes()
            if path == Path("__init__.py"):
                payload, count = INFO_RE.subn(
                    lambda m: m.group(1) + f"({version})".encode() + m.group(2),
                    payload,
                )
                if count != 1:
                    raise RuntimeError(
                        f"Expected one bl_info version tuple; found {count}"
                    )
            result.writestr(f"TheHerta4/{path.as_posix()}", payload)

    with zipfile.ZipFile(archive, "r") as result:
        if result.testzip() is not None:
            raise RuntimeError("ZIP integrity validation failed")
        entry = result.read("TheHerta4/__init__.py").decode("utf-8")
        if f'"version": ({version})' not in entry:
            raise RuntimeError("Packaged bl_info version mismatch")
        if not any(name.startswith("TheHerta4/resources/") for name in result.namelist()):
            raise RuntimeError("Resource directory is missing from ZIP")
        print(f"Validated {len(result.namelist())} files, bl_info={tag}")

    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    (dest / "SHA256SUMS.txt").write_text(
        f"{checksum}  {archive.name}\n", encoding="utf-8"
    )
    print(f"Created {archive.relative_to(ROOT)} ({archive.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
