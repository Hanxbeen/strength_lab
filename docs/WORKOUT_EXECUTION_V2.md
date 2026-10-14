> 호환 구현/과거 설계 기록. 현재 운영·공개 상태와 작업 순서는 [CURRENT.md](CURRENT.md)를 따른다. 이 문서만으로 배치 또는 처방 공개를 활성화하지 않는다.

# Source-linked workout execution v2

## Implemented scope

The source engine now has a separate execution ledger and API. This is a backend contract,
not a claim that the current iOS screens are connected or that the API has been deployed.
The five source templates are not five independent studies or expert-approved prescriptions.

Data linkage: source hash → programme version → source session → immutable execution
snapshot → selected measured-max record IDs → ordered set/rest events → summary chart.
New max registrations and catalog editions do not rewrite an existing workout.

### API

All routes below require a Supabase bearer token validated through `/auth/v1/user`.
Owner identity never comes from request JSON or editable user metadata.

| Route | Contract |
|---|---|
| POST/GET `/v2/max-records` | Immutable registrations; kg/lb input, canonical kg; measured vs estimated retained |
| POST `/v2/workout-readiness` | Missing exercise-specific max, working loads, RM test or setup choices; no writes |
| POST `/v2/workouts` | Start from current source version; reference max IDs; preserve source/setup snapshot |
| GET `/v2/workouts/{id}` | Owner-isolated recovery of events and recomputed execution state |
| POST `/v2/workouts/{id}/events` | `{expected_revision, event}`; transactional append and deterministic replay |

Event fields: `id`, timezone-aware `at`, `type`, plus payload:

| Type | Payload / effect |
|---|---|
| `change_load` | `set_id,value,unit,reason`; current set only; source target untouched |
| `set_result` | `set_id,reps,reason?,rir?,failure?`; below-minimum requires reason; starts rest |
| `skip_set` | `set_id,reason`; skipped is distinct from performed zero reps |
| `rest_end` | `outcome: completed/skipped`; cannot mark complete before target elapsed |
| `pause` / `resume` | Preserve prior state and physical elapsed rest, including background time |
| `finish` | Early finish requires reason; unresolved sets become not_attempted; ongoing rest retained |

Reasons: fatigue, pain, time, equipment, interruption, other. Pain pauses progression and
suppresses automatic load advice. This is a product handling rule, not medical triage.
Zero load is allowed as an actual/user-selected value; it does not substitute for a valid measured 1RM.

New event after closure is rejected. Exact duplicate event ID/payload is idempotent, including
after closure; conflicting reuse returns 409. Stale revision returns 409. Invalid transitions
return 422. Another owner's workout returns 404. Missing auth returns 401.

### Response and guidance

`sets` retains target reps/load/tempo and actual reps/weight/RIR/failure, plus load change history.
`active_rest` has started_at and target_seconds for client countdown; `rests` contains each closed
interval, outcome, elapsed_seconds and shortfall_seconds. Client timestamps are reported data,
not independently verified measurements. No polling is needed to persist timer ticks.

`guides` distinguishes source_reported evidence from versioned product_policy. Main-lift
decrease ranges are never applied to accessory RIR work. Missing effort data stays unknown.
No automatic catch-up volume, invented progression increment, or individual growth forecast.

`summary.chart` contains per-set target ranges, actuals, kg delta and rep shortfall. Unattempted
actuals remain null rather than fabricated zero performance. Minimum-rep completion is the
sum of capped per-set actual reps divided by total prescribed minimum reps, including planned
but unfinished sets. It is **not** a strength-gain, safety, or full protocol-adherence score.
Rest shortage is reported in seconds rather than combined into an unsupported efficacy score.

### Persistence and operational limits

`WORKOUT_DATABASE_PATH` must point to an absolute path on a private persistent volume. The
SQLite store uses owner-scoped keys and `BEGIN IMMEDIATE` transactions. It fails closed if
unconfigured. It is a single-server implementation, **not deployed Supabase personal storage**.
Production requires volume permissions, backup/retention/deletion policy, encryption and load
testing or a Postgres adapter. Auth integration tests use controlled test identities; no real
user credentials were accessed and no user exercise history was modified.

Outstanding: iOS v2 model/screen wiring, offline event queue and conflict UX, cloud sync adapter,
editing already recorded sets through explicit correction events, unilateral per-side results,
exercise substitutions, extra sets, calendar rescheduling, per-week outcome comparison and
the remaining scientific applicability review. Unsupported event types fail explicitly rather
than silently modifying the study protocol. This does not cover every conceivable situation.

### Verification

Run in the backend environment with FastAPI and httpx available:
`python -m unittest discover -s tests -p 'test_workout*.py' -v`

Uses committed real-source definitions, no AI. Tests cover max linkage, kg/lb, immutable targets,
shortfalls, early rest termination, pause/resume, pain, early completion, event idempotency,
ordering, revision conflict, owner isolation, durable reopen, invalid append rollback and API flow.

2026-10-11 verification: 110 domain/existing tests passed in the system environment and 6 API
tests passed in the FastAPI verification environment (116 distinct tests total; 23 new).
The combined run in the API environment initially failed to import an existing image test
because Pillow was absent; the split runs above verified that module in its existing environment.
API auth/catalog tests use test doubles; real end-user sign-in and production storage deployment
have not been verified in this change.
