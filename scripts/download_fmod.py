#!/usr/bin/env python3
"""FMOD registration/download flow adapted from pixelomer/Celeste-FMOD2.

Automatically register through mail.tm when neither supplied nor cached FMOD
credentials exist. Keep generated credentials private and reuse them on retries.
"""
import argparse
import base64
import getpass
import html
import json
import os
import re
import secrets
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from common import ROOT, download, sha256

FMOD = 'https://www.fmod.com/'
MAIL = 'https://api.mail.tm/'


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Never forward account credentials or verification tokens to redirects.
        return None


def request_json(url, headers=None, body=None):
    service = 'FMOD' if url.startswith(FMOD) else 'mail.tm'
    req = urllib.request.Request(url, data=body, headers={
        'User-Agent': 'Celeste64-Switch-build', **(headers or {})})
    try:
        with urllib.request.build_opener(NoRedirect).open(req, timeout=30) as f:
            result = json.load(f)
        if not isinstance(result, dict):
            raise ValueError('Expected an object')
        return result
    except urllib.error.HTTPError as e:
        raise RuntimeError(f'{service} request failed (HTTP {e.code}); retry or use local archives') from None
    except (urllib.error.URLError, OSError, ValueError):
        raise RuntimeError(f'{service} request failed; retry or use local archives') from None


def api(path, headers=None, body=None):
    return request_json(FMOD + path, {
        'Origin': FMOD.rstrip('/'), 'Referer': FMOD + 'download',
        'Content-Type': 'text/plain;charset=UTF-8', **(headers or {})}, body)


def mail_api(path, token=None, body=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    return request_json(MAIL + path, headers,
                        json.dumps(body).encode() if body is not None else None)


def save_account(path, account):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.fmod-account-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(account, f)
            f.write('\n')
        os.replace(name, path)  # mkstemp creates mode 0600, including on replacement.
    finally:
        Path(name).unlink(missing_ok=True)


def load_account(path):
    if path.is_symlink():
        raise RuntimeError('Refusing a symlinked FMOD credential file')
    try:
        data = json.loads(path.read_text())
        if not isinstance(data, dict) or not all(
                isinstance(data.get(k), str) and data[k] for k in ['username', 'password']):
            raise ValueError('Invalid credentials')
    except (OSError, ValueError):
        raise RuntimeError('Invalid fmod-login.json; supply credentials or restore the file') from None
    path.chmod(0o600)
    return data


def confirmation(message):
    parts = [message.get('text', '')]
    markup = message.get('html', [])
    parts.extend(markup if isinstance(markup, list) else [markup])
    for part in parts:
        if not isinstance(part, str):
            continue
        for url in re.findall(r'https://[^\s<>"\']+', html.unescape(part)):
            try:
                parsed = urllib.parse.urlsplit(url)
                trusted = parsed.hostname == 'www.fmod.com' and parsed.port in (None, 443) and not parsed.username
            except ValueError:
                continue
            if not trusted:
                continue
            if 'registration' not in parsed.path.lower():
                continue
            query = urllib.parse.parse_qsl(parsed.query)
            if query and query[-1][1]:
                return url, query[-1][1]
    return None


def register_account(path, timeout=180):
    account = load_account(path) if path.exists() else None
    if account is None:
        print('Choosing a temporary email domain from mail.tm...', flush=True)
        domains = mail_api('domains').get('hydra:member', [])
        domain = next((d.get('domain') for d in domains
                       if d.get('isActive', True) and not d.get('isPrivate', False)), None)
        if not domain:
            raise RuntimeError('mail.tm returned no available domains; use an existing account or local archives')
        username = secrets.token_hex(16)
        account = {'username': username, 'password': secrets.token_urlsafe(30),
                   'email': username + '@' + domain, 'stage': 'new'}
        save_account(path, account)
    mail_auth = {'address': account['email'], 'password': account['password']}
    if account['stage'] == 'new':
        print('Creating temporary mailbox...', flush=True)
        # Persist before the request: an ambiguous network failure must not create
        # more accounts on retry. The next run attempts login to this same mailbox.
        account['stage'] = 'mailbox'
        save_account(path, account)
        if not mail_api('accounts', body=mail_auth).get('id'):
            raise RuntimeError('mail.tm did not create a mailbox; inspect the saved account before retrying')
    mail_token = mail_api('token', body=mail_auth).get('token')
    if not mail_token:
        raise RuntimeError('mail.tm authentication failed; use an existing FMOD account or local archives')
    if account['stage'] == 'mailbox':
        print('Creating FMOD account...', flush=True)
        account['stage'] = 'verification'
        save_account(path, account)
        result = api('api-register', {'Referer': FMOD + 'profile/register'}, json.dumps({
            'username': account['username'], 'password': account['password'],
            'company': '', 'email': account['email'], 'name': account['username'],
            'ml_news': False, 'ml_release': False, 'industry': 1}).encode())
        if result.get('error') or result.get('status') in ('error', 'failed', False):
            raise RuntimeError('FMOD registration was rejected; use an existing account or local archives')
    print(f'Waiting up to {timeout} seconds for the FMOD verification email...', flush=True)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        messages = mail_api('messages', mail_token).get('hydra:member', [])
        for message in messages:
            message_id = message.get('id')
            if not isinstance(message_id, str):
                continue
            result = confirmation(mail_api('messages/' + urllib.parse.quote(message_id, safe=''), mail_token))
            if not result:
                continue
            url, key = result
            api('api-registration', {'Referer': url, 'Authorization': 'FMOD ' + key})
            # Login confirms activation before marking the cached account ready.
            auth = login(account)
            account['stage'] = 'ready'
            save_account(path, account)
            return auth
        remaining = deadline - time.monotonic()
        if remaining > 0:
            time.sleep(min(3, remaining))
    raise RuntimeError('FMOD verification email timed out; rerun to resume the same account, or use local archives')


def login(account):
    basic = base64.b64encode(f"{account['username']}:{account['password']}".encode()).decode()
    auth = api('api-login', {'Authorization': 'Basic ' + basic}, b'{}')
    if not auth.get('token') or not auth.get('user'):
        raise RuntimeError('FMOD login did not return an authenticated account')
    return auth


def authenticate(existing=False, timeout=180):
    username, password = os.environ.get('FMOD_USERNAME'), os.environ.get('FMOD_PASSWORD')
    if username or password:
        if not username or not password:
            raise RuntimeError('Set both FMOD_USERNAME and FMOD_PASSWORD')
        return login({'username': username, 'password': password})
    path = ROOT / 'fmod-login.json'
    if path.exists() or path.is_symlink():
        account = load_account(path)
        if account.get('stage', 'ready') == 'ready':
            print('Reusing saved FMOD account...', flush=True)
            return login(account)
        if existing:
            raise RuntimeError('Saved registration is incomplete; supply FMOD_USERNAME/FMOD_PASSWORD or resume without --existing-account')
    elif existing:
        if not sys.stdin.isatty():
            raise RuntimeError('Use FMOD_USERNAME/FMOD_PASSWORD or local archives for a noninteractive existing-account build')
        return login({'username': input('FMOD username: '), 'password': getpass.getpass('FMOD password: ')})
    return register_account(path, timeout)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive-dir', type=Path, help='Directory containing the two original 2.02.18 SDK archives')
    p.add_argument('--existing-account', action='store_true', help='Use supplied/cached credentials or prompt; never register an account')
    p.add_argument('--email-timeout', type=int, default=180, help='Verification-email wait limit in seconds (default: 180)')
    a = p.parse_args(argv)
    if a.email_timeout <= 0:
        p.error('--email-timeout must be positive')
    lock = json.loads((ROOT / 'dependencies.json').read_text())['fmod']
    out = ROOT / 'fmod'
    out.mkdir(exist_ok=True)
    pending = []
    for platform, item in lock['platforms'].items():
        dest = out / item['filename']
        if not dest.exists() and a.archive_dir:
            src = a.archive_dir / item['filename']
            if not src.is_file() or sha256(src) != item['sha256']:
                raise RuntimeError('Missing or incorrect FMOD archive: ' + item['filename'])
            shutil.copyfile(src, dest)
        if dest.exists():
            if sha256(dest) != item['sha256']:
                raise RuntimeError('FMOD archive checksum mismatch: ' + item['filename'])
        else:
            pending.append((platform, item, dest))
    if pending:
        auth = authenticate(a.existing_account, a.email_timeout)
        for platform, item, dest in pending:
            query = urllib.parse.urlencode({'path': f'files/fmodstudio/api/{platform.title()}/',
                                           'filename': item['filename'], 'user_id': auth['user']})
            link = api('api-get-download-link?' + query, {'Authorization': 'FMOD ' + auth['token']}).get('url')
            if not isinstance(link, str) or not link.startswith('https://'):
                raise RuntimeError('FMOD did not return a download URL; use --archive-dir')
            print('Downloading FMOD ' + lock['version'] + ' ' + platform, flush=True)
            try:
                download(link, dest, item['sha256'])
            except (OSError, ValueError):
                raise RuntimeError('FMOD archive download failed; retry or use --archive-dir') from None
    print('Verified FMOD SDK archives. Their license remains applicable.')


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError) as e:
        raise SystemExit(str(e))
