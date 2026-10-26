import json, struct, hashlib
from pathlib import Path
import xlrd
from xlrd.formula import decompile_formula, FMLA_TYPE_CELL, FMLA_TYPE_SHARED

ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'data/research/coaching/sources/pilot2018-supplement/AEK PL research traditional periodized template.xls'
b=xlrd.open_workbook(p,on_demand=True)
out=[]
for name,start in zip(b.sheet_names(),b._sh_abs_posn):
    sheet=b.sheet_by_name(name)
    shared=[]
    scan=start
    while scan<len(b.mem):
        code,size=struct.unpack_from('<HH',b.mem,scan)
        data=b.mem[scan+4:scan+4+size];scan+=4+size
        if code==0x0a:break
        if code==0x04bc:
            r1,r2,c1,c2,count,length=struct.unpack('<HHBBxBH',data[:10])
            shared.append((r1,r2,c1,c2,data[10:10+length]))
    pos=start
    while pos<len(b.mem):
        code,size=struct.unpack_from('<HH',b.mem,pos)
        data=b.mem[pos+4:pos+4+size];pos+=4+size
        if code==0x0a:break
        if code!=0x06:continue
        row,col=struct.unpack_from('<HH',data)
        length=struct.unpack_from('<H',data,20)[0]
        tokens=data[22:22+length]
        formula=decompile_formula(b,tokens,length,FMLA_TYPE_CELL,row,col)
        if formula and formula.startswith('SHARED FMLA'):
            matches=[x for x in shared if x[0]<=row<=x[1] and x[2]<=col<=x[3]]
            assert len(matches)==1,(name,row,col)
            tokens=matches[0][4]
            formula=decompile_formula(b,tokens,len(tokens),FMLA_TYPE_SHARED,row,col)
        out.append(dict(sheet=name,row=row+1,col=col+1,formula=formula,cached=sheet.cell_value(row,col)))
result=dict(source_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),formulas=out)
(ROOT/'data/research/coaching/reviews/per-formulas.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))

print('formula_count',len(out),'unresolved',sum(x['formula'] is None for x in out))
