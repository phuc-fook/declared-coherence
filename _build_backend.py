"""Small deterministic PEP 517 backend for this stdlib-only pure-Python package."""

from __future__ import annotations

import base64
import gzip
import hashlib
import io
from pathlib import Path
import tarfile
import zipfile

NAME = "declared_coherence"
VERSION = "0.1.0a1"
DIST_INFO = f"{NAME}-{VERSION}.dist-info"
WHEEL_NAME = f"{NAME}-{VERSION}-py3-none-any.whl"
SDIST_ROOT = f"declared_coherence-{VERSION}"


def _metadata():
    readme = (Path(__file__).parent / "README.md").read_text(encoding="utf-8")
    headers = (
        "Metadata-Version: 2.4\n"
        "Name: declared-coherence\n"
        f"Version: {VERSION}\n"
        "Summary: Deterministic validation of declared relationships among repository artifacts\n"
        "Requires-Python: >=3.11\n"
        "License-Expression: Apache-2.0\n"
        "License-File: LICENSE\n"
        "Classifier: Development Status :: 3 - Alpha\n"
        "Classifier: Intended Audience :: Developers\n"
        "Classifier: Programming Language :: Python :: 3 :: Only\n"
        "Classifier: Programming Language :: Python :: 3.11\n"
        "Classifier: Programming Language :: Python :: 3.12\n"
        "Classifier: Programming Language :: Python :: 3.13\n"
        "Classifier: Topic :: Software Development :: Quality Assurance\n"
        "Description-Content-Type: text/markdown\n\n"
    )
    return (headers + readme + "\n").encode()


def _wheel_metadata():
    return b"Wheel-Version: 1.0\nGenerator: stdlib-local-backend\nRoot-Is-Purelib: true\nTag: py3-none-any\n"


def _wheel_payload():
    root = Path(__file__).parent
    payload = {}
    for source in sorted((root / "src" / NAME).glob("*.py")):
        payload[f"{NAME}/{source.name}"] = source.read_bytes()
    payload[f"{DIST_INFO}/METADATA"] = _metadata()
    payload[f"{DIST_INFO}/WHEEL"] = _wheel_metadata()
    payload[f"{DIST_INFO}/top_level.txt"] = f"{NAME}\n".encode()
    payload[f"{DIST_INFO}/licenses/LICENSE"] = (root / "LICENSE").read_bytes()
    return payload


def _record_line(path, data):
    digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
    return f"{path},sha256={digest},{len(data)}"


def get_requires_for_build_wheel(config_settings=None):
    return []


def get_requires_for_build_sdist(config_settings=None):
    return []


def prepare_metadata_for_build_wheel(metadata_directory, config_settings=None):
    target = Path(metadata_directory) / DIST_INFO
    target.mkdir(parents=True, exist_ok=True)
    (target / "METADATA").write_bytes(_metadata())
    (target / "WHEEL").write_bytes(_wheel_metadata())
    (target / "top_level.txt").write_text(f"{NAME}\n", encoding="utf-8")
    licenses = target / "licenses"
    licenses.mkdir(exist_ok=True)
    (licenses / "LICENSE").write_bytes((Path(__file__).parent / "LICENSE").read_bytes())
    return DIST_INFO


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    target = Path(wheel_directory) / WHEEL_NAME
    payload = _wheel_payload()
    record_path = f"{DIST_INFO}/RECORD"
    record = "\n".join([_record_line(path, data) for path, data in sorted(payload.items())] + [f"{record_path},,"]) + "\n"
    payload[record_path] = record.encode()
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path, data in sorted(payload.items()):
            info = zipfile.ZipInfo(path, (1980, 1, 1, 0, 0, 0))
            info.create_system = 0
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, data)
    return WHEEL_NAME


def build_sdist(sdist_directory, config_settings=None):
    root = Path(__file__).parent
    files = [
        root / "pyproject.toml", root / "README.md", root / "LICENSE",
        root / "CONTRIBUTING.md", root / "SECURITY.md", root / "CHANGELOG.md",
        root / ".gitignore", root / "_build_backend.py",
        root / ".github" / "workflows" / "test.yml",
    ]
    files.extend(sorted((root / "src" / NAME).glob("*.py")))
    files.extend(sorted((root / "tests").glob("*.py")))
    files.extend(sorted((root / "examples").glob("*.py")))
    files.extend(sorted((root / "docs").glob("*.md")))
    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode="w", format=tarfile.PAX_FORMAT) as archive:
        for source in files:
            relative = source.relative_to(root).as_posix()
            data = source.read_bytes()
            info = tarfile.TarInfo(f"{SDIST_ROOT}/{relative}")
            info.size = len(data)
            info.mtime = 0
            info.mode = 0o644
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            archive.addfile(info, io.BytesIO(data))
    filename = f"{SDIST_ROOT}.tar.gz"
    with (Path(sdist_directory) / filename).open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0, compresslevel=9) as compressed:
            compressed.write(tar_buffer.getvalue())
    return filename
