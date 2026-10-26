import json,re,hashlib
from pathlib import Path
from decimal import Decimal,ROUND_HALF_UP
import xlrd

ROOT=Path(__file__).resolve().parents[1]
b=xlrd.open_workbook(ROOT/'data/research/coaching/sources/pilot2018-supplement/AEK PL research traditional periodized template.xls')
m=json.loads((ROOT/'data/research/coaching/pilot2018-sbd.json').read_text())
f=json.loads((ROOT/'data/research/coaching/reviews/per-formulas.json').read_text())
lookup={(r['sheet'],r['row']):r for r in f['formulas'] if r['col']==6}
issues=[]; rows=[]
for session in m['protocol']['sessions']:
    for r in session['rows']:
        src=r['source']; n=int(re.search(r'A(\d+)',src['cells'])[1]);s=b.sheet_by_name(src['sheet']);v=s.row_values(n-1)
        assert [round(v[2]*100,6),int(v[3]),int(v[4])]==[r['percent_1rm'],r['reps'],r['sets']]
        form=lookup[src['sheet'],n]['formula']
        match=re.fullmatch(r'ROUND\(VLOOKUP\(\$B\$(\d+),\$B\$1:\$C\$(\d+),2\.0,3\.0\)\*C(\d+)/2\.5,0\.0\)\*2\.5',form)
        if not match:
            issues.append(dict(sheet=s.name,row=n,formula=form,issue='unrecognized_formula'));continue
        anchor,index,percent_row=map(int,match.groups())
        exercise={1:'barbell_back_squat',2:'barbell_bench_press',3:'barbell_deadlift'}[index]
        baseline=s.cell_value(index-1,2)
        expected=float((Decimal(str(baseline))*Decimal(str(r['percent_1rm']))/100/Decimal('2.5')).quantize(Decimal('1'),rounding=ROUND_HALF_UP)*Decimal('2.5'))
        record=dict(week=session['week'],day=session['day'],sheet=s.name,row=n,source_exercise=r['source_exercise'],sets=r['sets'],formula=form,reference_exercise=exercise,reference_cell=f'C{index}',reference_label=s.cell_value(index-1,1),cached_kg=v[5],independently_computed_kg=expected)
        rows.append(record)
        if percent_row!=n or exercise!=r['numbered_sbd_anchor'] or expected!=v[5]:issues.append(record)
result=dict(source_sha256=f['source_sha256'],formula_cells_decoded=len(f['formulas']),training_rows_checked=len(rows),issues=issues,front_squat_rows=[r for r in rows if r['source_exercise']=='Front squat'],rows=rows,limitations=['Formula decoding and independent arithmetic; workbook not recalculated in Excel.','Front squat label versus manuscript SBD remains a source discrepancy.','Set roles not inferred from formulas.'])
(ROOT/'data/research/coaching/reviews/per-formula-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in result.items() if k not in ('rows','front_squat_rows')},ensure_ascii=False,indent=2))

assert not issues, "FORMULA_AUDIT_FAILED"
assert len(rows)==275, "INCOMPLETE_TRAINING_ROWS"
