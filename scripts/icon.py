"""Optional menu artwork: a supplied JPEG, or the first frame of the itch.io banner."""
import argparse
import hashlib
import io
import json
import shutil
import sys
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from common import ROOT
PAGE = 'https://maddymakesgamesinc.itch.io/celeste64'

class BannerParser(HTMLParser):

    def __init__(self):
        super().__init__()
        self.header_depth = 0
        self.url = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'div':
            if self.header_depth:
                self.header_depth += 1
            elif attrs.get('id') == 'header':
                self.header_depth = 1
        if tag == 'img' and self.header_depth and (self.url is None):
            url = urllib.parse.urljoin(PAGE, attrs.get('src', ''))
            parsed = urllib.parse.urlsplit(url)
            if parsed.scheme == 'https' and parsed.hostname == 'img.itch.zone' and parsed.path.lower().endswith('.gif'):
                self.url = url

    def handle_endtag(self, tag):
        if tag == 'div' and self.header_depth:
            self.header_depth -= 1

def fetch(url, maximum):
    req = urllib.request.Request(url, headers={'User-Agent': 'Celeste64-Switch-build'})
    with urllib.request.urlopen(req, timeout=15) as response:
        if not response.url.startswith('https://'):
            raise ValueError('Insecure icon download redirect')
        data = response.read(maximum + 1)
    if len(data) > maximum:
        raise ValueError('Icon download exceeds size limit')
    return data

def render_banner(data):
    from PIL import Image
    with Image.open(io.BytesIO(data)) as image:
        if image.format != 'GIF':
            raise ValueError('Expected the GIF banner')
        if image.width * image.height > 4000000:
            raise ValueError('Banner dimensions exceed size limit')
        image.seek(0)
        image = image.convert('RGBA')
        side = min(image.size)
        left, top = ((image.width - side) // 2, (image.height - side) // 2)
        square = image.crop((left, top, left + side, top + side))
        background = Image.new('RGBA', square.size, '#040b14')
        background.alpha_composite(square)
        icon = background.convert('RGB').resize((256, 256), Image.Resampling.LANCZOS)
        output = io.BytesIO()
        icon.save(output, 'JPEG', quality=95, subsampling=0, progressive=False)
        return output.getvalue()

def prepare_icon(supplied=None):
    local = ROOT / 'local/icon.jpg'
    if supplied is not None:
        supplied = Path(supplied).resolve()
        if not supplied.is_file() or supplied.read_bytes()[:2] != b'\xff\xd8':
            raise ValueError('--icon must be an existing 256x256 baseline JPEG file')
        local.parent.mkdir(parents=True, exist_ok=True)
        if supplied != local.resolve():
            shutil.copyfile(supplied, local)
    if local.is_file():
        print('Using supplied menu icon:', local, flush=True)
        return local
    destination = ROOT / 'artifacts/celeste64-switch-metadata/icon.jpg'
    if destination.is_file():
        print('Using cached banner icon:', destination, flush=True)
        return destination
    temporary = destination.with_suffix('.jpg.part')
    try:
        print('Attempting menu icon from the itch.io GIF banner...', flush=True)
        parser = BannerParser()
        parser.feed(fetch(PAGE, 2 * 1024 * 1024).decode('utf-8'))
        if not parser.url:
            raise ValueError('No GIF banner found in the page header')
        banner = fetch(parser.url, 16 * 1024 * 1024)
        icon = render_banner(banner)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary.write_bytes(icon)
        manifest = {'page': PAGE, 'banner': parser.url, 'frame': 0, 'crop': 'center square', 'size': [256, 256], 'banner_sha256': hashlib.sha256(banner).hexdigest(), 'icon_sha256': hashlib.sha256(icon).hexdigest()}
        destination.with_name('icon-input.json').write_text(json.dumps(manifest, indent=2) + '\n')
        temporary.replace(destination)
        print('Generated menu icon:', destination, flush=True)
        return destination
    except Exception as error:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        print(f'Optional banner icon unavailable ({type(error).__name__}); continuing with the default icon.', file=sys.stderr, flush=True)
        return None
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--icon', type=Path, help='Supply an existing 256x256 baseline JPEG')
    args = parser.parse_args()
    try:
        prepare_icon(args.icon)
    except (OSError, ValueError) as error:
        raise SystemExit(str(error))
