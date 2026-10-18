# Four-lift delivery — 2026-10-18

## Decision and scope
SBD strength is the goal, not a blanket exercise exclusion. Preserve OHP and other accessory lifts when included in the source; record any omission/substitution as a separate product decision.
This supersedes the no_ohp_product_scope adoption decision in the historical 2026-10-16 review, without rewriting that historical evidence or old workout versions.

Petrizzo 2018 Procedures pp.86–87 and Results p.88 were reread against the existing extraction.
Source: https://www.asep.org/asep/asep/JEPonlineOCTOBER2018_Petrizzo.pdf
Reported: squat first 3x5 every session, bench/standing press alternate 3x5, deadlift 1x5 at least weekly, two or three nonconsecutive days, chosen rest/increment, progressive warm-up, supervised initial assessment and real-time supervision.
Outcome: 58 recruited, 40 analyzed, 24 completed, 15 stopped progression, 1 injury withdrawal, 18 other exclusions. This is not a randomized efficacy comparison or an individual growth predictor.
Correction/retraction review and independent expert review are not completed.

## Explicit product differences
- Bench first, alternating across week boundaries; deadlift once weekly on day 2.
- Existing schedule policy enforces 48-hour start spacing. This is a product policy, not a proven safety threshold.
- Adult independent four-lift performers with registered known loads; self-report is not technique certification.
- Each lift starts from a recorded coach-assessed 5RM or known working load, with origin retained. Known working load is an adaptation, not the study's assessment.
- Subsequent loads remain explicit user choices. No regression-derived increments, automatic reset/deload or diagnosis of a stall.
- Weight changes during a set/session remain possible and are recorded separately.
- Source supervision is not reproduced by the app. No unsupervised safety claim.
- OHP measurements are shown separately and do not enter SBD total change.

## Deliverables
| Definition | Sessions | Working sets | Access |
| --- | ---: | ---: | --- |
| petrizzo2018-four-lift-2d-v1 | 24 | 156 | internal preview |
| petrizzo2018-four-lift-3d-v1 | 36 | 228 | internal preview |

These are two schedule choices from one study, not independent replications.
Legacy omission definition and its hash are preserved for existing records.
Database migrations add two immutable versions and RPC v4 (v3 envelope plus catalog_revision=4). The follow-up migration restores v3 to its original adapter set so deployed older readers do not fail on new adapters. RLS and execution allowlist remain.

## Supply audit
| User | Actual data | Remaining gap |
| --- | --- | --- |
| No technique or known load | Existing educational extraction, not an executable training course | In-app technique/first-load learning flow and reviewed demonstration |
| Learned four lifts and known loads | Two new complete schedules | Public product release review; deployed authenticated execution |
| Trained lifter | Existing Helms 2 arms, PER adapted 1 arm | Conditions/changes remain visible; no blanket intermediate suitability claim |
| Experienced powerlifter | Existing METD 3 arms | Experience/RPE conditions remain; no elite blanket suitability claim |

Existing legacy omission choice remains, giving six active definitions / nine options; this count does not mean nine papers or nine public routines.

## Verification boundaries
- Local full-course API execution: 24 + 36 sessions, restart/readback, idempotent start, no required 1RM, programme closure.
- Counterexamples: unknown/missing start origin, insufficient four-lift experience, source tamper, changed weight/repetitions, incomplete work, pain context, SBD/OHP total separation.
- Real Supabase HTTPS catalogue fetched with configured publishable credentials; version hashes and local JSON matched.
- Local FastAPI used the real catalogue for readiness/create/change/stop/next-session. Authentication overridden only in the test process; disposable SQLite ledger.
- This is NOT deployed authenticated HTTP/Postgres workout verification. Production user records were not written.
- Security advisor after migration: no new issue; existing two private research tables have RLS without policies (INFO).
- Reproduce: python -m scripts.verify_tests; with SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY, python -m scripts.verify_live_petrizzo_catalog.

## Next concrete gate
Connect the existing deployed backend to its authorized Postgres configuration and verify one actual signed-in owner's complete flow. Do not add an authentication bypass.
Public release and independent evidence review remain separate from technical execution.
Entry-level learning remains an explicit unsupported segment; do not label an independent-lifter programme as its substitute.
The inactivity policy closes a session as stopped; no resume-after-close is implemented. Unrecorded sets remain unknown.
