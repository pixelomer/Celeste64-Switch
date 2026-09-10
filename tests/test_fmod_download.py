import contextlib
import io
import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import download_fmod as fmod


class FmodDownload(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.patch = patch.object(fmod, 'ROOT', self.root)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.env = patch.dict(os.environ, {}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_registration_activation_and_cached_login(self):
        def mailbox(path, token=None, body=None):
            return {
                'domains': {'hydra:member': [{'domain': 'example.invalid'}]},
                'accounts': {'id': 'mail-id'}, 'token': {'token': 'mail-secret'},
                'messages': {'hydra:member': [{'id': 'first'}]},
                'messages/first': {'html': ['<a href="https://www.fmod.com/profile/registration?key=verify-secret">Verify</a>']},
            }[path]

        def api(path, headers=None, body=None):
            if path == 'api-register':
                self.assertFalse(json.loads(body)['ml_news'])
                return {'status': 'success'}
            if path == 'api-registration':
                self.assertEqual(headers['Authorization'], 'FMOD verify-secret')
                return {'status': 'success'}
            self.assertEqual(path, 'api-login')
            return {'token': 'fmod-secret', 'user': 'user-id'}

        output = io.StringIO()
        with patch.object(fmod, 'mail_api', side_effect=mailbox) as mail, patch.object(fmod, 'api', side_effect=api), contextlib.redirect_stdout(output):
            self.assertEqual(fmod.authenticate()['user'], 'user-id')
            count = mail.call_count
            self.assertEqual(fmod.authenticate()['user'], 'user-id')
            self.assertEqual(mail.call_count, count)
        path = self.root / 'fmod-login.json'
        saved = json.loads(path.read_text())
        self.assertEqual(saved['stage'], 'ready')
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        for secret in [saved['password'], saved['email'], 'mail-secret', 'verify-secret', 'fmod-secret']:
            self.assertNotIn(secret, output.getvalue())

    def test_timeout_preserves_registration_and_does_not_reregister(self):
        path = self.root / 'fmod-login.json'
        fmod.save_account(path, {'username': 'test', 'password': 'secret', 'email': 'test@example.invalid', 'stage': 'verification'})
        with patch.object(fmod, 'mail_api', return_value={'token': 'token'}), patch.object(fmod, 'api') as api, patch.object(fmod.time, 'monotonic', side_effect=[0, 2]), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(RuntimeError, 'timed out'):
                fmod.authenticate(timeout=1)
        api.assert_not_called()
        self.assertEqual(json.loads(path.read_text())['stage'], 'verification')

    def test_environment_credentials_do_not_create_or_save_account(self):
        with patch.dict(os.environ, {'FMOD_USERNAME': 'test', 'FMOD_PASSWORD': 'secret'}), patch.object(fmod, 'login', return_value={'token': 'token'}) as login, patch.object(fmod, 'register_account') as register:
            fmod.authenticate()
        login.assert_called_once_with({'username': 'test', 'password': 'secret'})
        register.assert_not_called()
        self.assertFalse((self.root / 'fmod-login.json').exists())

    def test_partial_credentials_fail_without_registration(self):
        with patch.dict(os.environ, {'FMOD_USERNAME': 'test'}), patch.object(fmod, 'register_account') as register:
            with self.assertRaisesRegex(RuntimeError, 'Set both'):
                fmod.authenticate()
        register.assert_not_called()

    def test_activation_ignores_untrusted_links(self):
        for url in ['https://evil.invalid/registration?key=secret',
                    'https://www.fmod.com.evil.invalid/registration?key=secret',
                    'https://www.fmod.com:444/registration?key=secret',
                    'https://www.fmod.com/download?key=secret']:
            self.assertIsNone(fmod.confirmation({'text': url}))
        self.assertEqual(fmod.confirmation({'text': 'https://www.fmod.com/profile/registration?key=ok'})[1], 'ok')

    def test_manual_archives_and_cache_do_not_authenticate(self):
        original = self.root / 'manual'
        original.mkdir()
        item = {'filename': 'test-sdk.tar.gz'}
        (original / item['filename']).write_bytes(b'archive')
        item['sha256'] = fmod.sha256(original / item['filename'])
        (self.root / 'dependencies.json').write_text(json.dumps({'fmod': {'version': 'test', 'platforms': {'linux': item}}}))
        with patch.object(fmod, 'authenticate') as auth, contextlib.redirect_stdout(io.StringIO()):
            fmod.main(['--archive-dir', str(original)])
            fmod.main([])
        auth.assert_not_called()

    def test_existing_account_noninteractive_never_registers(self):
        with patch.object(fmod.sys.stdin, 'isatty', return_value=False), patch.object(fmod, 'register_account') as register:
            with self.assertRaisesRegex(RuntimeError, 'noninteractive'):
                fmod.authenticate(existing=True)
        register.assert_not_called()

    def test_credential_symlinks_rejected(self):
        source = self.root / 'private'
        source.write_text('{"username":"test","password":"secret"}')
        (self.root / 'fmod-login.json').symlink_to(source)
        with self.assertRaisesRegex(RuntimeError, 'symlink'):
            fmod.authenticate()
