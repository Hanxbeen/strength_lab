"""Build the source-labelled variant from the independently audited XLS rows."""
import copy,json,re
from pathlib import Path
from research_engine.core import digest
from research_engine.per_provenance import SOURCE_IDS
ROOT=Path(__file__).resolve().parents[1]
def build():
    source=json.loads((ROOT/'data/research/coaching/pilot2018-sbd.json').read_text())
    audit=json.loads((ROOT/'data/research/coaching/reviews/per-formula-audit.json').read_text())
    assert audit['source_sha256']==source['source_sha256'] and not audit['issues']
    assert audit['training_rows_checked']==275
    by_cell={(r['sheet'],r['row']):r for r in audit['rows']}
    source.update(adapter_version='per-source-labels-v1',id='pilot2018-per-source-labels-v1',title='SBD·프런트스쿼트 10주 · 보충표 기반',
        application='supplement_labels_and_formula_with_explicit_product_choices',
        exercises=source['exercises']+['barbell_front_squat'],
        max_reference_exercises=copy.deepcopy(source['exercises']),
        formula_audit_sha256=digest(audit))
    for session in source['protocol']['sessions']:
        for row in session['rows']:
            n=int(re.search(r'A(\d+)',row['source']['cells'])[1])
            verified=by_cell[row['source']['sheet'],n]
            assert verified['source_exercise']==row['source_exercise']
            row['exercise_id']=SOURCE_IDS[row['source_exercise']]
            row['load_reference']={k:verified[k] for k in ('formula','reference_cell','reference_label')}
            row['load_reference'].update(exercise_id=verified['reference_exercise'],
                basis='verified_xls_formula',source_sha256=source['source_sha256'])
    source['protocol_sha256']=digest(source['protocol'])
    source['adaptations'].pop('numbered_sbd_adaptation_v1')
    source['adaptations']['exercise_mapping']='Preserve all literal supplement exercise labels, including front squat. Manuscript discrepancy remains unresolved.'
    source['adaptations']['load']='Use verified workbook baseline reference and percentage with frozen user measured SBD maxes; nearest half-up user equipment increment. Original increment 2.5 kg. Cached example kg are never prescriptions.'
    source['adaptations']['supervision']='Independent execution differs from supervised research. Front squat experience and RPE familiarity are required product inputs, not automated technique assessment.'
    source['release_limit']='Explicit selection by experienced adults meeting product scope; not automatic recommendation, source replication, or scientific approval.'
    source['product_scope']={'age_min':18,'sex':'male','training_years_min':2,'powerlifting_years_min':1,
        'independent_sbd':True,'independent_front_squat':True,'rpe_familiarized':True,
        'prior_moderate_high_load_training':True,
        'basis':'Study population and RPE preparation plus explicit independent-execution product constraints.',
        'study_rpe_familiarization_weeks':4}
    return source
if __name__=='__main__':
    source=build()
    (ROOT/'data/research/coaching/pilot2018-source-labels.json').write_text(json.dumps(source,ensure_ascii=False,indent=2)+'\n')
    print(source['id'],digest(source))
