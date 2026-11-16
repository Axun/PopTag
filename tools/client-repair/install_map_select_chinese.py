"""Install only the three prepared map-selector UI assets with rollback."""
from pathlib import Path
import sys,json,hashlib
sys.path.insert(0,r'D:\GAME\work\PopTag-monster-port')
from audit_shop324_compat import load_index,read_asset
from rewrite_fx_index import write_index
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'port-audit/map-select-chinese'
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
    assert not (OUT/'installed.json').exists()
    client=ROOT/'client';idx,key=load_index(client/'fx.idx');rows=json.loads((OUT/'manifest.json').read_text())
    before=(client/'fx.idx').read_bytes();size=(client/'fx.idd').stat().st_size
    (OUT/'fx.idx.before').write_bytes(before)
    for row in rows:
        assert sha(read_asset(client,idx[row['asset']]))==row['beforeSha256']
        assert sha((OUT/row['candidate']).read_bytes())==row['candidateSha256']
    try:
        with (client/'fx.idd').open('ab') as f:
            for row in rows:
                data=(OUT/row['candidate']).read_bytes();name=row['asset']
                idx[name]={**idx[name],'offset':f.tell(),'size':len(data)};f.write(data)
        write_index(client/'fx.idx',idx,key)
        actual,_=load_index(client/'fx.idx')
        for row in rows:assert sha(read_asset(client,actual[row['asset']]))==row['candidateSha256']
    except Exception:
        (client/'fx.idx').write_bytes(before)
        with (client/'fx.idd').open('r+b') as f:f.truncate(size)
        raise
    (OUT/'installed.json').write_text(json.dumps(dict(assets=3,geometryPreserved=True,readbackVerified=True),indent=2))
    print('Installed Chinese map title and both map-list filters')
if __name__=='__main__':main()
