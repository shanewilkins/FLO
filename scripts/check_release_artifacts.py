#!/usr/bin/env python3
"""Validate release tags, distribution identity, and bundled ELK assets."""

from __future__ import annotations

import argparse
import re
import tarfile
import tomllib
import zipfile
from email.parser import BytesParser
from pathlib import Path, PurePosixPath

REPO_ROOT = Path(__file__).resolve().parents[1]
VENDOR_FILES = (
    "flo/render/layout_core/vendor/elk.bundled.js",
    "flo/render/layout_core/vendor/ELKJS_LICENSE.md",
)


def check_release_tag(tag: str, version: str) -> None:
    """Require an exact package version, optionally prefixed with lowercase v."""
    if tag not in {version, f"v{version}"}:
        raise ValueError(
            f"Release tag {tag!r} does not match project version {version!r}."
        )


def _check_metadata(data: bytes, version: str) -> None:
    metadata = BytesParser().parsebytes(data)
    name = re.sub(r"[-_.]+", "-", metadata.get("Name", "")).lower()
    if name != "flo-lang" or metadata.get("Version") != version:
        raise ValueError(
            f"Distribution identity must be flo-lang {version}; "
            f"got {metadata.get('Name')!r} {metadata.get('Version')!r}."
        )


def _check_assets(assets: dict[str, bytes]) -> None:
    for name, content in assets.items():
        if not content:
            raise ValueError(f"Bundled ELK asset is empty: {name}")


def _read_tar_file(archive: tarfile.TarFile, name: str) -> bytes:
    if not archive.getmember(name).isfile():
        raise ValueError(f"Distribution member must be a regular file: {name}")
    stream = archive.extractfile(name)
    if stream is None:
        raise ValueError(f"Cannot read distribution member: {name}")
    with stream:
        return stream.read()


def check_archive(path: Path, version: str) -> None:
    """Check metadata and nonempty ELK bundle/license in a wheel or sdist."""
    if path.name.endswith(".whl"):
        with zipfile.ZipFile(path) as archive:
            metadata_names = [
                name
                for name in archive.namelist()
                if name.endswith(".dist-info/METADATA")
            ]
            if len(metadata_names) != 1:
                raise ValueError(f"{path}: expected exactly one wheel METADATA file.")
            _check_metadata(archive.read(metadata_names[0]), version)
            _check_assets({name: archive.read(name) for name in VENDOR_FILES})
    elif path.name.endswith(".tar.gz"):
        with tarfile.open(path, "r:gz") as archive:
            roots = {
                PurePosixPath(member.name).parts[0]
                for member in archive.getmembers()
                if member.isfile()
            }
            if len(roots) != 1:
                raise ValueError(f"{path}: expected exactly one sdist root directory.")
            root = roots.pop()
            _check_metadata(_read_tar_file(archive, f"{root}/PKG-INFO"), version)
            _check_assets(
                {
                    name: _read_tar_file(archive, f"{root}/src/{name}")
                    for name in VENDOR_FILES
                }
            )
    else:
        raise ValueError(f"Unsupported distribution archive: {path}")


def main() -> int:
    """Check supplied archives and/or a release tag against project metadata."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archives", nargs="*", type=Path)
    parser.add_argument("--tag")
    args = parser.parse_args()
    if not args.archives and args.tag is None:
        parser.error("provide distribution archives and/or --tag")
    version = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))[
        "project"
    ]["version"]
    try:
        if args.tag is not None:
            check_release_tag(args.tag, version)
            print(f"Release tag matches flo-lang {version}.")
        for path in args.archives:
            check_archive(path, version)
            print(f"Validated {path}: flo-lang {version} and bundled ELK assets.")
    except (ValueError, KeyError, OSError, tarfile.TarError, zipfile.BadZipFile) as exc:
        parser.exit(1, f"Release validation failed: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
