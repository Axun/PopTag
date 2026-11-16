"""Keep selected palette through equip/try-on refresh; explicit color changes stay native."""
from pathlib import Path
import sys,struct,json,hashlib
import pefile
sys.path.insert(0,r'D:\GAME\work\PopTag-monster-port')
from prepare_cn_login_tabs import Asm
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'port-audit/shop-preview-color'
def align(n,a):return (n+a-1)//a*a
def sha(b):return hashlib.sha256(b).hexdigest()
def adapter(base,register):
    a=Asm(base);a.emit('9c');a.load('8b0d',0x9e06c0)
    a.emit('85c9');a.branch('0f84','done')
    a.emit('8b81ec100000' if register=='eax' else '8bb9ec100000')
    a.emit('83f808' if register=='eax' else '83ff08');a.branch('0f86','done')
    a.emit('33c0' if register=='eax' else '33ff')
    a.label('done');a.emit('9dc3');return a.done(),a.absolute
def main():
    OUT.mkdir(parents=True,exist_ok=False)
    exe=(ROOT/'client/CA.exe').read_bytes();pe=pefile.PE(data=exe,fast_load=True);image=pe.OPTIONAL_HEADER.ImageBase
    last=pe.sections[-1];rva=align(last.VirtualAddress+max(last.Misc_VirtualSize,last.SizeOfRawData),pe.OPTIONAL_HEADER.SectionAlignment);base=image+rva
    hooks=[];payload=bytearray()
    for site,register in [(0x65cf01,'edi'),(0x5d6861,'eax')]:
        offset=align(len(payload),16);payload.extend(bytes(offset-len(payload)))
        code,absolute=adapter(base+offset,register);payload.extend(code)
        native=pe.get_offset_from_rva(site-image);old=bytes.fromhex('8b0dc0069e00');assert exe[native:native+6]==old
        hooks.append({'site':site,'fileOffset':native,'register':register,'codeOffset':offset,'code':code.hex(),'absolute':absolute,'before':old.hex()})
    header=last.get_file_offset()+40;assert header+40<=min(s.PointerToRawData for s in pe.sections) and not any(exe[header:header+40])
    raw=align(len(exe),pe.OPTIONAL_HEADER.FileAlignment);size=align(len(payload),pe.OPTIONAL_HEADER.FileAlignment)
    result=bytearray(exe)+bytes(raw-len(exe))+payload+bytes(size-len(payload))
    struct.pack_into('<8sIIIIIIHHI',result,header,b'.shpcol',len(payload),rva,size,raw,0,0,0,0,0x60000020)
    struct.pack_into('<H',result,pe.FILE_HEADER.get_field_absolute_offset('NumberOfSections'),len(pe.sections)+1)
    struct.pack_into('<I',result,pe.OPTIONAL_HEADER.get_field_absolute_offset('SizeOfImage'),align(rva+len(payload),pe.OPTIONAL_HEADER.SectionAlignment))
    allowed=set(range(header,header+40))
    for offset,n in [(pe.FILE_HEADER.get_field_absolute_offset('NumberOfSections'),2),(pe.OPTIONAL_HEADER.get_field_absolute_offset('SizeOfImage'),4)]:allowed.update(range(offset,offset+n))
    for h in hooks:
        site=h['site'];offset=h['fileOffset'];result[offset:offset+6]=b'\xe8'+struct.pack('<i',base+h['codeOffset']-site-5)+b'\x90';allowed.update(range(offset,offset+6))
    assert all(x==y or j in allowed for j,(x,y) in enumerate(zip(exe,result)))
    (OUT/'CA.exe.before').write_bytes(exe);(OUT/'CA.exe.candidate').write_bytes(result)
    (OUT/'manifest.json').write_text(json.dumps({'base':base,'payloadBytes':len(payload),'hooks':hooks,'beforeSha256':sha(exe),'candidateSha256':sha(result),'scope':'Only implicit equip/try-on palette arguments; preserve CUserFxMan+10EC selected palette, do not alter item definitions or manual color-cycle call sites','gameplayVerification':'pending'},indent=2))
    print('Prepared two bounded palette adapters; original explicit color selection calls untouched.')
if __name__=='__main__':main()
