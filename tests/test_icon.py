import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import icon

class MenuIcon(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        change = patch.object(icon, 'ROOT', self.root)
        change.start()
        self.addCleanup(change.stop)

    def test_supplied_and_cached_local_image_skip_network(self):
        supplied = self.root / 'supplied.jpg'
        supplied.write_bytes(b'\xff\xd8supplied')
        with patch.object(icon, 'fetch') as fetch, contextlib.redirect_stdout(io.StringIO()):
            result = icon.prepare_icon(supplied)
            self.assertEqual(result.read_bytes(), supplied.read_bytes())
            self.assertEqual(icon.prepare_icon(), result)
        fetch.assert_not_called()

    def test_banner_discovery_uses_only_header_gif(self):
        parser = icon.BannerParser()
        parser.feed('<img src="https://img.itch.zone/banner.gif"><div id="header"><div><img src="https://example.invalid/wrong.gif"></div><img src="https://img.itch.zone/banner.gif"></div>')
        self.assertEqual(parser.url, 'https://img.itch.zone/banner.gif')

    def test_generation_caches_icon_and_provenance(self):
        page = b'<div id="header"><img src="https://img.itch.zone/banner.gif"></div>'
        with patch.object(icon, 'fetch', side_effect=[page, b'GIF89a']) as fetch, patch.object(icon, 'render_banner', return_value=b'\xff\xd8generated'), contextlib.redirect_stdout(io.StringIO()):
            result = icon.prepare_icon()
            self.assertEqual(result.read_bytes(), b'\xff\xd8generated')
            self.assertEqual(icon.prepare_icon(), result)
            self.assertEqual(fetch.call_count, 2)
        self.assertEqual(json.loads(result.with_name('icon-input.json').read_text())['frame'], 0)

    def test_network_or_parser_failure_does_not_fail_build(self):
        for response in [OSError('offline'), b'<html>No banner</html>']:
            with self.subTest(response=response), patch.object(icon, 'fetch', side_effect=response if isinstance(response, Exception) else None, return_value=response), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertIsNone(icon.prepare_icon())
        self.assertFalse((self.root / 'artifacts/celeste64-switch-metadata/icon.jpg').exists())

    def test_missing_decoder_does_not_fail_build(self):
        page = b'<div id="header"><img src="https://img.itch.zone/banner.gif"></div>'
        with patch.object(icon, 'fetch', side_effect=[page, b'GIF89a']), patch.object(icon, 'render_banner', side_effect=ModuleNotFoundError('Pillow')), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertIsNone(icon.prepare_icon())
        self.assertFalse((self.root / 'artifacts/celeste64-switch-metadata/icon.jpg.part').exists())

    def test_render_is_square_baseline_jpeg_using_first_frame(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest('Optional Pillow is unavailable')
        source = io.BytesIO()
        first = Image.new('RGB', (640, 360), 'red')
        first.save(source, 'GIF', save_all=True, append_images=[Image.new('RGB', (640, 360), 'blue')])
        output = icon.render_banner(source.getvalue())
        with Image.open(io.BytesIO(output)) as generated:
            self.assertEqual(generated.format, 'JPEG')
            self.assertEqual(generated.size, (256, 256))
            self.assertFalse(generated.info.get('progressive'))
            red, green, blue = generated.getpixel((128, 128))
            self.assertGreater(red, 240)
            self.assertLess(blue, 10)
