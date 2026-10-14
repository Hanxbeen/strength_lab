"""Shared observation semantics; no training-effect inference."""
def pain_reported(rows):
    return any(r.get('reason') == 'pain' or (r.get('actual') or {}).get('reason') == 'pain'
               or any(c.get('reason') == 'pain' for c in r.get('changes', []))
               or any('pain_discomfort' in x.get('reason_codes',[]) for x in r.get('reason_reports',{}).values())
               for r in rows)

def short_interset_rests(rests):
    return [dict(r) for r in rests if r.get('kind') == 'between_sets'
            and r.get('outcome') == 'skipped' and r['shortfall_seconds'] > 0]
