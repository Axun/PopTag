"""Preserve CShopStageNew's own paper-doll palette at its two try-on setters."""
from pathlib import Path
import sys,struct,json,hashlib
import pefile
sys.path.insert(0,r'D:\GAME\work\PopTag-monster-port')
from prepare_cn_login_tabs import Asm
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'port-audit/shop-tryon-color'
sha=lambda b:hashlib.sha256(b).hexdigest()
def align(n,a):return (n+a-1)//a*a
def main():
 OUT.mkdir(parents=True,exist_ok=False)
 previous=json.loads((ROOT/'port-audit/shop-preview-color/manifest.json').read_text())
 current=(ROOT/'client/CA.exe').read_bytes();assert sha(current)==previous['candidateSha256']
 # Remove the ineffective shared-inventory adapters. Keep the separately
 # verified backpack adapter already present in this original baseline.
 exe=(ROOT/'port-audit/shop-preview-color/CA.exe.before').read_bytes();assert sha(exe)==previous['beforeSha256']
 pe=pefile.PE(data=exe,fast_load=True);image=pe.OPTIONAL_HEADER.ImageBase;last=pe.sections[-1]
 rva=align(last.VirtualAddress+max(last.Misc_VirtualSize,last.SizeOfRawData),pe.OPTIONAL_HEADER.SectionAlignment);base=image+rva
 a=Asm(base);a.emit('9c608d89742f0000');a.call(0x4d5f23)
 a.emit('83f808');a.branch('0f86','valid');a.emit('33c0');a.label('valid')
 a.emit('89442428619d') # replace only incoming color, restore all regs/flags
 a.emit('e9');offset=len(a.b);a.u32(0x5cec4a-base-offset-4);a.relative.append({'offset':offset,'target':0x5cec4a})
 code=a.done();header=last.get_file_offset()+40;assert not any(exe[header:header+40])
 raw=align(len(exe),pe.OPTIONAL_HEADER.FileAlignment);size=align(len(code),pe.OPTIONAL_HEADER.FileAlignment)
 result=bytearray(exe)+bytes(raw-len(exe))+code+bytes(size-len(code))
 struct.pack_into('<8sIIIIIIHHI',result,header,b'.trycol',len(code),rva,size,raw,0,0,0,0,0x60000020)
 struct.pack_into('<H',result,pe.FILE_HEADER.get_field_absolute_offset('NumberOfSections'),len(pe.sections)+1)
 struct.pack_into('<I',result,pe.OPTIONAL_HEADER.get_field_absolute_offset('SizeOfImage'),align(rva+len(code),pe.OPTIONAL_HEADER.SectionAlignment))
 sites=[];allowed=set(range(header,header+40))
 for off,n in [(pe.FILE_HEADER.get_field_absolute_offset('NumberOfSections'),2),(pe.OPTIONAL_HEADER.get_field_absolute_offset('SizeOfImage'),4)]:allowed.update(range(off,off+n))
 for site in [0x5d1625,0x5d155a]:
  off=pe.get_offset_from_rva(site-image);old=exe[off:off+5];assert old[0]==0xe8 and site+5+struct.unpack('<i',old[1:])[0]==0x5cec4a
  new=b'\xe8'+struct.pack('<i',base-site-5);result[off:off+5]=new;allowed.update(range(off,off+5));sites.append({'site':site,'offset':off,'before':old.hex(),'after':new.hex()})
 assert all(x==y or j in allowed for j,(x,y) in enumerate(zip(exe,result)))
 # Explicit color cycling calls the original setter directly and is untouched.
 off=pe.get_offset_from_rva(0x5d16d9-image);assert result[off:off+5]==exe[off:off+5]
 (OUT/'CA.exe.before').write_bytes(current);(OUT/'CA.exe.candidate').write_bytes(result)
 (OUT/'manifest.json').write_text(json.dumps({'base':base,'code':code.hex(),'relative':a.relative,'sites':sites,'replacesIneffectiveSharedPalettePatch':True,'beforeSha256':sha(current),'baselineSha256':sha(exe),'candidateSha256':sha(result),'manualColorCycleUnchanged':True,'runtimeVerification':'pending'},indent=2))
 print('Prepared independent shop try-on palette preservation; ineffective shared patch removed.')
if __name__=='__main__':main()
