"""Build a curated research draft, NEVER an executable programme or approval.

Table values were manually checked against dissertation Table 5, printed pp50-51
(PDF pp65-66). Journal Training Protocol supplies the reported adjustment options.
This script expands those facts; it does not infer missing coaching decisions.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'data/research/coaching/reviews/zourdos2016.json'
JOURNAL = 'https://journals.lww.com/nsca-jscr/fulltext/2016/03000/modified_daily_undulating_periodization_model.24.aspx'
THESIS = 'https://repository.lib.fsu.edu/islandora/object/fsu%3A183214'
PDF = 'https://liftvault.com/wp-content/uploads/2017/07/Daily-Undulating-Periodization-Research-Zourdos-et-al-2012-LiftVault.com_.pdf'
PDF_SHA256 = '68d60dc6fef46cf7d3189c63d7504ff80afe2b0df10a988f49f792d4fd70983d'
SBD = ['barbell_back_squat', 'barbell_bench_press', 'barbell_deadlift']


def build():
    rows = []
    for week in range(1, 7):
        sets = (5, 5, 4, 4, 3, 3)[week - 1]
        strength = (85, 87.5, 90, 90, 92.5, 95)[week - 1]
        power = (80, 80, 85, 85, 90, 90)[week - 1]
        for kind, movements in [('H', SBD[:2]), ('S', SBD), ('P', SBD[:2])]:
            for exercise in movements:
                unresolved = kind == 'H' and week > 1
                rows.append({
                    'id': 'w%d-%s-%s' % (week, kind, exercise),
                    'training_week': week, 'session_kind': kind, 'exercise_id': exercise,
                    'sets': 3 if kind == 'S' else sets, 'set_role': 'working',
                    'reps': {'kind': 'to_failure' if kind == 'S' else 'fixed',
                             'value': None if kind == 'S' else (8 if kind == 'H' else 1),
                             'rpe_target': None},
                    'load': {'kind': 'individually_adjusted' if unresolved else 'percent_1rm',
                             'percent': None if unresolved else (75 if kind == 'H' else strength if kind == 'S' else power),
                             'reference_exercise': exercise,
                             'adjustment_rule': None,
                             'reported_change_options_lb': [0, 5, 10] if unresolved else None},
                    'training_rest_seconds': None,
                    'provenance': {'kind': 'source_reported', 'table': 'thesis_table5',
                                   'methods': 'journal_training_protocol'},
                    'conflict_ids': ['power_week_typo'] if kind == 'P' and week in (2, 3, 4) else [],
                })
    arms = {}
    for arm, order in [('HSP', ['H', 'S', 'P']), ('HPS', ['H', 'P', 'S'])]:
        sessions = []
        for week in range(1, 7):
            for day, kind in enumerate(order, 1):
                sessions.append({'training_week': week, 'ordinal': day, 'kind': kind,
                                 'row_ids': [r['id'] for r in rows if r['training_week'] == week and r['session_kind'] == kind]})
        arms[arm] = {'sessions': sessions, 'source_locator': 'journal Experimental Approach to the Problem',
                     'public_eligible': False, 'automatic_prescription_complete': False}
    return {
        'schema_version': 'curated-sbd-source-review-v1', 'id': 'zourdos2016-dup-review',
        'reviewed_on': '2026-10-15', 'status': 'source_facts_only',
        'scientific_approval': False, 'executable': False,
        'sources': {
            'journal': {'doi': '10.1519/JSC.0000000000001165', 'year': 2016, 'url': JOURNAL,
                        'identity_verified_against': 'publisher DOI, title, authors and journal issue'},
            'thesis': {'year': 2012, 'url': THESIS, 'download_url': PDF, 'sha256': PDF_SHA256,
                       'copyright': 'author copyright; full PDF not redistributed in repository'},
        },
        'locators': {
            'thesis_table5': {'report': 'thesis', 'printed_pages': [50, 51], 'pdf_pages_one_based': [65, 66], 'method': 'visual_table_and_extracted_text_checked'},
            'journal_training_protocol': {'report': 'journal', 'section': 'Training Protocol'},
        },
        'evidence_relationship': {
            'independent_study_count_claimed': 1,
            'assessment': 'Treat thesis and journal as linked reports, not independent replication; same sample size, protocol and descriptive characteristics. Exact cohort identity not independently confirmed.',
            'conflict': 'Thesis recruitment mentions 2011/2012 teams; journal also mentions 2013. Do not merge participant-level data.'},
        'population': {'source': 'journal Subjects', 'sex': 'male', 'analyzed': 18,
                       'arm_n': {'HSP': 9, 'HPS': 9}, 'screened': 26, 'started': 20,
                       'noncompletion': 2, 'noncompletion_reason': 'noncompliance; >2 missed sessions',
                       'training_years_min': 5, 'structured_training_years_min': 1,
                       'prior_sessions_per_week_min': 3,
                       'minimum_1rm_bodyweight_ratios': dict(zip(SBD, [2, 1.25, 2])),
                       'application': 'experienced powerlifters; not evidence for a beginner default or an app eligibility rule'},
        'protocol': {'training_weeks': 6, 'study_weeks_including_testing': 8, 'sessions_per_week': 3,
                     'spacing': 'nonconsecutive days', 'weekly_exercise_frequency': dict(zip(SBD, [3, 3, 1])),
                     'rows': rows, 'arms': arms,
                     'warmup': None, 'training_rest': None, 'missed_session_rule': None,
                     'failed_rep_adjustment': None, 'next_cycle_rule': None,
                     'controls': ['Researcher supervision and lift standards', '30 g whey before and after sessions', 'Replicated prior-day dietary intake', 'No additional structured exercise'],
                     'control_note': 'Study context, not a product supplement recommendation or evidence that each control causes benefit.'},
        'conflicts': [
            {'id': 'power_week_typo', 'reported': 'Methods put 80% in weeks1-2 and 85% in weeks2-3; omit week4.',
             'table_fact': 'Table5 puts 80% in weeks1-2 and 85% in weeks3-4.',
             'handling': 'Preserve both; structured rows transcribe table, not a verified author correction.'},
            {'id': 'thesis_table6_caption', 'reported': 'Both original and switched order are labelled HSP in caption.',
             'handling': 'Arm order comes from explicit journal Methods and thesis pp46-47, not the caption.'}],
        'limitations': ['Small experienced male sample; no inactive/usual-training control',
                        'Not a comparison proving this is optimal for all users',
                        'Training to failure cannot be silently replaced with RPE9-9.5',
                        'Journal reference14 (Mann2010) alone does not identify which adjustment thresholds were used here'],
        'unresolved_decisions': [
            {'id': 'hypertrophy_adjustment', 'scope': 'weeks2-6 squat and bench',
             'known': 'reported choices: same load, +5 lb, +10 lb',
             'missing': 'performance threshold and input set selecting each choice',
             'automatic_fallback': None},
            {'id': 'execution_choices', 'scope': 'warmup, rest, equipment rounding, load-reference refresh',
             'missing': 'complete operational rules in retrieved training methods', 'automatic_fallback': None},
            {'id': 'failure_and_reentry', 'scope': 'incomplete work, pain, long absence, subsequent cycle',
             'missing': 'research-based response rules for this protocol', 'automatic_fallback': None}],
        'publication_check': {'correction_status': 'not_fully_verified',
                              'note': 'A targeted search did not establish an authoritative correction; absence of a result is not clearance.'},
        'adoption': {'decision': 'retain_as_experienced_lifter_candidate',
                     'default_basic_sbd': False, 'runtime_adapter': None, 'db_imported': False,
                     'next_action': 'Specify and review explicit user/product choices for missing decisions before any execution adapter; continue basic-SBD applicability review.'},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-pdf', type=Path, help='Optional local thesis identity check; no redistribution')
    parser.add_argument('--check', action='store_true', help='Check committed draft without writing')
    args = parser.parse_args()
    if args.source_pdf and hashlib.sha256(args.source_pdf.read_bytes()).hexdigest() != PDF_SHA256:
        raise SystemExit('SOURCE_PDF_CHANGED: re-review tables before updating transcription')
    result = build()
    if args.check:
        if json.loads(OUTPUT.read_text()) != result:
            raise SystemExit('DRAFT_DRIFT')
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print('42 source rows; 18 sessions / 150 working sets per arm; NOT executable; 10 unresolved load rows')


if __name__ == '__main__':
    main()
