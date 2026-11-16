"""Hide only the avatar layer in the four shop-home background previews."""
from pathlib import Path
import struct,json,hashlib
import pefile
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'port-audit/home-background-only'
sha=lambda b:hashlib.sha256(b).hexdigest()
align=lambda n,a:(n+a-1)//a*a
def main():
    OUT.mkdir(parents=True,exist_ok=False)
    original=(ROOT/'client/CA.exe').read_bytes()
    expected=json.loads((ROOT/'port-audit/shop-tryon-color/manifest.json').read_text())['candidateSha256']
    assert sha(original)==expected
    pe=pefile.PE(data=original);image=pe.OPTIONAL_HEADER.ImageBase;last=pe.sections[-1]
    rva=align(last.VirtualAddress+max(last.Misc_VirtualSize,last.SizeOfRawData),pe.OPTIONAL_HEADER.SectionAlignment)
    base=image+rva
    # Save flags/registers and the original preview-only avatar-visible field.
    # Forward the three original arguments to CRoomPreview::Render, then restore.
    code=bytearray.fromhex('9c608b81d00d00005083a1d00d000000ff742434ff742434ff742434e8')
    rel=len(code);code+=struct.pack('<i',0x4d60fd-(base+rel+4))
    code+=bytes.fromhex('588b5424188982d00d0000619dc20c00')
    header=last.get_file_offset()+40;assert not any(original[header:header+40])
    raw=align(len(original),pe.OPTIONAL_HEADER.FileAlignment);size=align(len(code),pe.OPTIONAL_HEADER.FileAlignment)
    result=bytearray(original)+bytes(raw-len(original))+code+bytes(size-len(code))
    struct.pack_into('<8sIIIIIIHHI',result,header,b'.bgonly',len(code),rva,size,raw,0,0,0,0,0x60000020)
    nh=pe.FILE_HEADER.get_field_absolute_offset('NumberOfSections');ih=pe.OPTIONAL_HEADER.get_field_absolute_offset('SizeOfImage')
    struct.pack_into('<H',result,nh,len(pe.sections)+1)
    struct.pack_into('<I',result,ih,align(rva+len(code),pe.OPTIONAL_HEADER.SectionAlignment))
    site=0x5c13a0;off=pe.get_offset_from_rva(site-image);old=original[off:off+5]
    assert old==b'\xe8'+struct.pack('<i',0x4d60fd-site-5)
    result[off:off+5]=b'\xe8'+struct.pack('<i',base-site-5)
    allowed=set(range(header,header+40))|set(range(nh,nh+2))|set(range(ih,ih+4))|set(range(off,off+5))
    assert all(x==y or j in allowed for j,(x,y) in enumerate(zip(original,result)))
    (OUT/'CA.exe.before').write_bytes(original);(OUT/'CA.exe.candidate').write_bytes(result)
    (OUT/'manifest.json').write_text(json.dumps(dict(beforeSha256=sha(original),candidateSha256=sha(result),site=site,code=code.hex(),relativeOffset=rel,base=base,scope='Four home room-preview cards only; original avatar visibility restored after draw',runtimeVerification='pending'),indent=2))
    print('Prepared home-only background draw adapter')
if __name__=='__main__':main()
