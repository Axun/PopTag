using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Security.Cryptography;
using System.IO.Compression;
using System.Web.Script.Serialization;

namespace PopTagUpdate {
 public class FileEntry { public string path; public string sha256; public long size; }
 public class Bundle { public string asset; public string sha256; public long size; public List<FileEntry> files; }
 public class Manifest { public int schema; public string version; public string notes; public List<Bundle> bundles; }
 public class Change { public string path; public string before; public string after; }
 public class Journal { public string state; public string oldManifest; public List<Change> changes; }
 public class Engine {
  public readonly string Root, State;
  public static JavaScriptSerializer Json = new JavaScriptSerializer { MaxJsonLength=8000000 };
  public Engine(string root) { Root=Path.GetFullPath(root); State=Path.Combine(Root,".updater"); RejectLinks(Root); }
  public static string Hash(string path) { using(var f=File.OpenRead(path)) using(var h=SHA256.Create()) return BitConverter.ToString(h.ComputeHash(f)).Replace("-","").ToLowerInvariant(); }
  public static void RejectLinks(string p) {
   for(var d=new DirectoryInfo(Path.GetDirectoryName(Path.GetFullPath(p)));d!=null;d=d.Parent)
    if(d.Exists && (d.Attributes & FileAttributes.ReparsePoint)!=0) throw new IOException("不支持链接目录："+d.FullName);
   if((File.Exists(p)||Directory.Exists(p)) && (File.GetAttributes(p)&FileAttributes.ReparsePoint)!=0) throw new IOException("不支持链接文件："+p);
  }
  public static void ValidatePath(string p) {
   if(String.IsNullOrWhiteSpace(p) || p.Contains('\\') || p.StartsWith("/") || p.Contains(':') || p.Length>220) throw new InvalidDataException("更新路径无效");
   foreach(var part in p.Split('/')) {
    if(part=="." || part==".." || part.Length==0 || part.EndsWith(".") || part.EndsWith(" ") || part.IndexOfAny(Path.GetInvalidFileNameChars())>=0) throw new InvalidDataException("更新路径无效："+p);
    var n=part.Split('.')[0].ToUpperInvariant();
    if(new[]{"CON","PRN","AUX","NUL","COM1","COM2","COM3","COM4","COM5","COM6","COM7","COM8","COM9","LPT1","LPT2","LPT3","LPT4","LPT5","LPT6","LPT7","LPT8","LPT9"}.Contains(n)) throw new InvalidDataException("保留文件名");
   }
   bool allowed=p.StartsWith("client/",StringComparison.OrdinalIgnoreCase)||p.StartsWith("server/classes/",StringComparison.OrdinalIgnoreCase)||p.StartsWith("server/lib/",StringComparison.OrdinalIgnoreCase)||p.StartsWith("runtime/",StringComparison.OrdinalIgnoreCase)||p=="Start.ps1"||p=="Start.cmd"||p=="Stop.ps1"||p=="Stop.cmd"||p=="README.txt"||p=="SOURCES.md"||p=="RELEASE-NOTES.md"||System.Text.RegularExpressions.Regex.IsMatch(p,@"^server/[A-Za-z0-9_]+\.yaml$");
   var lower="/"+p.ToLowerInvariant()+"/";
   if(!allowed || new[]{"/local-accounts/","/logs/","/nmdAtA/".ToLowerInvariant(),"/ndadata/"}.Any(lower.Contains)) throw new InvalidDataException("更新禁止触碰该路径："+p);
  }
  public string Target(string relative) { ValidatePath(relative); var p=Path.GetFullPath(Path.Combine(Root,relative.Replace('/',Path.DirectorySeparatorChar))); if(!p.StartsWith(Root.TrimEnd('\\')+"\\",StringComparison.OrdinalIgnoreCase)) throw new InvalidDataException("路径越界"); RejectLinks(p);return p; }
  public static void Validate(Manifest m) {
   if(m==null || m.schema!=1 || String.IsNullOrWhiteSpace(m.version)||m.bundles==null||m.bundles.Count>100) throw new InvalidDataException("不支持的版本清单");
   var paths=new HashSet<string>(StringComparer.OrdinalIgnoreCase);var assets=new HashSet<string>(StringComparer.OrdinalIgnoreCase);long total=0;
   foreach(var b in m.bundles) {
    if(b==null || !System.Text.RegularExpressions.Regex.IsMatch(b.asset??"",@"^[a-z0-9-]+\.zip$")||!assets.Add(b.asset)||!ValidHash(b.sha256)||b.size<1||b.size>2000000000||b.files==null||b.files.Count==0) throw new InvalidDataException("组件清单无效");
    foreach(var f in b.files) { ValidatePath(f.path);if(!paths.Add(f.path)||!ValidHash(f.sha256)||f.size<0||f.size>2000000000)throw new InvalidDataException("文件清单无效");total+=f.size; }
   }
   if(paths.Count>20000 || total>10000000000L)throw new InvalidDataException("更新体积超出限制");
  }
  static bool ValidHash(string h) { return System.Text.RegularExpressions.Regex.IsMatch(h??"", "^[a-f0-9]{64}$"); }
  public bool Matches(FileEntry f) { var p=Target(f.path);return File.Exists(p)&&new FileInfo(p).Length==f.size&&Hash(p)==f.sha256; }
  public List<Bundle> Needed(Manifest m) { Validate(m);return m.bundles.Where(b=>b.files.Any(f=>!Matches(f))).ToList(); }
  public void Stage(Bundle b,string zip,string stage) {
   if(new FileInfo(zip).Length!=b.size || Hash(zip)!=b.sha256)throw new InvalidDataException("组件校验失败："+b.asset);
   var wanted=b.files.ToDictionary(f=>f.path,StringComparer.OrdinalIgnoreCase);var seen=new HashSet<string>(StringComparer.OrdinalIgnoreCase);
   using(var z=ZipFile.OpenRead(zip)) foreach(var e in z.Entries) {
    ValidatePath(e.FullName);
    FileEntry f;
    if(!wanted.TryGetValue(e.FullName,out f)||!seen.Add(e.FullName)||e.Length!=f.size||((e.ExternalAttributes>>16)&0xF000)==0xA000)throw new InvalidDataException("ZIP内容与清单不符");
    var p=Path.Combine(stage,f.path.Replace('/',Path.DirectorySeparatorChar)); RejectLinks(p);Directory.CreateDirectory(Path.GetDirectoryName(p));
    using(var s=e.Open())using(var d=File.Create(p)) { var bytes=new byte[81920];long count=0;int n;while((n=s.Read(bytes,0,bytes.Length))>0){count+=n;if(count>f.size)throw new InvalidDataException("文件超长");d.Write(bytes,0,n);} }
    if(Hash(p)!=f.sha256)throw new InvalidDataException("文件校验失败："+f.path);
   }
   if(seen.Count!=wanted.Count)throw new InvalidDataException("更新包缺失文件");
  }
  public static void AtomicText(string p,string value) { Directory.CreateDirectory(Path.GetDirectoryName(p));var t=p+".tmp";File.WriteAllText(t,value,new System.Text.UTF8Encoding(false));AtomicMove(t,p); }
  static void AtomicMove(string from,string to) { RejectLinks(to);Directory.CreateDirectory(Path.GetDirectoryName(to));if(File.Exists(to))File.Replace(from,to,null);else File.Move(from,to); }
  public void Apply(Manifest m,string stage,Action<int> afterFile=null) {
   Validate(m);RejectLinks(State);Directory.CreateDirectory(State);
   var journalPath=Path.Combine(State,"transaction.json");
   if(File.Exists(journalPath))throw new IOException("请先处理已有更新备份（回滚或保留当前版本）");
   var changes=new List<Change>(); var desired=m.bundles.SelectMany(b=>b.files).ToDictionary(f=>f.path,StringComparer.OrdinalIgnoreCase);
   foreach(var f in desired.Values)if(!Matches(f)) {
    var staged=Path.Combine(stage,f.path.Replace('/',Path.DirectorySeparatorChar));
    if(!File.Exists(staged)||new FileInfo(staged).Length!=f.size||Hash(staged)!=f.sha256)throw new InvalidDataException("暂存文件缺失或损坏："+f.path);
    var target=Target(f.path);changes.Add(new Change{path=f.path,before=File.Exists(target)?Hash(target):null,after=f.sha256});
   }
   var current=Path.Combine(State,"current.json");string old=File.Exists(current)?File.ReadAllText(current):null;
   if(old!=null) {
    var previous=Json.Deserialize<Manifest>(old);Validate(previous);
    foreach(var f in previous.bundles.SelectMany(b=>b.files)) if(!desired.ContainsKey(f.path)&&File.Exists(Target(f.path))) {
     if(Hash(Target(f.path))!=f.sha256)throw new IOException("已修改的旧文件不能自动移除："+f.path);
     changes.Add(new Change{path=f.path,before=f.sha256,after=null});
    }
   }
   var backup=Path.Combine(State,"backup");
   if(Directory.Exists(backup))throw new IOException("存在未处理的备份目录");
   Directory.CreateDirectory(backup);
   foreach(var c in changes)if(c.before!=null) {var d=Path.Combine(backup,c.path.Replace('/',Path.DirectorySeparatorChar));Directory.CreateDirectory(Path.GetDirectoryName(d));File.Copy(Target(c.path),d);if(Hash(d)!=c.before)throw new IOException("备份校验失败");}
   var j=new Journal{state="pending",oldManifest=old,changes=changes};AtomicText(journalPath,Json.Serialize(j));
   try {
    int n=0;
    foreach(var c in changes) {
     var target=Target(c.path);if(c.after==null)File.Delete(target);else { var t=Path.Combine(stage,c.path.Replace('/',Path.DirectorySeparatorChar));AtomicMove(t,target); }
     if(afterFile!=null)afterFile(++n);
    }
    AtomicText(current,Json.Serialize(m));j.state="complete";AtomicText(journalPath,Json.Serialize(j));
   } catch { Rollback();throw; }
  }
  public bool HasTransaction { get{return File.Exists(Path.Combine(State,"transaction.json"));} }
  public bool Pending { get { if(!HasTransaction)return false;return Json.Deserialize<Journal>(File.ReadAllText(Path.Combine(State,"transaction.json"))).state=="pending"; } }
  public void Rollback() {
   RejectLinks(State);var path=Path.Combine(State,"transaction.json");if(!File.Exists(path))throw new IOException("没有可回滚的更新");
   var j=Json.Deserialize<Journal>(File.ReadAllText(path));var backup=Path.Combine(State,"backup");
   foreach(var c in j.changes) {
    var p=Target(c.path);var actual=File.Exists(p)?Hash(p):null;
    if(actual!=c.before&&actual!=c.after&&actual!=null)throw new IOException("文件已另行修改，停止回滚："+c.path);
    if(c.before!=null) {var b=Path.Combine(backup,c.path.Replace('/',Path.DirectorySeparatorChar));RejectLinks(b);if(!File.Exists(b)||Hash(b)!=c.before)throw new IOException("备份不完整："+c.path);}
   }
   foreach(var c in j.changes.AsEnumerable().Reverse()) {
    var p=Target(c.path);
    if(c.before==null){if(File.Exists(p))File.Delete(p);}
    else {var b=Path.Combine(backup,c.path.Replace('/',Path.DirectorySeparatorChar));var t=b+".restore";File.Copy(b,t,true);AtomicMove(t,p);}
   }
   var current=Path.Combine(State,"current.json");if(j.oldManifest==null)File.Delete(current);else AtomicText(current,j.oldManifest);
   j.state="rolledback";AtomicText(path,Json.Serialize(j));ArchiveTransaction();
  }
  public void ArchiveTransaction() {
   if(Pending)throw new IOException("上次更新中断，请先回滚");
   if(!HasTransaction)return;
   var archive=Path.Combine(State,"history",DateTime.UtcNow.ToString("yyyyMMddHHmmssfff")+"-"+Guid.NewGuid().ToString("N"));
   Directory.CreateDirectory(archive);Directory.Move(Path.Combine(State,"backup"),Path.Combine(archive,"backup"));File.Move(Path.Combine(State,"transaction.json"),Path.Combine(archive,"transaction.json"));
  }
 }
}
