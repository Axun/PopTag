"""Stage classic CN057 clothing/hats in the isolated candidate, never live accounts."""
from pathlib import Path
import sys,json,hashlib,struct
from collections import Counter
sys.path.insert(0,r'D:\GAME\work\PopTag-monster-port')
from audit_shop324_compat import national_items,CN057,load_index,read_asset
from prepare_shop_expansion_bulk import registry
from prepare_cn057_shop_port import Reader
from legacy_sprite_codec import convert_sprite
from rewrite_fx_index import write_index

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'port-audit/classic057-clothing'
FIELDS=['itemId','category','name','skinId','targetCharId','param','desc','flags','status']
def sha(b):return hashlib.sha256(b).hexdigest()
def model_for(character,part,style):
    char={0:0,1:1,2:3,3:5,4:4,5:6,6:2,7:7}[character]
    suffix={10:21,11:41}.get(part,part*10)
    return f'AvatarDeco/A{char:02d}_{suffix:02d}_{style:04d}'

def main():
    OUT.mkdir(parents=True,exist_ok=False)
    data=ROOT/'server/src/main/resources/data';extra=data/'local_extra_items.tsv'
    raw=(data/'item_def_base.bin').read_bytes();reader=Reader(raw,8)
    current=[reader.item() for _ in range(struct.unpack_from('<H',raw,6)[0])]
    for line in extra.read_text(encoding='utf-8-sig').splitlines():
        if not line.strip():continue
        f=line.split('\t');current.append(dict(zip(FIELDS,[int(f[0]),int(f[1]),f[2],int(f[3]),int(f[4]),int(f[5]),f[6],int(f[7]),int(f[8])])))
    seen={(i['category'],i['skinId'],i['targetCharId'],i['param']) for i in current}
    ids={i['itemId'] for i in current}
    idx,models=registry(ROOT/'client','CharTE');src,_=load_index(CN057/'CharTE.idx')
    products=[];assets={};rejected=Counter()
    for i in sorted(national_items(),key=lambda x:x['itemId']):
        identity=(i['category'],i['skinId'],i['targetCharId'],i['param'])
        if i['category']!=19 or i['skinId'] not in range(8) or i['targetCharId'] not in [10,11] or identity in seen:continue
        model=model_for(i['skinId'],i['targetCharId'],i['param']);icon='Icon/'+model.split('/')[1]+'icon'
        keys=[k for k in idx if k.startswith(model+'_')]+[icon]
        if model not in models or len(keys)<3 or any(k not in src or k not in idx for k in keys):rejected['missing registered model or 057 action/icon']+=1;continue
        converted={};valid=True
        for k in keys:
            old=read_asset(ROOT/'client',idx[k],'CharTE');raw=read_asset(CN057,src[k],'CharTE')
            if struct.unpack_from('<I',old)[0]!=struct.unpack_from('<I',raw)[0]:valid=False;break
            converted[k]=convert_sprite(raw)[0]
        if not valid:rejected['frame count mismatch']+=1;continue
        item={**i,'itemId':980_000_000+i['itemId'],'desc':i['desc'].strip(),'flags':0,'status':1}
        assert item['itemId'] not in ids and '\t' not in item['desc'] and '\n' not in item['desc']
        products.append({**item,'sourceItemId':i['itemId'],'source':str(CN057),'nameSource':'CN324 matching definition','model':model,'assets':keys,'price':220000 if i['targetCharId']==10 else 180000})
        seen.add(identity);ids.add(item['itemId']);assets.update(converted)
    assert len(products)>=100
    files={'items':extra,'names':ROOT/'server/src/main/resources/localization/zh-CN-official-item-names.tsv','prices':data/'local-shop-prices.tsv'}
    for label,p in files.items():
        (OUT/(label+'.before.tsv')).write_bytes(p.read_bytes())
        added=''.join(('\t'.join(str(i[k]) for k in FIELDS) if label=='items' else f'{i["itemId"]}\t'+(i['desc'] if label=='names' else str(i['price'])))+'\n' for i in products)
        (OUT/(label+'.candidate.tsv')).write_text(p.read_text(encoding='utf-8-sig').rstrip()+'\n'+added,encoding='utf8')
    entries,key=load_index(ROOT/'client/CharTE.idx');base=(ROOT/'client/CharTE.idd').stat().st_size;append=bytearray();changes=[]
    for name,new in sorted(assets.items()):
        before=entries[name]
        if new==read_asset(ROOT/'client',before,'CharTE'):continue
        after={**before,'offset':base+len(append),'size':len(new),'key':src[name]['key']}
        entries[name]=after;append.extend(new);changes.append({'name':name,'before':before,'after':after,'sha256':sha(new)})
    (OUT/'CharTE.idx.before').write_bytes((ROOT/'client/CharTE.idx').read_bytes())
    (OUT/'CharTE.append.bin').write_bytes(append);write_index(OUT/'CharTE.idx.candidate',entries,key)
    report={'products':products,'counts':dict(Counter(f'{i["skinId"]}:{i["targetCharId"]}' for i in products)),'rejected':dict(rejected),'originalIddSize':base,'changes':changes,'clientExeChanged':False,'accountDataChanged':False}
    (OUT/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'products':len(products),'counts':report['counts'],'changedAssets':len(changes),'appendBytes':len(append),'rejected':dict(rejected)}))
if __name__=='__main__':main()
