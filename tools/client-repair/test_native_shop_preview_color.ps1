$ErrorActionPreference='Stop'
if([IntPtr]::Size -ne 4){throw 'Requires 32-bit Windows PowerShell'}
Add-Type -TypeDefinition @'
using System;using System.Collections.Generic;using System.Runtime.InteropServices;
public static class ShopPaletteSelfTest {
 [DllImport("kernel32.dll",SetLastError=true)]static extern IntPtr VirtualAlloc(IntPtr a,UIntPtr n,uint t,uint p);
 [DllImport("kernel32.dll")]static extern bool VirtualFree(IntPtr a,UIntPtr n,uint t);
 [UnmanagedFunctionPointer(CallingConvention.Cdecl)]delegate void Run();
 static IntPtr mem;static int checks;
 static IntPtr At(int x){return new IntPtr(mem.ToInt32()+x);}
 static void Put(int x,int n){Marshal.WriteInt32(At(x),n);}static int Get(int x){return Marshal.ReadInt32(At(x));}
 static byte[] Hex(string s){var b=new byte[s.Length/2];for(int i=0;i<b.Length;i++)b[i]=Convert.ToByte(s.Substring(i*2,2),16);return b;}
 static void Check(bool ok,string message){if(!ok)throw new Exception(message);checks++;}
 public static int Test(string hex,int[] absolute,string destination){
  mem=VirtualAlloc(IntPtr.Zero,(UIntPtr)0x8000,0x3000,0x40);if(mem==IntPtr.Zero)throw new Exception("Allocate isolated test buffer");
  try {
   byte[] code=Hex(hex);foreach(int a in absolute)Array.Copy(BitConverter.GetBytes(At(0x3000).ToInt32()),0,code,a,4);
   Marshal.Copy(code,0,At(0x1000),code.Length);
   var w=new List<byte>();Action<string> e=s=>w.AddRange(Hex(s));Action<int> n=v=>w.AddRange(BitConverter.GetBytes(v));
   e("9c60b811111111bb22222222ba33333333bf44444444bd55555555be6666666668460200009de8");n(0x1000-0x2000-w.Count-4);
   e("a3");n(At(0x3800).ToInt32());e("891d");n(At(0x3804).ToInt32());e("8915");n(At(0x3808).ToInt32());
   e("893d");n(At(0x380c).ToInt32());e("892d");n(At(0x3810).ToInt32());e("8935");n(At(0x3814).ToInt32());
   e("890d");n(At(0x3818).ToInt32());e("9c58a3");n(At(0x381c).ToInt32());e("619dc3");
   Marshal.Copy(w.ToArray(),0,At(0x2000),w.Count);var run=(Run)Marshal.GetDelegateForFunctionPointer(At(0x2000),typeof(Run));
   foreach(int color in new int[]{0,1,2,3,4,5,6,7,8,9,-1})foreach(bool present in new bool[]{true,false}){
    Put(0x3000,present?At(0x4000).ToInt32():0);Put(0x50ec,color);run();int desired=color>=0&&color<=8?color:0;
    Check(Get(0x3800)==(present&&destination=="eax"?desired:0x11111111),"EAX palette/slot argument");
    Check(Get(0x380c)==(present&&destination=="edi"?desired:0x44444444),"EDI palette argument");
    Check(Get(0x3818)==(present?At(0x4000).ToInt32():0),"Original manager load preserved");
    Check(Get(0x3804)==0x22222222&&Get(0x3808)==0x33333333&&Get(0x3810)==0x55555555&&Get(0x3814)==0x66666666,"Other registers preserved");
    Check((Get(0x381c)&0x8d5)==(0x246&0x8d5),"Flags preserved");Check(Get(0x50ec)==color,"Selected palette not written by adapter");
   }
  } finally {VirtualFree(mem,UIntPtr.Zero,0x8000);}return checks;
 }
}
'@
$audit=Join-Path $PSScriptRoot 'port-audit/shop-preview-color'
$m=Get-Content -LiteralPath (Join-Path $audit 'manifest.json') -Raw | ConvertFrom-Json
$total=0
foreach($h in $m.hooks){$total=[ShopPaletteSelfTest]::Test($h.code,[int[]]$h.absolute,$h.register)}
@{passed=$total;gameProcessTouched=$false}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $audit 'native-test-result.json')
Write-Output "$total isolated native shop palette assertions passed"
