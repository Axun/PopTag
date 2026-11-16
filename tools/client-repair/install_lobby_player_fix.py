"""Install verified player-tab art and clean only explicitly identified history rows."""
from pathlib import Path
import sys,json,hashlib
sys.path.insert(0,r'D:\GAME\work\PopTag-monster-port')
from audit_shop324_compat import load_index,read_asset
from rewrite_fx_index import write_index
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'port-audit/lobby-player-tabs'
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
    assert not (OUT/'installed.json').exists()
    manifest=json.loads((OUT/'manifest.json').read_text());client=ROOT/'client'
    idx,key=load_index(client/'fx.idx');name=manifest['asset']
    assert sha(read_asset(client,idx[name]))==manifest['beforeSha256']
    data=(OUT/'LB_Img.candidate').read_bytes();assert sha(data)==manifest['afterSha256']
    before=(client/'fx.idx').read_bytes();size=(client/'fx.idd').stat().st_size
    (OUT/'fx.idx.before').write_bytes(before)
    with (client/'fx.idd').open('ab') as f:f.write(data)
    idx[name]={**idx[name],'offset':size,'size':len(data)}
    try:
        write_index(client/'fx.idx',idx,key)
        actual,_=load_index(client/'fx.idx');assert read_asset(client,actual[name])==data
    except Exception:
        (client/'fx.idx').write_bytes(before)
        with (client/'fx.idd').open('r+b') as f:f.truncate(size)
        raise
    history=ROOT/'server/data/local-accounts/login-history/players.properties'
    removed=[]
    if history.exists():
        original=history.read_bytes();(OUT/'players.properties.before').write_bytes(original)
        p=dict(line.split('=',1) for line in original.decode('latin1').splitlines() if '=' in line and not line.startswith('#'))
        rows=[]
        knownTests={'lobby-level-init-test','local-players-test','nameplate-display-test'}
        for i in range(int(p.get('count',0))):
            fields={k:p[f'{i}.{k}'] for k in ['account','id','name']}
            account=fields['account'].encode('latin1').decode('unicode_escape')
            if account in knownTests or account=='半身王子':removed.append(account)
            else:rows.append(fields)
        text='#Local login history; test rows and hidden account removed\n'
        text+=''.join(f'{i}.{k}={value}\n' for i,row in enumerate(rows) for k,value in row.items())
        text+=f'count={len(rows)}\n';history.write_text(text,encoding='ascii')
    hidden=history.with_name('hidden-accounts.txt');existing=hidden.read_text(encoding='utf-8') if hidden.exists() else ''
    (OUT/'hidden-accounts.before.txt').write_text(existing,encoding='utf-8')
    hidden.write_text('\n'.join(dict.fromkeys(existing.splitlines()+['半身王子']))+'\n',encoding='utf-8')
    (OUT/'installed.json').write_text(json.dumps(dict(translatedFrames=[72,73,74,75],removedHistoryRows=removed,hiddenHistoryAccount='半身王子',walletInventoryAndExperienceFilesChanged=False,formalAccountImported=False,runtimeVerified=False),ensure_ascii=False,indent=2),encoding='utf-8')
    print('Installed Chinese 1P/2P tabs; removed',len(removed),'history rows; account saves unchanged')
if __name__=='__main__':main()
