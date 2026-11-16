"""Restore the original CN057 select-player dialog, keeping native geometry."""
from pathlib import Path
import sys,struct,json,hashlib
sys.path.insert(0,r'D:\GAME\work\PopTag-monster-port')
from audit_shop324_compat import CN057,load_index,read_asset
from legacy_sprite_codec import convert_sprite,frame_from_sprite
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'port-audit/select-player-chinese'
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
    OUT.mkdir(exist_ok=False)
    current,_=load_index(ROOT/'client/fx.idx');source,_=load_index(CN057/'fx.idx');name='Etc/Dlg_SelectUser'
    old=read_asset(ROOT/'client',current[name]);raw=read_asset(CN057,source[name])
    nf,ver,np,_=struct.unpack_from('<4I',old);end=16+8*np+48*nf
    assert (nf,ver,np)==(1,2,1)
    assert old[:12]==raw[:12] and old[16:end]==raw[16:end]
    converted,audits=convert_sprite(raw);result=old[:end]+converted[end:]
    assert frame_from_sprite(result).size==(350,221)
    frame_from_sprite(result).save(OUT/'preview.png')
    (OUT/'dialog.before').write_bytes(old);(OUT/'dialog.candidate').write_bytes(result)
    (OUT/'manifest.json').write_text(json.dumps(dict(asset=name,beforeSha256=sha(old),candidateSha256=sha(result),source=str(CN057),frameGeometryPreserved=True,convertedPages=audits),indent=2))
    print('Prepared original Chinese select-player title and both player labels')
if __name__=='__main__':main()
