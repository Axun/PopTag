"""Install audited cosmetic definitions and only the changed registered sprites."""
from prepare_shop_expansion_v2 import ROOT,OUT,sha
from idd_assets import load_index,read_asset
import json

def main():
    assert not (OUT/'installed.json').exists()
    files={'items':ROOT/'server/src/main/resources/data/local_extra_items.tsv',
           'prices':ROOT/'server/src/main/resources/data/local-shop-prices.tsv',
           'names':ROOT/'server/src/main/resources/localization/zh-CN-official-item-names.tsv'}
    for k,p in files.items():assert p.read_bytes()==(OUT/f'{k}.before.tsv').read_bytes()
    for package in ['CharTE','EmoTE']:
        idx=ROOT/'client'/f'{package}.idx';idd=ROOT/'client'/f'{package}.idd'
        m=json.loads((OUT/f'{package}.manifest.json').read_text(encoding='utf-8'))
        assert idx.read_bytes()==(OUT/f'{package}.idx.before').read_bytes()
        assert idd.stat().st_size==m['originalIddSize']
        before,_=load_index(idx);after,_=load_index(OUT/f'{package}.idx.candidate')
        changed={r['name'] for r in m['changes']}
        assert list(before)==list(after) and all(before[n]==after[n] for n in before if n not in changed)
        assert all(before[n]==after[n] for n in before if n.startswith('ObjectTable/'))
    executable=sha((ROOT/'client/CA.exe').read_bytes())
    touched=[]
    try:
        for package in ['CharTE','EmoTE']:
            m=json.loads((OUT/f'{package}.manifest.json').read_text(encoding='utf-8'))
            if not m['changes']:continue
            touched.append((package,m['originalIddSize']))
            with (ROOT/'client'/f'{package}.idd').open('ab') as f:f.write((OUT/f'{package}.append.bin').read_bytes())
            (ROOT/'client'/f'{package}.idx').write_bytes((OUT/f'{package}.idx.candidate').read_bytes())
            idx,_=load_index(ROOT/'client'/f'{package}.idx')
            for row in m['changes']:assert sha(read_asset(ROOT/'client',idx[row['name']],package))==row['sha256']
        for k,p in files.items():p.write_bytes((OUT/f'{k}.candidate.tsv').read_bytes())
        assert sha((ROOT/'client/CA.exe').read_bytes())==executable
    except Exception:
        for k,p in files.items():p.write_bytes((OUT/f'{k}.before.tsv').read_bytes())
        for package,size in touched:
            (ROOT/'client'/f'{package}.idx').write_bytes((OUT/f'{package}.idx.before').read_bytes())
            with (ROOT/'client'/f'{package}.idd').open('r+b') as f:f.truncate(size)
        raise
    (OUT/'installed.json').write_text(json.dumps({'products':38,'accountDataChanged':False,
        'clientExeSha256':executable,'registryOrderPreserved':True,'gameplayVerification':'pending'},indent=2))
    print('Installed 38 products; six nameplate icons adapted; executable and object registry unchanged.')
if __name__=='__main__':main()
