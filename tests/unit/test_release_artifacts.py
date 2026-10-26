"""Distribution acceptance rejects version drift and incomplete ELK bundles."""

import importlib.util
import io
import re
import sys
import tarfile
import zipfile
from pathlib import Path

import pytest

_SCRIPT_PATH = Path("scripts/check_release_artifacts.py")
_SPEC = importlib.util.spec_from_file_location("check_release_artifacts", _SCRIPT_PATH)
assert _SPEC is not None
assert _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)


def _write_archive(
    tmp_path, kind, *, version="0.4.3", name="flo-lang", missing=None, empty=None
):
    metadata = f"Metadata-Version: 2.4\nName: {name}\nVersion: {version}\n".encode()
    files = {"metadata": metadata}
    files.update(dict.fromkeys(_MODULE.VENDOR_FILES, b"ELK asset fixture"))
    if missing is not None:
        del files[missing]
    if empty is not None:
        files[empty] = b""
    root = f"flo_lang-{version}"
    if kind == "wheel":
        path = tmp_path / f"{root}-py3-none-any.whl"
        with zipfile.ZipFile(path, "w") as archive:
            for member, content in files.items():
                target = (
                    f"{root}.dist-info/METADATA" if member == "metadata" else member
                )
                archive.writestr(target, content)
    else:
        path = tmp_path / f"{root}.tar.gz"
        with tarfile.open(path, "w:gz") as archive:
            for member, content in files.items():
                suffix = "PKG-INFO" if member == "metadata" else f"src/{member}"
                info = tarfile.TarInfo(f"{root}/{suffix}")
                info.size = len(content)
                archive.addfile(info, io.BytesIO(content))
    return path


@pytest.mark.parametrize("tag", ["0.4.3", "v0.4.3"])
def test_release_tag_accepts_only_the_declared_version(tag):
    _MODULE.check_release_tag(tag, "0.4.3")


@pytest.mark.parametrize("tag", ["", "v0.4.4", "release/0.4.3", "v0.4.3\n"])
def test_release_tag_rejects_mismatches(tag):
    with pytest.raises(ValueError, match="does not match project version"):
        _MODULE.check_release_tag(tag, "0.4.3")


@pytest.mark.parametrize("kind", ["wheel", "sdist"])
def test_distribution_accepts_matching_identity_and_bundled_assets(tmp_path, kind):
    _MODULE.check_archive(_write_archive(tmp_path, kind), "0.4.3")


@pytest.mark.parametrize("kind", ["wheel", "sdist"])
@pytest.mark.parametrize("overrides", [{"version": "0.4.4"}, {"name": "other-package"}])
def test_distribution_rejects_wrong_identity(tmp_path, kind, overrides):
    path = _write_archive(tmp_path, kind, **overrides)

    with pytest.raises(ValueError, match="Distribution identity must be"):
        _MODULE.check_archive(path, "0.4.3")


@pytest.mark.parametrize("kind", ["wheel", "sdist"])
@pytest.mark.parametrize("asset", _MODULE.VENDOR_FILES)
def test_distribution_requires_both_elk_bundle_and_license(tmp_path, kind, asset):
    path = _write_archive(tmp_path, kind, missing=asset)

    with pytest.raises(KeyError, match=re.escape(asset)):
        _MODULE.check_archive(path, "0.4.3")


@pytest.mark.parametrize("kind", ["wheel", "sdist"])
@pytest.mark.parametrize("asset", _MODULE.VENDOR_FILES)
def test_distribution_rejects_empty_elk_assets(tmp_path, kind, asset):
    path = _write_archive(tmp_path, kind, empty=asset)

    with pytest.raises(ValueError, match="Bundled ELK asset is empty"):
        _MODULE.check_archive(path, "0.4.3")


def test_distribution_rejects_unsupported_archive_types(tmp_path):
    with pytest.raises(ValueError, match="Unsupported distribution archive"):
        _MODULE.check_archive(tmp_path / "candidate.zip", "0.4.3")


def test_release_cli_reports_tag_mismatch_and_exits_nonzero(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", [str(_SCRIPT_PATH), "--tag", "not-a-release"])

    with pytest.raises(SystemExit) as error:
        _MODULE.main()

    assert error.value.code == 1
    assert "does not match project version" in capsys.readouterr().err


def test_release_cli_requires_an_archive_or_tag(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", [str(_SCRIPT_PATH)])

    with pytest.raises(SystemExit) as error:
        _MODULE.main()

    assert error.value.code == 2
    assert "provide distribution archives and/or --tag" in capsys.readouterr().err
