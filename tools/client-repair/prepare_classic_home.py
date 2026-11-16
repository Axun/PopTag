"""Compose a native UI banner from actual equipped sprites; preserve all UI geometry."""
from pathlib import Path
import sys,struct,json,hashlib
from PIL import Image,ImageDraw,ImageFont
sys.path.insert(0,r'D:\GAME\work\PopTag-monster-port')
from audit_shop324_compat import CN057,load_index,read_asset
from legacy_sprite_codec import frame_from_sprite,encode_legacy
from rewrite_fx_index import write_index
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'port-audit/classic057-clothing'

def main():
    fx,key=load_index(ROOT/'client/fx.idx');char,_=load_index(ROOT/'client/CharTE.idx');src,_=load_index(CN057/'CharTE.idx')
    old=read_asset(ROOT/'client',fx['Shop/S_Main'],'fx')
    assert struct.unpack_from('<3I',old)==(1,2,1)
    image=frame_from_sprite(old).convert('RGBA');assert image.size==(508,454)
    draw=ImageDraw.Draw(image)
    # This is a UI composition from the shipped game sprites, not a replacement
    # game render or an invented product. Lower purchase hitboxes remain intact.
    draw.rectangle((20,14,487,168),fill='#123a79')
    for y in range(15,168):
        t=(y-15)/153;draw.line((21,y,486,y),fill=(int(18+8*t),int(57+41*t),int(120+42*t)))
    for x in range(32,488,24):
        for y in range(22,169,24):draw.ellipse((x,y,x+3,y+3),fill='#2a66ab')
    font=ImageFont.truetype(r'C:\Windows\Fonts\msyhbd.ttc',18)
    small=ImageFont.truetype(r'C:\Windows\Fonts\msyh.ttc',11)
    draw.text((34,22),'经典衣橱 · 换个造型一起玩',font=font,fill='#ffffff')
    draw.text((35,49),'经典服饰回归  /  衣服与帽子可分别搭配',font=small,fill='#b9eaff')
    proofs=[]
    for x,c,style,label in [(62,2,4,'小乖·将军'),(139,2,1,'小乖·圣诞'),(216,6,1,'宝宝·经典'),(293,6,4,'宝宝·绅士'),(370,0,None,'皮蛋·酷装'),(447,1,None,'黑妞·趣搭')]:
        canvas=Image.new('RGBA',(128,140));assets=[]
        def layer(raw,name):
            n,v,p,f=struct.unpack_from('<4I',raw);frame=struct.unpack_from('<12i',raw,16+8*p)
            canvas.alpha_composite(frame_from_sprite(raw),(64-frame[0],128-frame[1]));assets.append(name)
        name=f'Character/C{c:02d}-WalkDown_ALayerStatic';layer(read_asset(ROOT/'client',fx[name],'fx'),name)
        if style is not None:
            for part in [21,41]:
                name=f'AvatarDeco/A{c:02d}_{part}_{style:04d}_0LayerStatic'
                assert name in src;layer(read_asset(CN057,src[name],'CharTE'),name)
        else:
            name='CharDeco/CharDeco_A0022';assert name in char
            # Promotional standing pose: place this floating head ornament by
            # the base figure's head, rather than use its per-animation offsets.
            ornament=frame_from_sprite(read_asset(ROOT/'client',char[name],'CharTE'))
            ornament=ornament.crop(ornament.getbbox());ornament.thumbnail((25,25))
            top=canvas.getbbox()[1]
            canvas.alpha_composite(ornament,(64-ornament.width//2,top-ornament.height+5));assets.append(name)
        box=canvas.getbbox();assert box
        figure=canvas.crop(box);figure.thumbnail((66,82))
        draw.ellipse((x-24,138,x+24,146),fill='#0b2d64')
        image.alpha_composite(figure,(x-figure.width//2,143-figure.height))
        draw.text((x,149),label,font=small,anchor='mt',fill='#ffffff')
        proofs.append({'label':label,'assets':assets})
    image.save(OUT/'shop-home-preview.png')
    # Keep frame count, anchor, dimensions, flags and all lower controls unchanged.
    encoded=encode_legacy(image);new=old[:72]+struct.pack('<I',len(encoded))+encoded
    assert frame_from_sprite(new).size==(508,454)
    assert new[:72]==old[:72]
    assert image.crop((0,170,508,454)).tobytes()==frame_from_sprite(old).convert('RGBA').crop((0,170,508,454)).tobytes()
    base=(ROOT/'client/fx.idd').stat().st_size;before=fx['Shop/S_Main']
    fx['Shop/S_Main']={**before,'offset':base,'size':len(new)}
    (OUT/'fx.idx.before').write_bytes((ROOT/'client/fx.idx').read_bytes())
    write_index(OUT/'fx.idx.candidate',fx,key);(OUT/'fx.append.bin').write_bytes(new)
    (OUT/'home-manifest.json').write_text(json.dumps({'source':'Shipped CN057 clothing and existing native base characters/accessory sprites','compositions':proofs,'before':before,'originalIddSize':base,'sha256':hashlib.sha256(new).hexdigest(),'frameGeometryPreserved':True,'lowerControlsPreserved':True},ensure_ascii=False,indent=2),encoding='utf8')
    print('Native home banner prepared, 6 outfit compositions; purchase controls untouched.')
if __name__=='__main__':main()
