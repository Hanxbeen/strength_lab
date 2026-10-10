# 무게무게 iOS (SwiftUI)
Requires Xcode and XcodeGen.

    cd apps/ios
    xcodegen generate
    xcodebuild -project MugeMuge.xcodeproj -scheme MugeMuge -sdk iphoneos -configuration Debug CODE_SIGNING_ALLOWED=NO build

Run API locally from repository root:

    python3 -m pip install -r backend/requirements.txt
    python3 -m uvicorn backend.main:app --reload

The API intentionally publishes ZERO research protocols. The separate demo catalog is labeled DEMO_ONLY.
For iPhone physical-device development, configure a reachable HTTPS API endpoint.

## Offline-first slice
- The demo catalog is bundled in the app, so it works without a server.
- Workout sets are atomically persisted to Application Support. Invalid values are rejected and failed writes do not update the visible log.
- Sets can be deleted. The Growth tab shows Epley e1RM estimates (1–10 reps) and training volume; measured 1RM records are stored separately from estimates through the maximum-weight setup screen.
- API URL may be supplied via Info.plist key MugeMugeAPIURL (HTTPS for remote hosts).
- The current build uses Xcode 27.0. NativeGlassPanel keeps its compiler-gated Liquid Glass implementation; full device visual validation remains outstanding.

## Device installation checklist (iPhone iOS 26.5)
- A physical iPhone named Hanbeen (iPhone 15 Pro, iOS 26.5) is paired with this Mac.
- As of 2026-10-10, the connected Mac uses Xcode 27.0 (27A266a), and a signed physical-device build succeeds.
- Xcode > Settings > Accounts: sign in with the Apple ID that owns the development team.
- In Signing & Capabilities choose that team and enable automatic signing; generate a development provisioning profile for the app bundle ID.
- Build and run on the selected physical device. Never use CODE_SIGNING_ALLOWED=NO for physical installation.
- Earlier installation attempts on 2026-10-09 failed with unsigned builds and missing credentials. The current signed build passed on 2026-10-10; installation and launch results are recorded in the continuation verification below.
- The app has not yet passed device UI, gesture, lifecycle, or end-to-end testing.

## Atomic workout persistence (2026-10)
- All logged sets, active session, completed sessions, and measured 1RMs share one atomically written `workout-database.json` snapshot.
- `completeSet` commits both the set and its session reference in one operation. `delete` also removes all session references in the same operation; `updateSet` modifies the saved weight/reps atomically.
- On first launch, old `workout-logs.json` and `training-state.json` are migrated if present. Legacy files remain untouched. Dangling set references are filtered.
- A corrupted unified file blocks all writes and is preserved for recovery. File write failure does not update in-memory data.
- Verified with Swift CLI persistence tests; real-device forced termination, storage exhaustion, and power-loss tests remain outstanding.

## Backup and edit UI
- Tap a completed set in the exercise screen to edit its weight/repetitions. Changes update e1RM and volume from the same persisted data.
- The Data tab exports the unified snapshot as a JSON file via the iOS share sheet. The user must save it somewhere safe; this is not automatic cloud backup.
- Import uses the system document picker, schema and referential integrity validation, and an explicit destructive confirmation. Import replaces the entire current snapshot, never merges.
- Swift CLI tests cover export/import roundtrip, invalid backup rejection, edit persistence, and prior migration scenarios. Actual file-picker/share-sheet interaction still needs on-device testing.

## Native visual system
- `BrandUI.swift` defines reusable color, card, section title, primary action and platform-native glass wrapper.
- Home uses branded editorial hierarchy and restrained surfaces. NativeGlassPanel uses system material on older SDKs; its iOS 26 glassEffect branch is compiled only by Swift 6.2+ toolchains with iOS 26 SDK support.
- The earlier Xcode 16.2 limitation is historical. The current Xcode 27.0 build compiles the app, but dedicated visual and touch validation of Liquid Glass remains outstanding.
- Cloud sync architecture proposal: `docs/CLOUD_ARCHITECTURE.md`. No remote cloud sync is deployed.

## Training and progress UI iteration
- Exercise screen: branded session progress, prominent weight/reps, guarded save, persistent rest timer, editable history cards.
- Progress screen: SBD selector, separated estimated 1RM and manually measured 1RM, training volume, estimate chart, session history.
- All changes use SwiftUI and reusable brand primitives; dedicated on-device visual validation remains outstanding.
- Supabase is connected to the assistant but the target project has not yet been identified; do not deploy schema or credentials into an unrelated project.

## Approved native flow verification (2026-10-10)
- The app entry uses ApprovedHomeView: home, routine library, training history, and growth, with settings accessible from home.
- Shared foundations in BrandUI.swift cover semantic colors, spacing, typography, cards, buttons, aligned metric cards, Dynamic Type reflow, and numeric accessibility labels.
- StrengthSetupView offers actual 1RM entry, calculation from a previous set, and a guided assessment with preparation, technique, warmup, attempt, and result stages. Estimates do not overwrite measured records.
- GuidedWorkoutView covers starting weights, atomic set completion, editable sets, persisted pause/resume/extension of rest, resuming a workout, and completion.
- Display name: 무게무게. App icon: opaque 1024×1024 frontal Lila face closeup.
- Fixed a missing initial wrapped value in the shared ScaledMetric property that prevented the latest foundation build.
- Signed Debug build passed with Xcode 27.0 for the paired Hanbeen iPhone. devicectl installation and app launch both completed successfully (bundle ID app.mugemuge.ios).
- All 11 Swift CLI test suites passed, including rest persistence, migration compatibility, invalid-backup rejection, account isolation, and transport/merge tests.
- Full manual gesture, keyboard, VoiceOver, Dynamic Type, and visual comparison against every wireframe state remain unverified.
