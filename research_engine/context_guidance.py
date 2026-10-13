"""Non-prescriptive, versioned research interpretation attached to actual records."""
from .core import digest
from .workout import require
from .execution_facts import pain_reported, short_interset_rests

POLICY = 'context-guidance-v2'
TOPICS = ('rest', 'volume', 'deload')

def validate_packet(packet):
    require(isinstance(packet, dict), 'INVALID_CONTEXT_PACKET')
    require(packet.get('schema_version') == 1 and packet.get('scientific_approval') is False
            and packet.get('review_status') == 'extracted_pending_independent_review', 'CONTEXT_REVIEW_REQUIRED')
    sources = packet.get('sources')
    require(isinstance(sources, list) and len(sources) == 3, 'CONTEXT_SOURCES_REQUIRED')
    require({s.get('topic') for s in sources} == set(TOPICS), 'CONTEXT_TOPICS_REQUIRED')
    require(len({s.get('id') for s in sources}) == len(sources), 'DUPLICATE_CONTEXT_SOURCE')
    for source in sources:
        require(source.get('prescription_changes_allowed') is False, 'CONTEXT_NOT_PRESCRIPTIVE')
        require(source.get('review_extent') in ('abstract_only','methods_results_limitations_fulltext'),
                'CONTEXT_REVIEW_EXTENT')
        for key in ('id','doi','url','title','locator','guidance_ko','finding'):
            require(isinstance(source.get(key),str) and bool(source[key]), 'CONTEXT_FIELD_REQUIRED')
        require(source['url'].startswith('https://') and bool(source.get('limitations')), 'CONTEXT_PROVENANCE_REQUIRED')
    return packet

def explain(execution, packet, topic='auto'):
    validate_packet(packet)
    require(topic in ('auto',) + TOPICS, 'UNKNOWN_CONTEXT_TOPIC')
    rows = execution['sets']
    completed_rests = execution['rests']
    short_rests = short_interset_rests(completed_rests)
    attempted = [r for r in rows if r.get('actual') and r['status'] == 'recorded']
    below = [r['id'] for r in attempted if r['actual']['reps'] < r['reps']['min']]
    pain = pain_reported(rows)
    selected = ([topic] if topic != 'auto' else (['rest'] if short_rests else []))
    facts = {
        'recorded_sets': len(attempted), 'below_minimum_rep_set_ids': below,
        'skipped_sets': sum(r['status'] == 'skipped' for r in rows),
        'not_attempted_sets': sum(r['status'] == 'not_attempted' for r in rows),
        'closed_rest_count': len(completed_rests), 'short_rests': short_rests,
        'active_rest_excluded': execution.get('active_rest') is not None,
        'pain_reported': pain,
    }
    cards = []
    if not pain and not execution.get('legacy_read_only'):
        for source in packet['sources']:
            if source['topic'] not in selected: continue
            cards.append({
                'code': 'RESEARCH_CONTEXT_' + source['topic'].upper(),
                'text': source['guidance_ko'], 'source': source,
                'kind': 'research_interpretation_preview',
                'applicability': 'not_assessed_for_individual',
                'prescription_change': None,
            })
    return {
        'policy_version': POLICY, 'evidence_id': packet['id'], 'evidence_version': digest(packet),
        'scientific_approval': False, 'status': 'pain_review_needed' if pain else 'research_preview',
        'execution_revision': execution['revision'], 'execution_hash': digest(execution),
        'facts': facts, 'cards': cards, 'topic': topic,
        'safety_note': '통증이 기록돼 있어 훈련 조정 안내를 제공하지 않아요.' if pain else None,
        'assessment_limits': ['One session cannot establish a plateau or identify its cause.',
                              'Rest differences are not growth-loss percentages.',
                              'Research sample averages are not individual predictions.'],
        'prescription_change': None, 'growth_prediction': None,
    }
