import hashlib, importlib.util, json, stat, sys, tempfile, unittest, zipfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from common import extract_sdk_zip, download

class ArchiveSafety(unittest.TestCase):

    def test_reject_path_escape(self):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            p = r / 'bad.zip'
            with zipfile.ZipFile(p, 'w') as z:
                z.writestr('../escape', 'bad')
            with self.assertRaises(RuntimeError):
                extract_sdk_zip(p, r / 'sdk')
            self.assertFalse((r / 'escape').exists())

    def test_reject_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            p = r / 'bad.zip'
            info = zipfile.ZipInfo('link')
            info.external_attr = (stat.S_IFLNK | 511) << 16
            with zipfile.ZipFile(p, 'w') as z:
                z.writestr(info, '/tmp')
            with self.assertRaises(RuntimeError):
                extract_sdk_zip(p, r / 'sdk')

    def test_preserve_executable_permission(self):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            p = r / 'sdk.zip'
            info = zipfile.ZipInfo('bin/compiler')
            info.external_attr = (stat.S_IFREG | 493) << 16
            with zipfile.ZipFile(p, 'w') as z:
                z.writestr(info, 'test')
            extract_sdk_zip(p, r / 'sdk')
            self.assertEqual((r / 'sdk/bin/compiler').stat().st_mode & 511, 493)

    def test_corrupted_cache_is_not_accepted(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'archive'
            p.write_bytes(b'wrong')
            with self.assertRaises(RuntimeError):
                download('https://example.invalid/file', p, hashlib.sha256(b'correct').hexdigest())
            self.assertEqual(p.read_bytes(), b'wrong')

class InstallPackage(unittest.TestCase):

    def test_built_package_layout_and_hashes(self):
        paths = list((ROOT / 'dist').glob('*.zip'))
        if not paths:
            self.skipTest('Build an installation ZIP first')
        for path in paths:
            with self.subTest(zip=path.name), zipfile.ZipFile(path) as z:
                names = z.namelist()
                self.assertEqual(z.testzip(), None)
                manifest = json.loads(z.read('BUILD-MANIFEST.json'))
                for n, v in manifest['files'].items():
                    data = z.read(n)
                    self.assertEqual(len(data), v['bytes'])
                    self.assertEqual(hashlib.sha256(data).hexdigest(), v['sha256'])
                for n in names:
                    self.assertFalse(n.startswith('/') or '..' in Path(n).parts)
                    self.assertTrue(n in ['INSTALL.txt', 'BUILD-MANIFEST.json'] or n.startswith('switch/celeste64/licenses/') or n in ['switch/celeste64-v120.nro', 'switch/celeste64/fmod/libfmod.so', 'switch/celeste64/fmod/libfmodstudio.so'], n)
                for n in ['libfmod.so', 'libfmodstudio.so']:
                    data = z.read('switch/celeste64/fmod/' + n)
                    self.assertEqual(data[:5], b'\x7fELF\x02')
                    self.assertEqual(int.from_bytes(data[18:20], 'little'), 183)
                nro = [n for n in names if n.endswith('.nro')]
                self.assertEqual(len(nro), 1)
                self.assertEqual(z.read(nro[0])[16:20], b'NRO0')
