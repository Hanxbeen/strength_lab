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
- Sets can be deleted. The Growth tab shows Epley e1RM estimates (1–10 reps) and training volume; actual 1RM recording is not yet implemented.
- API URL may be supplied via Info.plist key MugeMugeAPIURL (HTTPS for remote hosts).
- iOS 26 Liquid Glass requires a newer Xcode/iOS SDK than the currently installed Xcode 16.2.

## Device installation checklist (iPhone iOS 26.5)
- A physical iPhone named Hanbeen (iPhone 15 Pro, iOS 26.5) is paired with this Mac.
- The current Xcode is 16.2 (iOS 18.2 SDK). Upgrade to an Xcode release supporting iOS 26.5 for on-device debugging and Liquid Glass development.
- Xcode > Settings > Accounts: sign in with the Apple ID that owns the development team.
- In Signing & Capabilities choose that team and enable automatic signing; generate a development provisioning profile for the app bundle ID.
- Build and run on the selected physical device. Never use CODE_SIGNING_ALLOWED=NO for physical installation.
- Device installation attempted on 2026-10-09 and failed because the app was unsigned; automatic signing then failed because Xcode has no account credentials for the development team.
- The app has not yet passed device UI, gesture, lifecycle, or end-to-end testing.

## Atomic workout persistence (2026-10)
- All logged sets, active session, completed sessions, and measured 1RMs share one atomically written `workout-database.json` snapshot.
- `completeSet` commits both the set and its session reference in one operation. `delete` also removes all session references in the same operation; `updateSet` modifies the saved weight/reps atomically.
- On first launch, old `workout-logs.json` and `training-state.json` are migrated if present. Legacy files remain untouched. Dangling set references are filtered.
- A corrupted unified file blocks all writes and is preserved for recovery. File write failure does not update in-memory data.
- Verified with Swift CLI persistence tests; real-device forced termination, storage exhaustion, and power-loss tests remain outstanding.
