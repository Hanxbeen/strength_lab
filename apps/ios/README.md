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
