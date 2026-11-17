import unittest,tempfile,json,zipfile
from pathlib import Path
from publish_update import prepare,sha,allowed

class PublisherTests(unittest.TestCase):
 def test_components_allow_skipping_versions_and_reuse_unchanged_assets(self):
  with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as d:
   base=Path(d);root=base/'game'
   for name in ['client/CA.exe','client/CharTE.idd','server/classes/bnbemu/MainKt.class','runtime/bin/java.exe','server/Config.yaml','server/EN_18_recv.yaml','server/EN_18_send.yaml','server/data/local-accounts/person.properties','logs/server.log']:
    p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'old')
   first=prepare(root,'v1.0.0',base/'v1')
   (root/'server/classes/bnbemu/MainKt.class').write_bytes(b'new')
   second=prepare(root,'v1.1.0',base/'v2')
   self.assertEqual(len(first['bundles']),len(second['bundles']))
   old={b['asset']:b for b in first['bundles']}
   changed=[b for b in second['bundles'] if b['asset'] not in old]
   self.assertEqual(len(changed),1);self.assertTrue(changed[0]['asset'].startswith('server-code-'))
   for b in second['bundles']:
    p=base/'v2'/b['asset'];self.assertEqual(sha(p),b['sha256'])
    with zipfile.ZipFile(p) as z:self.assertEqual(set(z.namelist()),{f['path'] for f in b['files']})
   entries=[f['path'] for b in second['bundles'] for f in b['files']]
   self.assertFalse(any('person' in p or 'server.log' in p for p in entries))
   for b in second['bundles']:
    if b['asset'] in old:self.assertEqual(b['sha256'],old[b['asset']]['sha256'])
 def test_reject_release_missing_login_configuration(self):
  with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as d:
   root=Path(d)/'game'
   for n in ['client/CA.exe','server/classes/bnbemu/MainKt.class','runtime/bin/java.exe']:
    p=root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'test')
   with self.assertRaises(ValueError):prepare(root,'v1.0.0',Path(d)/'out')
 def test_reject_invalid_publish_targets_and_private_paths(self):
  for path in ['server/data/local-accounts/x','client/NMDATA/account.dat','../x','client/x:ads','logs/server.log']:
   self.assertFalse(allowed(path),path)
  with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as d:
   root=Path(d)/'game';root.mkdir()
   with self.assertRaises(ValueError):prepare(root,'v1.0.0',root/'out')
   with self.assertRaises(ValueError):prepare(root,'v1.0.0',Path(d)/'out')

if __name__=='__main__':unittest.main()
