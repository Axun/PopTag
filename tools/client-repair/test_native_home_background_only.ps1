$ErrorActionPreference='Stop'
if([IntPtr]::Size -ne 4){throw 'Requires 32-bit PowerShell'}
Add-Type -TypeDefinition @'
using System;using System.Collections.Generic;using System.Runtime.InteropServices;
public static class HomeBackgroundTest {
 [DllImport("kernel32.dll")]static extern IntPtr VirtualAlloc(IntPtr a,UIntPtr n,uint t,uint p);
 [DllImport("kernel32.dll")]static extern bool VirtualFree(IntPtr a,UIntPtr n,uint t);
 [UnmanagedFunctionPointer(CallingConvention.Cdecl)]delegate void Run();
 static IntPtr mem;static int checks;
 static IntPtr At(int x){return new IntPtr(mem.ToInt32()+x);}static int Get(int x){return Marshal.ReadInt32(At(x));}static void Put(int x,int v){Marshal.WriteInt32(At(x),v);}
 static byte[] Hex(string s){var b=new byte[s.Length/2];for(int i=0;i<b.Length;i++)b[i]=Convert.ToByte(s.Substring(i*2,2),16);return b;}
 static void Check(bool b,string s){if(!b)throw new Exception(s);checks++;}
 public static int Test(string hex,int rel){
 mem=VirtualAlloc(IntPtr.Zero,(UIntPtr)0x10000,0x3000,0x40);if(mem==IntPtr.Zero)throw new Exception("alloc");
 try {
 var code=Hex(hex);Array.Copy(BitConverter.GetBytes(0x1000-rel-4),0,code,rel,4);Marshal.Copy(code,0,mem,code.Length);
 var stub=new List<byte>();Action<string> e=s=>stub.AddRange(Hex(s));Action<int> n=v=>stub.AddRange(BitConverter.GetBytes(v));
 e("8b81d00d0000a3");n(At(0x3000).ToInt32());e("890d");n(At(0x3004).ToInt32());
 for(int j=0;j<3;j++){e("8b4424");stub.Add((byte)(4+j*4));e("a3");n(At(0x3008+j*4).ToInt32());}
 e("ff05");n(At(0x3014).ToInt32());e("b811111111b922222222ba33333333c20c00");Marshal.Copy(stub.ToArray(),0,At(0x1000),stub.Count);
 var w=new List<byte>();Action<string> emit=s=>w.AddRange(Hex(s));Action<int> val=v=>w.AddRange(BitConverter.GetBytes(v));
 emit("9c60b9");val(At(0x4000).ToInt32());emit("6a336a226a11e8");val(-0x2000-w.Count-4);
 emit("890d");val(At(0x3018).ToInt32());emit("619dc3");Marshal.Copy(w.ToArray(),0,At(0x2000),w.Count);
 var run=(Run)Marshal.GetDelegateForFunctionPointer(At(0x2000),typeof(Run));
 foreach(int visible in new int[]{0,1,2,-1}) {
 Put(0x4dd0,visible);Put(0x3014,0);run();
 Check(Get(0x3000)==0,"Avatar disabled only during home draw");Check(Get(0x4dd0)==visible,"Original visibility restored");
 Check(Get(0x3004)==At(0x4000).ToInt32(),"Original preview instance");Check(Get(0x3018)==At(0x4000).ToInt32(),"ECX restored despite renderer clobber");
 Check(Get(0x3008)==0x11&&Get(0x300c)==0x22&&Get(0x3010)==0x33,"All three render arguments preserved");Check(Get(0x3014)==1,"Renderer called once");
 }
 }finally{VirtualFree(mem,UIntPtr.Zero,0x8000);}return checks;
 }
}
'@
$audit=Join-Path $PSScriptRoot 'port-audit/home-background-only'
$m=Get-Content -LiteralPath (Join-Path $audit 'manifest.json') -Raw|ConvertFrom-Json
$passed=[HomeBackgroundTest]::Test($m.code,$m.relativeOffset)
@{passed=$passed;gameProcessTouched=$false}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $audit 'native-test-result.json')
Write-Output "$passed isolated native home-background assertions passed"
