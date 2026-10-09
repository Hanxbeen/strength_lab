// swift-tools-version: 5.10
import PackageDescription

/// Local wrapper around the official Rive 6.28.1 XCFramework.
/// Run scripts/install_rive_xcframework.sh before generating/building Xcode.
let package = Package(
    name: "RiveRuntime",
    platforms: [.iOS(.v14)],
    products: [.library(name: "RiveRuntime", targets: ["RiveRuntime"])],
    targets: [
        .binaryTarget(
            name: "RiveRuntime",
            path: "Binaries/RiveRuntime.xcframework"
        )
    ]
)
