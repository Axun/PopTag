"""Prepare a bounded set of registered national cosmetics, without touching live files."""
from audit_shop324_compat import *
from legacy_sprite_codec import convert_sprite,frame_from_sprite
from rewrite_fx_index import write_index
from PIL import Image,ImageDraw,ImageFont
from collections import Counter

OUT=ROOT/'port-audit/shop-expansion-20261116-final'
FIELDS=['itemId','category','name','skinId','targetCharId','param','desc','flags','status']
sha=lambda b:hashlib.sha256(b).hexdigest()

def registry(folder,package):
    idx,_=load_index(folder/f'{package}.idx')
    e=idx[next(k for k in idx if k.startswith('ObjectTable/'))]
    raw=decrypt(read_asset(folder,e,package),e['flags']);r=Reader(raw)
    models=set()
    for _ in range(r.number('I')):models.add(r.string());r.number('I')
    return idx,models

def canonical(i):
    if i['category']==10:return (10,i['targetCharId'],i['skinId'])
    if i['category']==18:return (18,i['skinId'])
    if i['category']==19:return (19,i['skinId'],i['targetCharId'],i['param'])
    return identity(i)

def layout(i):
    cat=i['category']
    if cat==19 and i['skinId'] in [5,6] and i['targetCharId'] in [1,2,3]:
        m={5:6,6:2}[i['skinId']]
        model=f'AvatarDeco/A{m:02d}_{i["targetCharId"]}0_{i["param"]:04d}'
        return 'CharTE',model,'Icon/'+model.split('/')[1]+'icon'
    if cat==10 and i['targetCharId'] in [1,4]:
        model=f'Slot/Slot{i["targetCharId"]:02d}_{i["skinId"]:04d}'
        return 'EmoTE',model,'Icon/'+model.split('/')[1]+'icon'
    if cat==18 and i['skinId']>0:
        return 'EmoTE',f'IDDeco/IDDeco_C{i["skinId"]:03d}',f'Icon/ItemIDDeco_C{i["skinId"]:03d}'

def first_visible(raw):
    nf,np=struct.unpack_from('<I',raw)[0],struct.unpack_from('<I',raw,8)[0]
    for f in range(min(nf,32)):
        fields=struct.unpack_from('<12i',raw,16+8*np+48*f)
        if fields[3]<0:continue
        im=frame_from_sprite(raw,f)
        if im.getbbox():return im
    raise ValueError('No visible icon')

def main():
    OUT.mkdir(exist_ok=False)
    current=current_items();national=national_items()
    indices={};models={};source={}
    for package in ['CharTE','EmoTE']:
        indices[package],models[package]=registry(ROOT/'client',package)
        source[package]={}
        for folder in [CN057,CN324]:source[package][folder]=load_index(folder/f'{package}.idx')[0]
    known={canonical(i) for i in current};ids={i['itemId'] for i in current}
    # Deduplicate actual icon pixels as well as definition/model identities.
    icons=set()
    def icon_signature(raw):
        im=first_visible(raw).convert('RGBA')
        return sha(struct.pack('<II',*im.size)+im.tobytes())
    for i in current:
        lay=layout(i)
        if lay and lay[2] in indices[lay[0]]:
            try:icons.add((i['category'],icon_signature(read_asset(ROOT/'client',indices[lay[0]][lay[2]],lay[0]))))
            except (AssertionError,ValueError,IndexError):pass
    groups=[(f'avatar-{c}-{part}',lambda i,c=c,part=part:i['category']==19 and i['skinId']==c and i['targetCharId']==part,n)
            for c in [6,5] for part,n in [(2,6),(3,4),(1,4)]]
    groups += [('background',lambda i:i['category']==10 and i['targetCharId']==1,6),
               ('flag',lambda i:i['category']==10 and i['targetCharId']==4,6),
               ('nameplate',lambda i:i['category']==18,6)]
    products=[];assets={'CharTE':{},'EmoTE':{}};rejected=Counter();previews=[]
    for group,accept,limit in groups:
        added=0
        for original in sorted((i for i in national if accept(i)),key=lambda i:i['itemId']):
            item={**original,'desc':original['desc'].strip()}
            if canonical(item) in known:continue
            if not any('\u3400'<=c<='\u9fff' for c in item['desc']) or any(c in item['desc'] for c in ['\ufffd','\t','\n']):continue
            lay=layout(item)
            if not lay:continue
            package,model,icon=lay;idx=indices[package]
            if model not in models[package] or icon not in idx:rejected['unregistered model/icon']+=1;continue
            if package=='CharTE':keys=[k for k in idx if k==icon or k.startswith(model+'_')]
            else:keys=[k for k in idx if k==icon or k==model or k.startswith(model+'_') or (item['category']==18 and k in [model+'G',model.replace('IDDeco/','IDDeco/Shop_')])]
            if len(keys)<2:rejected['incomplete animation']+=1;continue
            sourceKeys={k:k for k in keys}
            if item['category']==18:
                # CN324 uses four digits and a lowercase d in its icon path;
                # retain the legacy three-digit registry keys on the destination.
                stem=f'C{item["skinId"]:03d}';modernStem=f'C{item["skinId"]:04d}'
                sourceKeys={k:k.replace(stem,modernStem).replace('ItemIDDeco_','ItemIDdeco_') for k in keys}
            chosen=CN324 if all(sourceKeys[k] in source[package][CN324] for k in keys) else None
            if chosen is None:rejected['missing national actions']+=1;continue
            converted={};pages=0
            try:
                for key in keys:
                    old=read_asset(ROOT/'client',idx[key],package)
                    src=source[package][chosen][sourceKeys[key]]
                    if src['flags'] or idx[key]['flags']:raise ValueError('Encrypted sprite')
                    raw=read_asset(chosen,src,package)
                    if len(raw)<16 or struct.unpack_from('<I',raw,4)[0]!=2:raise ValueError('Unsupported sprite')
                    if struct.unpack_from('<I',old)[0]!=struct.unpack_from('<I',raw)[0]:raise ValueError('Native frame count differs')
                    fixed,audits=convert_sprite(raw);pages+=len(audits);converted[key]=fixed
                sig=(item['category'],icon_signature(converted[icon]))
                if sig in icons:rejected['duplicate icon pixels']+=1;continue
            except (AssertionError,ValueError,IndexError,struct.error) as e:
                rejected[str(e)[:75] or type(e).__name__]+=1;continue
            newId=970_000_000+item['itemId'] if item['category']==19 else 960_000_000+item['itemId']
            if newId in ids:rejected['id collision']+=1;continue
            p={**item,'itemId':newId,'sourceItemId':item['itemId'],'source':str(chosen),'group':group,'assets':keys,
               'sourceKeys':sourceKeys,'package':package,'model':model,'icon':icon,'convertedPages':pages,'flags':0}
            if item['category']==18:p['name']=icon
            frames=max(struct.unpack_from('<I',v)[0] for k,v in converted.items() if k!=icon)
            tier=0 if frames<8 else 1 if frames<16 else 2 if frames<32 else 3
            if item['category']==19:
                # Walking/directional frame counts are not cosmetic rarity.
                tier=1 if item['targetCharId'] in [2,3] else 0
                if any(w in item['desc'] for w in ['炫','星光','闪耀','水晶']):tier=2
            p.update(price=[120000,220000,380000,680000][tier],tier=['普通','精致','华丽','典藏'][tier])
            for k,v in converted.items():
                if k in assets[package]:assert assets[package][k]==v
                assets[package][k]=v
            products.append(p);ids.add(newId);known.add(canonical(item));icons.add(sig)
            previews.append((p,first_visible(converted[icon])));added+=1
            if added==limit:break
        print('Prepared group',group,added,'/',limit,flush=True)
    assert len(products)>=28,'Do not install an empty or mostly incompatible batch'
    for package,entries in indices.items():
        _,key=load_index(ROOT/'client'/f'{package}.idx');base=(ROOT/'client'/f'{package}.idd').stat().st_size
        append=bytearray();changes=[];order=list(entries)
        for name,raw in sorted(assets[package].items()):
            old=read_asset(ROOT/'client',entries[name],package)
            if old==raw:continue
            before=dict(entries[name]);after={**before,'offset':base+len(append),'size':len(raw)}
            entries[name]=after;append.extend(raw)
            changes.append({'name':name,'before':before,'after':after,'sha256':sha(raw)})
        assert list(entries)==order
        (OUT/f'{package}.idx.before').write_bytes((ROOT/'client'/f'{package}.idx').read_bytes())
        (OUT/f'{package}.append.bin').write_bytes(append);write_index(OUT/f'{package}.idx.candidate',entries,key)
        (OUT/f'{package}.manifest.json').write_text(json.dumps({'originalIddSize':base,'changes':changes},ensure_ascii=False,indent=2),encoding='utf-8')
    for label,path in [('items',DATA/'local_extra_items.tsv'),('names',ROOT/'server/src/main/resources/localization/zh-CN-official-item-names.tsv'),('prices',DATA/'local-shop-prices.tsv')]:
        old=path.read_bytes();(OUT/f'{label}.before.tsv').write_bytes(old)
        lines=['\t'.join(str(i[k]) for k in FIELDS) if label=='items' else f'{i["itemId"]}\t{i["desc"]}' if label=='names' else f'{i["itemId"]}\t{i["price"]}\t{i["tier"]}\t{i["desc"]}' for i in products]
        (OUT/f'{label}.candidate.tsv').write_text(old.decode('utf-8-sig').rstrip()+'\n'+'\n'.join(lines)+'\n',encoding='utf-8')
    sheet=Image.new('RGB',(1440,150*((len(previews)+5)//6)),(235,242,250));draw=ImageDraw.Draw(sheet);font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',14)
    for n,(p,im) in enumerate(previews):
        x=n%6*240;y=n//6*150;im.thumbnail((200,92));sheet.paste(im,(x+(240-im.width)//2,y+4),im)
        draw.text((x+8,y+100),p['desc'][:15],font=font,fill=(15,35,65));draw.text((x+8,y+123),str(p['price'])+' 金币',font=font,fill=(40,70,100))
    sheet.save(OUT/'preview.png')
    (OUT/'manifest.json').write_text(json.dumps({'products':products,'counts':dict(Counter(p['group'] for p in products)),
        'rejected':dict(rejected),'clientExeChanged':False,'accountDataChanged':False,'visualGameplayVerification':'pending'},ensure_ascii=False,indent=2),encoding='utf-8')
    print('Total new products:',len(products),flush=True)

if __name__=='__main__':main()
