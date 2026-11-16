"""Rebuild the home showcase from complete native room-decoration compositions."""
from pathlib import Path
import sys,struct,json,hashlib
from PIL import Image,ImageDraw,ImageFont
sys.path.insert(0,r'D:\GAME\work\PopTag-monster-port')
from audit_shop324_compat import load_index,read_asset,CN057
from legacy_sprite_codec import frame_from_sprite,encode_legacy
from rewrite_fx_index import write_index
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'port-audit/reference-shop-home'

def main():
    OUT.mkdir(parents=True,exist_ok=False)
    fx,key=load_index(ROOT/'client/fx.idx');emo,_=load_index(ROOT/'client/EmoTE.idx')
    old=read_asset(ROOT/'client',fx['Shop/S_Main'],'fx')
    assert struct.unpack_from('<3I',old)==(1,2,1)
    sources=[]
    def raw_asset(name,pack):
        idx=fx if pack=='fx' else emo
        sources.append({'name':name,'package':pack})
        return read_asset(ROOT/'client',idx[name],pack)
    def frame(raw,n=0):
        count,_,pages,_=struct.unpack_from('<4I',raw);n=min(n,count-1)
        return frame_from_sprite(raw,n),struct.unpack_from('<12i',raw,16+8*pages+48*n)
    def compose(bg,flag,char=2,bgFrame=0,flagFrame=0,border=None):
        canvas=Image.new('RGBA',(100,100))
        raw=raw_asset(f'Slot/Slot01_{bg:04d}','EmoTE');image,meta=frame(raw,bgFrame)
        canvas.alpha_composite(image,(-meta[0],-meta[1]))
        # A = face, B = body, C = head for Uni/Bazzi. Include each native
        # palette-adjusted layer as well as static art, instead of face-only A.
        for state in (['B','C','A'] if char in [2,6] else ['A']):
            for suffix in ['LayerAdjust','LayerStatic']:
                name=f'Character/C{char:02d}-WalkDown_{state}'+suffix
                if name not in fx:continue
                image,meta=frame(raw_asset(name,'fx'))
                canvas.alpha_composite(image,(27-meta[0],94-meta[1]))
        if flag:
            image,meta=frame(raw_asset(f'Slot/Slot04_{flag:04d}','EmoTE'),flagFrame)
            canvas.alpha_composite(image,(-meta[0],-meta[1]))
        if border:
            image,meta=frame(raw_asset(f'Slot/Slot07_{border:04d}','EmoTE'))
            canvas.alpha_composite(image,(-meta[0],-meta[1]))
        return canvas
    themes=[
        {'name':'缤纷世界','bg':289,'flag':272,'bgFrame':4,'flagFrame':1,'char':2},
        {'name':'老虎背景搭配','bg':290,'flag':273,'border':75,'char':6},
        {'name':'雪倾城','bg':297,'flag':282,'border':80,'char':2},
        {'name':'暗夜的妖媚','bg':287,'flag':270,'bgFrame':19,'char':0},
        {'name':'情侣星星','bg':128,'flag':108,'border':25,'char':1},
        {'name':'幽幽雪','bg':277,'flag':257,'border':69,'char':2},
        {'name':'图腾背景','bg':253,'flag':237,'char':6},
    ]
    font=ImageFont.truetype(r'C:\Windows\Fonts\msyhbd.ttc',18)
    small=ImageFont.truetype(r'C:\Windows\Fonts\msyh.ttc',11)
    sheet=Image.new('RGBA',(700,130),'#e8f7ff');sd=ImageDraw.Draw(sheet)
    for i,theme in enumerate(themes):
        img=compose(**{k:v for k,v in theme.items() if k!='name'});img.save(OUT/f'composition-{i+1}.png')
        sheet.alpha_composite(img,(i*100,0));sd.text((i*100+50,108),theme['name'],font=small,anchor='mt',fill='#143d70')
    sheet.save(OUT/'reference-compositions.png')
    image=frame_from_sprite(old).convert('RGBA');d=ImageDraw.Draw(image)
    # Retain the native purchase areas and draw four full decorative cards in
    # the banner, rather than six disembodied character sprite fragments.
    d.rectangle((20,14,487,168),fill='#063d79')
    d.text((34,20),'经典背景 · 搭配精选',font=font,fill='#ffffff')
    d.text((483,27),'背景 / 旗帜分售',font=small,anchor='rt',fill='#a8e4ff')
    for i,theme in enumerate(themes[:4]):
        x=34+i*115
        d.rounded_rectangle((x-2,48,x+102,151),radius=6,fill='#1768a8',outline='#54c6e6',width=1)
        tile=Image.open(OUT/f'composition-{i+1}.png').convert('RGBA')
        image.alpha_composite(tile,(x,49))
        d.text((x+50,152),theme['name'],font=small,anchor='mt',fill='#ffffff')
    image.save(OUT/'shop-home-preview.png')
    # Existing frame metadata and lower purchase hitboxes stay byte-identical.
    assert image.crop((0,170,508,454)).tobytes()==frame_from_sprite(old).convert('RGBA').crop((0,170,508,454)).tobytes()
    encoded=encode_legacy(image);new=old[:72]+struct.pack('<I',len(encoded))+encoded
    assert new[:72]==old[:72]
    base=(ROOT/'client/fx.idd').stat().st_size;before=fx['Shop/S_Main']
    fx['Shop/S_Main']={**before,'offset':base,'size':len(new)}
    (OUT/'fx.idx.before').write_bytes((ROOT/'client/fx.idx').read_bytes())
    (OUT/'fx.append.bin').write_bytes(new);write_index(OUT/'fx.idx.candidate',fx,key)
    (OUT/'manifest.json').write_text(json.dumps({'themes':themes,'sources':sources,'originalIddSize':base,'before':before,'sha256':hashlib.sha256(new).hexdigest(),'frameGeometryPreserved':True,'lowerControlsPreserved':True,'accountDataChanged':False},ensure_ascii=False,indent=2),encoding='utf8')
    print('Prepared seven complete reference-style compositions and four home showcase cards.')
if __name__=='__main__':main()
