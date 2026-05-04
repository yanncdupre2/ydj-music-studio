// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "KaraokeProcessGUI",
    platforms: [.macOS(.v13)],
    targets: [
        .executableTarget(
            name: "KaraokeProcessGUI",
            path: "Sources/KaraokeProcessGUI"
        )
    ]
)
