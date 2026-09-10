#!/usr/bin/env python3
"""FMOD login/download flow adapted from pixelomer/Celeste-FMOD2/download-fmod.sh.
Uses an existing FMOD account; does not register disposable accounts.
Credentials/tokens are neither persisted nor printed. Local archives also work.
"""
import argparse,base64,getpass,json,os,shutil,sys,urllib.error,urllib.parse,urllib.request
from pathlib import Path
from common import ROOT,download,sha256

def api(path,headers=None,body=None):
 req=urllib.request.Request('https://www.fmod.com/'+path,data=body,headers={'User-Agent':'Celeste64-Switch-build','Origin':'https://www.fmod.com','Referer':'https://www.fmod.com/download','Content-Type':'text/plain;charset=UTF-8',**(headers or {})})
 try:
  with urllib.request.urlopen(req,timeout=45) as f:return json.load(f)
 except (urllib.error.HTTPError,urllib.error.URLError,ValueError):
  raise RuntimeError('FMOD request failed; check your account or provide downloaded archives with --archive-dir') from None

def main():
 p=argparse.ArgumentParser();p.add_argument('--archive-dir',type=Path,help='Directory containing the two original 2.02.18 SDK archives');a=p.parse_args()
 lock=json.loads((ROOT/'dependencies.json').read_text())['fmod'];out=ROOT/'fmod';out.mkdir(exist_ok=True)
 pending=[]
 for platform,item in lock['platforms'].items():
  dest=out/item['filename']
  if not dest.exists() and a.archive_dir:
   src=a.archive_dir/item['filename']
   if not src.is_file() or sha256(src)!=item['sha256']:raise RuntimeError('Missing or incorrect FMOD archive: '+item['filename'])
   shutil.copyfile(src,dest)
  if dest.exists():
   if sha256(dest)!=item['sha256']:raise RuntimeError('FMOD archive checksum mismatch: '+item['filename'])
  else:pending.append((platform,item,dest))
 if pending:
  username=os.environ.get('FMOD_USERNAME') or (input('FMOD username: ') if sys.stdin.isatty() else '')
  password=os.environ.get('FMOD_PASSWORD') or (getpass.getpass('FMOD password: ') if sys.stdin.isatty() else '')
  if not username or not password:raise RuntimeError('Provide an existing FMOD account via FMOD_USERNAME/FMOD_PASSWORD, run interactively, or use --archive-dir')
  basic=base64.b64encode(f'{username}:{password}'.encode()).decode()
  auth=api('api-login',{'Authorization':'Basic '+basic},b'{}')
  if not auth.get('token') or not auth.get('user'):raise RuntimeError('FMOD login did not return an authenticated account')
  for platform,item,dest in pending:
   query=urllib.parse.urlencode({'path':f'files/fmodstudio/api/{platform.title()}/','filename':item['filename'],'user_id':auth['user']})
   link=api('api-get-download-link?'+query,{'Authorization':'FMOD '+auth['token']}).get('url')
   if not isinstance(link,str) or not link.startswith('https://'):raise RuntimeError('FMOD did not return a download URL; use --archive-dir')
   print('Downloading FMOD '+lock['version']+' '+platform,flush=True);download(link,dest,item['sha256'])
 print('Verified FMOD SDK archives. Their license remains applicable.')
if __name__=='__main__':
 try:main()
 except (RuntimeError,OSError) as e:raise SystemExit(str(e))
