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
