import SwiftUI
import AppKit

final class AppState: ObservableObject {
    static let shared = AppState()

    @Published var fileURL: URL?
    @Published var scriptPath: String?
    let cacheDir: URL

    private init() {
        let pid = ProcessInfo.processInfo.processIdentifier
        let dir = FileManager.default.temporaryDirectory
            .appendingPathComponent("KaraokeProcessGUI-\(pid)", isDirectory: true)
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        self.cacheDir = dir
    }
}

final class AppDelegate: NSObject, NSApplicationDelegate {
    func application(_ application: NSApplication, open urls: [URL]) {
        guard let url = urls.first else { return }
        DispatchQueue.main.async {
            AppState.shared.fileURL = url
        }
    }

    func applicationDidFinishLaunching(_ notification: Notification) {
        DispatchQueue.main.async {
            if AppState.shared.fileURL == nil, CommandLine.arguments.count > 1 {
                let arg = CommandLine.arguments[1]
                if !arg.hasPrefix("-") {
                    AppState.shared.fileURL = URL(fileURLWithPath: arg)
                }
            }
            AppState.shared.scriptPath = self.locateScript()
        }
        NSColorPanel.setPickerMode(.crayon)
        NSApp.activate(ignoringOtherApps: true)
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        true
    }

    func applicationWillTerminate(_ notification: Notification) {
        try? FileManager.default.removeItem(at: AppState.shared.cacheDir)
    }

    private func locateScript() -> String? {
        let home = NSHomeDirectory()
        let candidates = [
            "\(home)/.local/bin/karaoke-process",
            "\(home)/Projects/ydj-music-studio/karaoke-processing/karaoke-process"
        ]
        for path in candidates where FileManager.default.isExecutableFile(atPath: path) {
            return path
        }
        return nil
    }
}

@main
struct KaraokeProcessGUIApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var delegate
    @StateObject private var state = AppState.shared

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(state)
                .frame(minWidth: 1100, minHeight: 720)
        }
        .windowResizability(.contentSize)
    }
}
