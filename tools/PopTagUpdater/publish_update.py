"""Prepare GitHub Release components from an isolated release tree; never upload.

Usage: python publish_update.py --root RELEASE_TREE --version v0.1.0 --out NEW_DIR
Every published release carries a full manifest and self-contained components,
so players can skip versions. Unchanged components keep stable content names.
"""
import argparse, hashlib, json, re, zipfile
from pathlib import Path

def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def allowed(name):
    p=Path(name)
    if p.is_absolute() or '\\' in name or ':' in name or any(x in ('.','..','') for x in name.split('/')):return False
    if any(x.lower() in ('local-accounts','logs','nmdata','ndadata','.updater') for x in p.parts):return False
    return name.startswith(('client/','server/classes/','server/lib/','runtime/')) or name in ('Start.cmd','Start.ps1','Stop.cmd','Stop.ps1','README.txt','SOURCES.md','RELEASE-NOTES.md') or bool(re.fullmatch(r'server/[A-Za-z0-9_]+\.yaml',name))

def prepare(root,version,out,notes=''):
    root=root.resolve();out=out.resolve()
    if out==root or root in out.parents:raise ValueError('Output must be outside the release tree')
    if out.exists():raise ValueError('Use a new output directory to preserve old releases')
    if not re.fullmatch(r'v[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9.-]+)?',version):raise ValueError('Use a version such as v0.1.0')
    groups={}
    for path in sorted(root.rglob('*')):
        if path.is_symlink():raise ValueError('Symlinks are not allowed')
        if not path.is_file():continue
        name=path.relative_to(root).as_posix()
        if not allowed(name):continue
        if path.suffix.lower() in ('.log','.pcap','.dmp','.bak'):raise ValueError('Unexpected diagnostic file: '+name)
        if name.startswith('runtime/'):group='runtime'
        elif name.startswith('server/classes/'):group='server-code'
        elif name.startswith('server/lib/'):group='server-libraries'
        elif name.startswith('client/') and path.suffix.lower()=='.idd':group='resource-'+path.stem.lower()
        elif name.startswith('client/'):group='client-core'
        else:group='launcher-support'
        groups.setdefault(group,[]).append((path,{'path':name,'sha256':sha(path),'size':path.stat().st_size}))
    required=['client/CA.exe','server/classes/bnbemu/MainKt.class','runtime/bin/java.exe']
    names={entry['path'] for group in groups.values() for _,entry in group}
    if any(p not in names for p in required):raise ValueError('Not a complete release tree')
    out.mkdir(parents=True)
    manifest={'schema':1,'version':version,'notes':notes,'bundles':[]}
    for group,entries in sorted(groups.items()):
        files=[e for _,e in entries]
        identity=hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()[:16]
        asset=group+'-'+identity+'.zip';dest=out/asset
        with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=3,allowZip64=True) as archive:
            for path,entry in entries:
                # Fixed timestamps make identical input produce identical bundles.
                info=zipfile.ZipInfo(entry['path'],(2020,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
                with path.open('rb') as src,archive.open(info,'w',force_zip64=True) as target:
                    import shutil
                    shutil.copyfileobj(src,target)
                if sha(path)!=entry['sha256']:raise RuntimeError('Source changed during packaging: '+str(path))
        manifest['bundles'].append({'asset':asset,'sha256':sha(dest),'size':dest.stat().st_size,'files':files})
    (out/'update-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'UPLOAD.txt').write_text('Upload every ZIP plus update-manifest.json to the SAME GitHub Release.\nTag must be '+version+'. Drafts and prereleases are ignored by the stable updater.\nPublish only when every asset is uploaded. Keep a complete package for new players.\n',encoding='utf-8')
    return manifest

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--root',type=Path,required=True);a.add_argument('--out',type=Path,required=True);a.add_argument('--version',required=True);a.add_argument('--notes',default='')
    args=a.parse_args();m=prepare(args.root,args.version,args.out,args.notes)
    print('Prepared',len(m['bundles']),'components;',sum(len(b['files']) for b in m['bundles']),'files. Nothing uploaded.')
