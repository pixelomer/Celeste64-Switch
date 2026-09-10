"""Verified downloads and bounded extraction for build dependencies."""
import hashlib, os, stat, urllib.request, zipfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def sha256(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def download(url, path, digest=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if digest and sha256(path) != digest:
            raise RuntimeError(f'Checksum mismatch: {path.name}; remove it and retry')
        return
    if not url.startswith('https://'):
        raise RuntimeError('Downloads require HTTPS')
    temporary = path.with_name(path.name + '.part')
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Celeste64-Switch-build'}), timeout=60) as src, temporary.open('wb') as dst:
            if not src.url.startswith('https://'):
                raise RuntimeError('Insecure download redirect')
            while (chunk := src.read(1024 * 1024)):
                dst.write(chunk)
        if digest and sha256(temporary) != digest:
            raise RuntimeError(f'Checksum mismatch: {path.name}')
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)

def extract_sdk_zip(archive, destination):
    destination = Path(destination).resolve()
    with zipfile.ZipFile(archive) as z:
        for m in z.infolist():
            target = destination / m.filename
            if not target.resolve().is_relative_to(destination) or stat.S_ISLNK(m.external_attr >> 16):
                raise RuntimeError('Unsafe SDK ZIP member')
            z.extract(m, destination)
            if target.is_file():
                target.chmod(m.external_attr >> 16 & 511 or 420)
