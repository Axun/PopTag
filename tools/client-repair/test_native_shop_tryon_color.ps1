$ErrorActionPreference='Stop'
if([IntPtr]::Size -ne 4){throw 'Requires 32-bit PowerShell'}
Add-Type -TypeDefinition @'
using System;using System.Collections.Generic;using System.Runtime.InteropServices;
public static class TryOnPaletteTest {
 [DllImport("kernel32.dll")]static extern IntPtr VirtualAlloc(IntPtr a,UIntPtr n,uint t,uint p);
 [DllImport("kernel32.dll")]static extern bool VirtualFree(IntPtr a,UIntPtr n,uint t);
 [UnmanagedFunctionPointer(CallingConvention.Cdecl)]delegate void Run();
 static IntPtr mem;static int checks;
 static IntPtr At(int x){return new IntPtr(mem.ToInt32()+x);}static int Get(int x){return Marshal.ReadInt32(At(x));}static void Put(int x,int n){Marshal.WriteInt32(At(x),n);}
 static byte[] Hex(string s){var b=new byte[s.Length/2];for(int i=0;i<b.Length;i++)b[i]=Convert.ToByte(s.Substring(i*2,2),16);return b;}
 static void Check(bool x,string s){if(!x)throw new Exception(s);checks++;}
 public static int Test(string hex,int[] offsets,int[] targets){
  mem=VirtualAlloc(IntPtr.Zero,(UIntPtr)0x10000,0x3000,0x40);if(mem==IntPtr.Zero)throw new Exception("Allocate test memory");
  try{
   var code=Hex(hex);for(int j=0;j<offsets.Length;j++){int dst=targets[j]==0x4d5f23?0x1000:targets[j]==0x5cec4a?0x1100:-1;Check(dst>=0,"known dependency");Array.Copy(BitConverter.GetBytes(dst-offsets[j]-4),0,code,offsets[j],4);}Marshal.Copy(code,0,mem,code.Length);
   var getter=Hex("8b8130060000c3");Marshal.Copy(getter,0,At(0x1000),getter.Length);
   var native=new List<byte>();Action<string> e=s=>native.AddRange(Hex(s));Action<int> n=v=>native.AddRange(BitConverter.GetBytes(v));
   e("9c60a3");n(At(0x3800).ToInt32());e("891d");n(At(0x3804).ToInt32());e("8915");n(At(0x3808).ToInt32());e("893d");n(At(0x380c).ToInt32());e("892d");n(At(0x3810).ToInt32());e("8935");n(At(0x3814).ToInt32());e("890d");n(At(0x3818).ToInt32());
   e("8b442420a3");n(At(0x381c).ToInt32());e("8b442428a3");n(At(0x3820).ToInt32());e("ff05");n(At(0x3824).ToInt32());e("619dc20400");Marshal.Copy(native.ToArray(),0,At(0x1100),native.Count);
   var w=new List<byte>();Action<string> emit=s=>w.AddRange(Hex(s));Action<int> val=v=>w.AddRange(BitConverter.GetBytes(v));
   emit("9c60b811111111bb22222222ba33333333bf44444444bd55555555be66666666b9");val(At(0x4000).ToInt32());emit("68460200009dff35");val(At(0x3830).ToInt32());emit("e8");val(-0x2000-w.Count-4);emit("619dc3");Marshal.Copy(w.ToArray(),0,At(0x2000),w.Count);
   var run=(Run)Marshal.GetDelegateForFunctionPointer(At(0x2000),typeof(Run));
   foreach(int selected in new int[]{0,1,2,3,4,5,6,7,8,9,-1})foreach(int bad in new int[]{0,1,3,8}){
    Put(0x75a4,selected);Put(0x3830,bad);Put(0x3824,0);run();int expected=selected>=0&&selected<=8?selected:0;
    Check(Get(0x3820)==expected,"Original shop setter receives actual selected palette, not item status");Check(Get(0x3824)==1,"Original setter called once");Check(Get(0x3818)==At(0x4000).ToInt32(),"Shop-stage this restored");Check(Get(0x3800)==0x11111111&&Get(0x3804)==0x22222222&&Get(0x3808)==0x33333333&&Get(0x380c)==0x44444444&&Get(0x3810)==0x55555555&&Get(0x3814)==0x66666666,"All incoming registers preserved");Check((Get(0x381c)&0x8d5)==(0x246&0x8d5),"Flags restored before native setter");Check(Get(0x75a4)==selected,"No paper-doll field mutation in adapter");
   }
  }finally{VirtualFree(mem,UIntPtr.Zero,0x8000);}return checks;
 }
}
'@
$audit=Join-Path $PSScriptRoot 'port-audit/shop-tryon-color'
$m=Get-Content -LiteralPath (Join-Path $audit 'manifest.json') -Raw|ConvertFrom-Json
$passed=[TryOnPaletteTest]::Test($m.code,[int[]]@($m.relative|ForEach-Object {$_.offset}),[int[]]@($m.relative|ForEach-Object {$_.target}))
@{passed=$passed;gameProcessTouched=$false}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $audit 'native-test-result.json')
Write-Output "$passed isolated native try-on palette assertions passed"
