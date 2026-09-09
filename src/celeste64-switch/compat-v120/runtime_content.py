"""Exclude model-authoring inputs; retain every model the game can load."""
import hashlib, json, shutil

def prune_editor_content(out):
    source = out / 'romfs/Content/Models/Sources'
    if not source.exists():
        return
    assert not any((p.suffix.lower() == '.glb' for p in source.rglob('*'))), 'Unexpected runtime model in Sources'
    entries = [{'path': str(p.relative_to(out / 'romfs')), 'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(source.rglob('*')) if p.is_file()]
    (out / 'excluded-editor-content.json').write_text(json.dumps(entries, indent=2) + '\n')
    shutil.rmtree(source)
