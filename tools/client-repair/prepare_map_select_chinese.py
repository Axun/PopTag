"""Restore CN057 map-selector title and filter buttons within existing frame bounds."""
from pathlib import Path
import sys,json,hashlib
sys.path.insert(0,r'D:\GAME\work\PopTag-monster-port')
from audit_shop324_compat import CN057,load_index,read_asset
sys.path.insert(0,str(Path(__file__).resolve().parent))
from prepare_remaining_ui import patch_sprite
from legacy_sprite_codec import frame_from_sprite
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'port-audit/map-select-chinese'
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
    OUT.mkdir(exist_ok=False)
    old,_=load_index(ROOT/'client/fx.idx');source,_=load_index(CN057/'fx.idx');rows=[]
    for j,name in enumerate(['Prepare/Dlg_PRE-SelMap','Prepare/Dlg_PRE-SelMapBt_ListAll','Prepare/Dlg_PRE-SelMapBt_ListAvailable']):
        raw=read_asset(ROOT/'client',old[name]);cn=read_asset(CN057,source[name])
        result=patch_sprite(raw,cn)
        (OUT/f'{j}.before').write_bytes(raw);(OUT/f'{j}.candidate').write_bytes(result)
        frame_from_sprite(result).save(OUT/f'{j}.png')
        rows.append(dict(asset=name,candidate=f'{j}.candidate',beforeSha256=sha(raw),candidateSha256=sha(result),frameGeometryPreserved=True))
    (OUT/'manifest.json').write_text(json.dumps(rows,indent=2))
    print('Prepared Chinese map-selection title and both filters')
if __name__=='__main__':main()
