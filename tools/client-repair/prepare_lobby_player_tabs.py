"""Copy only LB_Img frames 72..75 from CN057, preserving all other UI frames."""
from pathlib import Path
import sys,struct,json,hashlib
sys.path.insert(0,r'D:\GAME\work\PopTag-monster-port')
from audit_shop324_compat import CN057,load_index,read_asset
from legacy_sprite_codec import modern_page,encode_legacy,frame_from_sprite
from PIL import Image
import numpy as npy
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'port-audit/lobby-player-tabs'
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
    OUT.mkdir(exist_ok=True)
    assert not (OUT/'manifest.json').exists()
    idx,_=load_index(ROOT/'client/fx.idx');source,_=load_index(CN057/'fx.idx');name='Lobby/LB_Img'
    raw=read_asset(ROOT/'client',idx[name]);cn=read_asset(CN057,source[name])
    nf,version,np,flags=struct.unpack_from('<4I',raw);assert (nf,version)==(77,2)
    dims=[struct.unpack_from('<2I',raw,16+j*8) for j in range(np)]
    end=16+8*np+48*nf;pos=end;pages=[];originalPages=[];changedPages=set()
    for h,w in dims:
        size=struct.unpack_from('<I',raw,pos)[0];pos+=4
        originalPages.append(raw[pos:pos+size]);pages.append(modern_page(raw[pos:pos+size],w,h));pos+=size
    assert pos==len(raw)
    for frame in [72,73,74,75]:
        f=struct.unpack_from('<12i',raw,16+8*np+48*frame)
        image=frame_from_sprite(cn,frame)
        assert image.size==frame_from_sprite(raw,frame).size
        pages[f[3]].paste(image,f[4:6])
        changedPages.add(f[3])
    result=bytearray(raw[:end])
    for j,image in enumerate(pages):
        encoded=encode_legacy(image) if j in changedPages else originalPages[j]
        result+=struct.pack('<I',len(encoded))+encoded
    assert result[:end]==raw[:end]
    for frame in range(nf):
        expected=frame_from_sprite(cn if frame in [72,73,74,75] else raw,frame)
        actual=frame_from_sprite(result,frame)
        background=Image.new('RGBA',expected.size,(0,0,0,255))
        if frame in [72,73,74,75]:
            a=npy.asarray(actual).astype(int);b=npy.asarray(expected).astype(int);visible=a[:,:,3]>0
            assert npy.max(npy.abs(a[:,:,:3][visible]-b[:,:,:3][visible]),initial=0)<=7,frame
            assert npy.all(a[:,:,3][b[:,:,3]==0]==0),frame
        else:
            assert Image.alpha_composite(background,actual).tobytes()==Image.alpha_composite(background,expected).tobytes(),frame
    (OUT/'LB_Img.before').write_bytes(raw);(OUT/'LB_Img.candidate').write_bytes(result)
    (OUT/'manifest.json').write_text(json.dumps(dict(asset=name,frames=[72,73,74,75],beforeSha256=sha(raw),afterSha256=sha(result),source=str(CN057),otherFramesPixelIdentical=True),indent=2))
    print('Prepared four original CN057 player tabs; other 73 frames pixel-identical')
if __name__=='__main__':main()
