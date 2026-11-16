"""Install the staged 057 dungeon assets after stopping the candidate client."""
from pathlib import Path
import sys,json,hashlib
sys.path.insert(0,r'D:\GAME\work\PopTag-monster-port')
from audit_shop324_compat import load_index,read_asset
from fix_map_object_indices import decrypt
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'port-audit/dungeon057'
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
    manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
    client=ROOT/'client';path=client/'fx.idx';archive=client/'fx.idd'
    assert not (OUT/'installed.json').exists()
    assert sha(path.read_bytes())==manifest['beforeIndexSha256']
    assert archive.stat().st_size==manifest['originalArchiveBytes']
    before,_=load_index(path);after,_=load_index(OUT/'fx.idx.candidate')
    assert all(after[n]==entry for n,entry in before.items()),'Existing asset entries changed'
    assert len(after)-len(before)==44
    append=(OUT/'fx.append.bin').read_bytes();assert len(append)==manifest['appendBytes']
    try:
        with archive.open('ab') as f:f.write(append)
        path.write_bytes((OUT/'fx.idx.candidate').read_bytes())
        actual,_=load_index(path)
        for row in manifest['maps']:
            entry=actual[row['name']];plain=decrypt(read_asset(client,entry),entry['flags'])
            assert sha(plain)==row['convertedSha256']
        assert sha(path.read_bytes())==manifest['candidateIndexSha256']
    except Exception:
        path.write_bytes((OUT/'fx.idx.before').read_bytes())
        with archive.open('r+b') as f:f.truncate(manifest['originalArchiveBytes'])
        raise
    (OUT/'installed.json').write_text(json.dumps(dict(installedMaps=22,installedMinimaps=22,existingAssetEntriesPreserved=True,readbackVerified=True,gameplayVerified=False),indent=2))
    print('Installed 22 dungeons and 22 minimaps; all 22 decrypted readbacks verified')
if __name__=='__main__':main()
