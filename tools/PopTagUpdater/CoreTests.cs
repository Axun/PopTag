using System;
using System.IO;
using System.IO.Compression;
using System.Collections.Generic;
using System.Linq;
using PopTagUpdate;
class CoreTests {
 static int count;static string work;
 static void Assert(bool b,string name){if(!b)throw new Exception("FAIL: "+name);count++;Console.WriteLine("PASS "+name);}
 static void Reject(Action a,string name){bool rejected=false;try{a();}catch{rejected=true;}Assert(rejected,name);}
 static string NewRoot(){var p=Path.Combine(work,Guid.NewGuid().ToString("N"));Directory.CreateDirectory(p);return p;}
 static void Write(string root,string p,string text){var target=Path.Combine(root,p);Directory.CreateDirectory(Path.GetDirectoryName(target));File.WriteAllText(target,text);}
 static Manifest Make(string root,Dictionary<string,string> values){
  var files=new List<FileEntry>();foreach(var kv in values){Write(root,"input/"+kv.Key,kv.Value);var p=Path.Combine(root,"input",kv.Key);files.Add(new FileEntry{path=kv.Key,sha256=Engine.Hash(p),size=new FileInfo(p).Length});}
  var zip=Path.Combine(root,"package.zip");using(var a=ZipFile.Open(zip,ZipArchiveMode.Create))foreach(var f in files)a.CreateEntryFromFile(Path.Combine(root,"input",f.path),f.path);
  return new Manifest{schema=1,version="v1.0.0",notes="test",bundles=new List<Bundle>{new Bundle{asset="test-package.zip",sha256=Engine.Hash(zip),size=new FileInfo(zip).Length,files=files}}};
 }
 static void Stage(Engine e,Manifest m,string fixture,string stage){e.Stage(m.bundles[0],Path.Combine(fixture,"package.zip"),stage);}
 static void Main(string[] args){
  work=Path.GetFullPath(args[0]);Directory.CreateDirectory(work);
  if(args.Length>1) {
   var published=Path.GetFullPath(args[1]);var parsed=Engine.Json.Deserialize<Manifest>(File.ReadAllText(Path.Combine(published,"update-manifest.json")));Engine.Validate(parsed);
   var installed=NewRoot();var ie=new Engine(installed);var staged=Path.Combine(installed,"stage");
   foreach(var b in parsed.bundles)ie.Stage(b,Path.Combine(published,b.asset),staged);
   ie.Apply(parsed,staged);
   Assert(ie.Needed(parsed).Count==0,"Python manifest to native installer interoperability");
   Assert(File.Exists(Path.Combine(installed,"client/CA.exe")),"install all components from one release");
   ie.Rollback();Assert(!File.Exists(Path.Combine(installed,"client/CA.exe")),"cross-language installation rollback");
  }
  var root=NewRoot();var fixture=NewRoot();var e=new Engine(root);Write(root,"client/a.txt","old");Write(root,"server/data/local-accounts/account.properties","coins=123");
  var m=Make(fixture,new Dictionary<string,string>{{"client/a.txt","new"},{"client/b.txt","added"}});Assert(e.Needed(m).Count==1,"select changed component");
  var stage=Path.Combine(root,"stage");Stage(e,m,fixture,stage);e.Apply(m,stage);
  Assert(File.ReadAllText(Path.Combine(root,"client/a.txt"))=="new","replace changed file");
  Assert(File.ReadAllText(Path.Combine(root,"server/data/local-accounts/account.properties"))=="coins=123","preserve player save");
  Assert(e.Needed(m).Count==0,"skip identical components");Assert(e.HasTransaction&&!e.Pending,"record completed backup");
  e.Rollback();Assert(File.ReadAllText(Path.Combine(root,"client/a.txt"))=="old","rollback original");Assert(!File.Exists(Path.Combine(root,"client/b.txt")),"rollback new file");Assert(!e.HasTransaction,"archive restored transaction");

  root=NewRoot();e=new Engine(root);Write(root,"client/a.txt","before");stage=Path.Combine(root,"stage");Stage(e,m,fixture,stage);
  Reject(()=>e.Apply(m,stage,n=>{if(n==1)throw new IOException("simulated interruption");}),"failed install reports failure");
  Assert(File.ReadAllText(Path.Combine(root,"client/a.txt"))=="before","failed install automatically restores files");Assert(!e.Pending,"failed install leaves no pending transaction");

  var corrupt=Path.Combine(fixture,"corrupt.zip");File.Copy(Path.Combine(fixture,"package.zip"),corrupt);File.AppendAllText(corrupt,"bad");
  Reject(()=>e.Stage(m.bundles[0],corrupt,Path.Combine(root,"bad-stage")),"reject corrupt download before installation");
  foreach(var p in new[]{"../escape","client/../../escape","server/data/local-accounts/x","client/NMDATA/account.dat","client/CA.exe:stream","/client/x","client/CON.txt","client/x.","client\\x","logs/x"})Reject(()=>Engine.ValidatePath(p),"reject forbidden path "+p);
  var dup=Engine.Json.Deserialize<Manifest>(Engine.Json.Serialize(m));dup.bundles[0].files.Add(dup.bundles[0].files[0]);Reject(()=>Engine.Validate(dup),"reject duplicate path");
  var hostile=Path.Combine(fixture,"hostile.zip");using(var z=ZipFile.Open(hostile,ZipArchiveMode.Create)){var entry=z.CreateEntry("../outside.txt");using(var w=new StreamWriter(entry.Open()))w.Write("bad");}
  var hb=new Bundle{asset="bad.zip",sha256=Engine.Hash(hostile),size=new FileInfo(hostile).Length,files=m.bundles[0].files};
  Reject(()=>e.Stage(hb,hostile,Path.Combine(root,"hostile")),"reject ZIP traversal");Assert(!File.Exists(Path.Combine(root,"outside.txt")),"ZIP cannot write outside staging");

  root=NewRoot();e=new Engine(root);Write(root,"client/a.txt","old");stage=Path.Combine(root,"stage");Stage(e,m,fixture,stage);e.Apply(m,stage);Write(root,"client/a.txt","user-edited");
  Reject(e.Rollback,"stop rollback on later user modification");Assert(File.ReadAllText(Path.Combine(root,"client/a.txt"))=="user-edited","keep user edit after conflict");Assert(File.ReadAllText(Path.Combine(root,"client/b.txt"))=="added","rollback preflight avoids partial restoration");

  root=NewRoot();e=new Engine(root);stage=Path.Combine(root,"stage1");Stage(e,m,fixture,stage);e.Apply(m,stage);e.ArchiveTransaction();
  var fixture2=NewRoot();var m2=Make(fixture2,new Dictionary<string,string>{{"client/a.txt","newer"}});m2.version="v2.0.0";stage=Path.Combine(root,"stage2");Stage(e,m2,fixture2,stage);e.Apply(m2,stage);
  Assert(!File.Exists(Path.Combine(root,"client/b.txt")),"remove obsolete tracked application file");
  e.Rollback();Assert(File.ReadAllText(Path.Combine(root,"client/b.txt"))=="added","rollback removed application file");
  Assert(File.ReadAllText(Path.Combine(root,".updater/current.json")).Contains("v1.0.0"),"rollback restores version index");

  root=NewRoot();e=new Engine(root);stage=Path.Combine(root,"stage");Stage(e,m,fixture,stage);e.Apply(m,stage);
  var jp=Path.Combine(root,".updater/transaction.json");var journal=Engine.Json.Deserialize<Journal>(File.ReadAllText(jp));journal.state="pending";File.WriteAllText(jp,Engine.Json.Serialize(journal));
  var reopened=new Engine(root);Assert(reopened.Pending,"detect interrupted transaction after restart");reopened.Rollback();Assert(!File.Exists(Path.Combine(root,"client/a.txt")),"recover interrupted installation after restart");
  Console.WriteLine("ALL PASSED: "+count+" assertions");
 }
}
