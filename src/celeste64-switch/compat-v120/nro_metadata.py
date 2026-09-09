"""Read actual NRO metadata and checksum, from a supplied file."""
import hashlib, json, struct, sys
from pathlib import Path

def inspect(path):
    with path.open('rb') as file:
        header = file.read(128)
        assert header[16:20] == b'NRO0', 'Invalid NRO header'
        base = struct.unpack_from('<I', header, 24)[0]
        file.seek(base)
        asset = file.read(56)
        assert asset[:4] == b'ASET', 'Missing NRO assets'
        offset, size = struct.unpack_from('<QQ', asset, 24)
        assert size >= 12400 and base + offset + size <= path.stat().st_size
        file.seek(base + offset)
        nacp = file.read(size)
        file.seek(0)
        digest = hashlib.file_digest(file, 'sha256').hexdigest()
    string = lambda data: data.split(b'\x00')[0].decode('utf-8')
    return dict(file=str(path), bytes=path.stat().st_size, sha256=digest, title=string(nacp[:512]), author=string(nacp[512:768]), version=string(nacp[12384:12400]))
if __name__ == '__main__':
    print(json.dumps(inspect(Path(sys.argv[1])), indent=2))
