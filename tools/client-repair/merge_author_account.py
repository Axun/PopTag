"""Copy the explicitly requested local author save into this candidate, retaining new items."""
from pathlib import Path
import hashlib,json,time
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'port-audit/author-account-merge'
def read(p):
    return dict(line.split('=',1) for line in p.read_text(encoding='latin1').splitlines() if '=' in line and not line.startswith('#'))
def main():
    name='潜在游鱼';key=hashlib.sha256(name.encode('utf-8')).hexdigest()+'.properties'
    source=ROOT.parent/'PopTag-monster-port/server/data/local-accounts'/key
    target=ROOT/'server/data/local-accounts'/key
    OUT.mkdir(exist_ok=False)
    old=target.read_bytes();original=source.read_bytes()
    (OUT/'test-account.before').write_bytes(old);(OUT/'formal-account.snapshot').write_bytes(original)
    test=read(target);formal=read(source);merged={**test,**formal}
    itemKeys={k for k in test.keys()|formal.keys() if k.startswith('item.')}
    for k in itemKeys:merged[k]=str(max(int(test.get(k,0)),int(formal.get(k,0))))
    assert len(itemKeys)<=128
    merged['economy.version']='1'
    receipts=(test.get('reward.receipts','')+','+formal.get('reward.receipts','')).split(',')
    merged['reward.receipts']=','.join(list(dict.fromkeys(x for x in receipts if x))[-128:])
    data=('#Merged local author record; private, never part of public package\n'+''.join(f'{k}={v}\n' for k,v in sorted(merged.items()))).encode('ascii')
    temporary=target.with_suffix('.merge.tmp');temporary.write_bytes(data)
    for i in range(10):
        try:temporary.replace(target);break
        except PermissionError:
            if i==9:raise
            time.sleep(.1)
    assert source.read_bytes()==original
    assert all(int(read(target)[k])>=int(v) for k,v in test.items() if k.startswith('item.'))
    report=dict(localAccountMerged=True,sourceUnchanged=True,publicPackageMustExcludeAccount=True,gold=int(merged['lucci']),experience=int(merged.get('experience',0)),ownedItemTypes=len(itemKeys))
    (OUT/'manifest.json').write_text(json.dumps(report,indent=2))
    print(report)
if __name__=='__main__':main()
