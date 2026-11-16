"""Design preview only. Writes PNG/JSON under design-previews; no game edits."""
from pathlib import Path
import sys,struct,json
from PIL import Image,ImageDraw,ImageFont
sys.path.insert(0,r'D:\GAME\work\PopTag-monster-port')
from audit_shop324_compat import CN057,load_index,read_asset
from legacy_sprite_codec import frame_from_sprite
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'design-previews/home-theme-options-v2-20261116'

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    fx,_=load_index(CN057/'fx.idx');char,_=load_index(CN057/'CharTE.idx');emo,_=load_index(ROOT/'client/EmoTE.idx')
    currentChar,_=load_index(ROOT/'client/CharTE.idx')
    defs=json.loads((ROOT/'port-audit/classic057-clothing/manifest.json').read_text(encoding='utf8'))['products']
    for line in (ROOT/'server/src/main/resources/data/local_extra_items.tsv').read_text(encoding='utf8').splitlines():
        f=line.split('\t')
        if len(f)==9 and f[1]=='19' and int(f[4]) in [1,5]:
            c={6:2,5:6}.get(int(f[3]))
            if c is not None:defs.append({'desc':f[6],'model':f'AvatarDeco/A{c:02d}_{int(f[4])*10:02d}_{int(f[5]):04d}'})
    def item(name):return next(i for i in defs if i['desc']==name)
    def raw(key,pack):
        if pack=='CharTE' and key not in char:
            return read_asset(ROOT/'client',currentChar[key],pack)
        folder=ROOT/'client' if pack=='EmoTE' else CN057
        idx={'fx':fx,'CharTE':char,'EmoTE':emo}[pack]
        return read_asset(folder,idx[key],pack)
    def frame(key,pack,n=0):
        r=raw(key,pack);count,v,pages,flags=struct.unpack_from('<4I',r);n=min(n,count-1)
        return frame_from_sprite(r,n),struct.unpack_from('<12i',r,16+8*pages+48*n)
    def outfit(canvas,character,cloth,hat,face):
        model={6:2,5:6}[character]
        # Replace the body and head with the actual matching clothing layers;
        # retain the character's own face. Do not pair clothes/hats by ordinal.
        for clothing in [item(cloth),item(hat)]:
            for suffix in ['LayerAdjust','LayerStatic']:
                key=clothing['model']+'_0'+suffix
                im,m=frame(key,'CharTE');canvas.alpha_composite(im,(27-m[0],94-m[1]))
        key=f'Character/C{model:02d}-WalkDown_ALayerStatic'
        im,m=frame(key,'fx');canvas.alpha_composite(im,(27-m[0],94-m[1]))
        for suffix in ['LayerAdjust','LayerStatic']:
            key=item(face)['model']+'_0'+suffix
            if key not in char and key not in currentChar:continue
            im,m=frame(key,'CharTE');canvas.alpha_composite(im,(27-m[0],94-m[1]))
    themes=[
        dict(title='小乖 · 罗密欧',character=6,cloth='罗密欧休闲装',hat='流行元素',face='爱兜风',bg=290,flag=273,border=75,
             setting='老虎背景搭配',components=['荣耀之王（虎纹背景）','禄山之爪（旗帜）','虎虎生威（边框）'],reason='用户指定：棕色发型与虎纹背景呼应。'),
        dict(title='小乖 · 明星',character=6,cloth='小乖明星装',hat='小乖明星帽',face='小乖偶尔也朋克',bg=128,flag=108,border=25,
             setting='情侣星星',components=['情侣星星右（背景）','情侣星星旗帜','情侣星星边框'],reason='用户指定：明星造型与彩色星星舞台呼应。'),
        dict(title='宝宝 · 暗夜伯爵',character=5,cloth='德古拉伯爵衣服',hat='猫王经典发型',face='德古拉伯爵脸型',bg=287,flag=270,border=None,
             setting='暗夜的妖媚',components=['暗夜的妖媚（背景）','黑山老妖（旗帜）'],reason='复古发型、伯爵衣服和脸部统一为暗夜主题，非木乃伊全包头。'),
        dict(title='宝宝 · 金甲天子',character=5,cloth='黄金甲战袍',hat='宝宝天子帽',face='真男人',bg=253,flag=237,border=None,
             setting='图腾',components=['图腾背景','图腾旗帜'],reason='金甲与皇冠式天子帽搭配金红龙图腾；保留脸部表情。'),
    ]
    font=ImageFont.truetype(r'C:\Windows\Fonts\msyhbd.ttc',22)
    small=ImageFont.truetype(r'C:\Windows\Fonts\msyh.ttc',15)
    caption=ImageFont.truetype(r'C:\Windows\Fonts\msyh.ttc',18)
    sheet=Image.new('RGB',(1240,605),'#e9f5ff');d=ImageDraw.Draw(sheet)
    d.text((30,18),'首页搭配候选 · 仅预览，尚未应用',font=font,fill='#104274')
    previews=[]
    for j,t in enumerate(themes):
        canvas=Image.new('RGBA',(100,100))
        im,m=frame(f'Slot/Slot01_{t["bg"]:04d}','EmoTE',19 if t['bg']==287 else 0);canvas.alpha_composite(im,(-m[0],-m[1]))
        outfit(canvas,t['character'],t['cloth'],t['hat'],t['face'])
        im,m=frame(f'Slot/Slot04_{t["flag"]:04d}','EmoTE');canvas.alpha_composite(im,(-m[0],-m[1]))
        if t['border']:
            im,m=frame(f'Slot/Slot07_{t["border"]:04d}','EmoTE');canvas.alpha_composite(im,(-m[0],-m[1]))
        canvas.save(OUT/f'set-{j+1}.png');previews.append(canvas)
        x=30+j*305
        d.rounded_rectangle((x-8,65,x+277,560),radius=12,fill='white',outline='#a6c8e0',width=1)
        sheet.paste(canvas.resize((250,250),Image.Resampling.NEAREST),(x+8,78),canvas.resize((250,250),Image.Resampling.NEAREST))
        d.text((x+132,344),t['title'],font=font,anchor='mt',fill='#123e68')
        d.text((x+132,380),t['setting'],font=caption,anchor='mt',fill='#137eb3')
        y=418
        for line in [t['cloth']+'＋'+t['hat'],t['face']+'（脸部）']+t['components']:
            d.text((x+6,y),line,font=small,fill='#37516c');y+=25
    d.text((30,576),'“经典稀有”为选品方向；未据此宣称官方稀有度或当年获取难度。',font=small,fill='#546a80')
    sheet.save(OUT/'four-outfit-options.png')
    # Build a clearly labelled layout mock-up from the untouched CN057 home art.
    base=frame_from_sprite(raw('Shop/S_Main','fx')).convert('RGBA')
    bubbles=[(13,'水玲珑'),(14,'七彩'),(16,'红色魔幻'),(17,'蓝色魔幻'),(18,'超级圣诞'),(28,'鬼眼')]
    for j,(style,name) in enumerate(bubbles):
        im,m=frame(f'Icon/Bomb{style:03d}icon','CharTE');im.thumbnail((52,60))
        x=34+j*75
        base.alpha_composite(im,(x+(62-im.width)//2,192+(62-im.height)//2))
    for j,im in enumerate(previews):
        # Four 94px native home preview windows; use a uniform 94px composition.
        tile=im.resize((94,94),Image.Resampling.NEAREST)
        base.alpha_composite(tile,(34+j*118,313))
    button,_=frame('Shop/S_BtBuy','fx')
    for j in range(6):base.alpha_composite(button,(46+j*75,266))
    for j in range(4):base.alpha_composite(button,(61+j*118,414))
    base.resize((1016,908),Image.Resampling.NEAREST).save(OUT/'home-layout-preview.png')
    report={'status':'PREVIEW ONLY; not installed','themes':themes,'bubbles':[{'style':s,'name':n,'artSource':'CN057'} for s,n in bubbles],'rarity':'Not officially verified','gameFilesChanged':False}
    (OUT/'choices.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print('Preview PNGs and choice list only; no resource, executable, server, or account changes.')
if __name__=='__main__':main()
