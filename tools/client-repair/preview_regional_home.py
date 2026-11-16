"""Preview only: original home, six classic bubbles, four unmodified region backgrounds."""
from pathlib import Path
import sys,struct,json,hashlib
from PIL import Image,ImageDraw,ImageFont
sys.path.insert(0,r'D:\GAME\work\PopTag-monster-port')
from audit_shop324_compat import CN057,load_index,read_asset
from legacy_sprite_codec import frame_from_sprite
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'design-previews/regional-home-20261116'

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    indices={p:load_index(CN057/(p+'.idx'))[0] for p in ['fx','CharTE','EmoTE']}
    def sprite(name,pack):return frame_from_sprite(read_asset(CN057,indices[pack][name],pack))
    base=sprite('Shop/S_Main','fx').convert('RGBA')
    original=base.copy()
    bubbles=[(41,'巧克力'),(14,'七彩'),(9,'绿色西瓜'),(27,'奶牛'),(32,'绿光妖精'),(28,'鬼眼')]
    candidate_icons=load_index(ROOT/'client/CharTE.idx')[0]
    for j,(style,_) in enumerate(bubbles):
        im=frame_from_sprite(read_asset(ROOT/'client',candidate_icons[f'Icon/Bomb{style:03d}icon'],'CharTE'));im.thumbnail((52,60));x=34+j*75
        base.alpha_composite(im,(x+(62-im.width)//2,192+(62-im.height)//2))
    regions=[('上海',5021,960060328),('广东',5022,960060329),('浙江',5025,960060332),('江苏',5026,960060333)]
    large=Image.new('RGB',(1080,400),'#eaf5ff');draw=ImageDraw.Draw(large)
    title=ImageFont.truetype(r'C:\Windows\Fonts\msyhbd.ttc',22)
    text=ImageFont.truetype(r'C:\Windows\Fonts\msyh.ttc',16)
    draw.text((22,15),'中国地区背景候选 · 不放人物 · 仅预览',font=title,fill='#123d6a')
    record=[]
    for j,(name,style,itemId) in enumerate(regions):
        key=f'Slot/Slot01_{style:04d}'
        raw=read_asset(CN057,indices['EmoTE'][key],'EmoTE');im=frame_from_sprite(raw)
        assert im.size==(94,94)
        # The images are the original single-background products, not invented
        # flag/frame bundles; no character or shared inventory is composited.
        base.alpha_composite(im,(34+j*118,313))
        display=im.resize((220,220),Image.Resampling.NEAREST);large.paste(display,(25+j*270,64),display)
        draw.text((135+j*270,301),name,font=title,anchor='mt',fill='#123d6a')
        draw.text((135+j*270,340),'057 原版独立背景',font=text,anchor='mt',fill='#47708c')
        record.append({'name':name,'style':style,'itemId':itemId,'source':str(CN057),'resource':key,'sha256':hashlib.sha256(raw).hexdigest(),'characterIncluded':False,'matchingFlagOrBorderFound':False})
    button=sprite('Shop/S_BtBuy','fx')
    for j in range(6):base.alpha_composite(button,(46+j*75,266))
    for j in range(4):base.alpha_composite(button,(61+j*118,414))
    assert base.crop((0,0,508,170)).tobytes()==original.crop((0,0,508,170)).tobytes()
    large.save(OUT/'four-regions.png');base.resize((1016,908),Image.Resampling.NEAREST).save(OUT/'home-layout-preview.png')
    (OUT/'choices.json').write_text(json.dumps({'status':'PREVIEW ONLY; not installed','regions':record,'bubbles':[{'style':s,'name':n} for s,n in bubbles],'topBanner':'Original CN057, pixels preserved','gameFilesChanged':False,'replacesAllCharacterOutfitDrafts':True},ensure_ascii=False,indent=2),encoding='utf8')
    print('Generated regional-only preview; no character graphics, game files, account edits or invented set components.')
if __name__=='__main__':main()
