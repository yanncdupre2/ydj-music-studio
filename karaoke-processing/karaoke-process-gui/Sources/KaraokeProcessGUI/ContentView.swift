import SwiftUI
import AppKit
import UniformTypeIdentifiers

struct ContentView: View {
    @EnvironmentObject var state: AppState
    @ObservedObject private var processService = ProcessService.shared
    @StateObject private var presetStore = PresetStore()

    @State private var parameters = ProcessingParameters()
    @State private var currentPreset: CurrentPreset = .custom
    @State private var player: AVPlayerWrapper?
    @State private var maskedImage: NSImage?
    @State private var processedImage: NSImage?
    @State private var isLoadingPreview = false
    @State private var statusNote: String?
    @State private var statusError: String?

    var body: some View {
        Group {
            if let url = state.fileURL, let player {
                mainLayout(url: url, player: player)
            } else if state.fileURL != nil {
                ProgressView("Loading…")
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                    .onAppear { initPlayer() }
            } else {
                emptyState
            }
        }
        .onChange(of: state.fileURL) { _ in
            player = nil
            maskedImage = nil
            processedImage = nil
            statusNote = nil
            statusError = nil
            initPlayer()
        }
    }

    // MARK: - Main Layout

    @ViewBuilder
    private func mainLayout(url: URL, player: AVPlayerWrapper) -> some View {
        VStack(spacing: 0) {
            Text(url.lastPathComponent)
                .font(.headline)
                .lineLimit(1)
                .truncationMode(.middle)
                .padding(.horizontal, 12).padding(.vertical, 6)
                .frame(maxWidth: .infinity, alignment: .leading)
            Divider()

            // Top row: video (left) | parameters (right)
            HSplitView {
                VideoPanel(player: player)
                    .frame(minWidth: 360, idealWidth: 480)

                ParametersPanel(
                    parameters: $parameters,
                    currentPreset: $currentPreset,
                    presetStore: presetStore,
                    currentPlayheadSeconds: player.currentSeconds,
                    videoDurationSeconds: player.durationSeconds,
                    canRefresh: state.scriptPath != nil,
                    isRefreshing: isLoadingPreview,
                    onUserTouched: userTouchedParameters,
                    onRefresh: refreshPreviews
                )
                .frame(minWidth: 600, idealWidth: 720)
            }
            .frame(minHeight: 320, idealHeight: 380)

            Divider()

            // Bottom row: mask preview (left) | LUT preview (right)
            HSplitView {
                PreviewPanel(
                    image: maskedImage,
                    label: "Mask + Zoom",
                    isLoading: isLoadingPreview,
                    showAspectBorder: true
                )
                .frame(minWidth: 320)

                PreviewPanel(
                    image: processedImage,
                    label: "LUT + Outline (full aspect)",
                    isLoading: isLoadingPreview,
                    showAspectBorder: true
                )
                .frame(minWidth: 320)
            }
            .frame(minHeight: 280)

            Divider()
            statusBar(url: url, player: player)
        }
    }

    // MARK: - Status Bar

    @ViewBuilder
    private func statusBar(url: URL, player: AVPlayerWrapper) -> some View {
        VStack(spacing: 4) {
            if state.scriptPath == nil {
                HStack {
                    Text("karaoke-process-v2 not found in ~/.local/bin or project tree.")
                        .foregroundColor(.red).font(.callout)
                    Spacer()
                }
            }
            statusRow(currentURL: url, player: player)
        }
        .padding(10)
    }

    @ViewBuilder
    private func statusRow(currentURL: URL, player: AVPlayerWrapper) -> some View {
        switch processService.status {
        case .idle:
            HStack {
                if let err = statusError {
                    Text(err).foregroundColor(.red).lineLimit(2)
                } else if let note = statusNote {
                    Text(note).foregroundColor(.secondary).lineLimit(1)
                }
                Spacer()
                Button {
                    startProcessing(url: currentURL, player: player)
                } label: {
                    Label("Process Video", systemImage: "play.circle.fill")
                }
                .buttonStyle(.borderedProminent)
                .controlSize(.large)
                .keyboardShortcut(.return, modifiers: [.command])
                .disabled(state.scriptPath == nil || player.durationSeconds <= 0)
            }

        case .starting(let input):
            HStack(spacing: 12) {
                ProgressView().controlSize(.small)
                Text("Starting: \(input.lastPathComponent)").foregroundColor(.secondary).lineLimit(1)
                Spacer()
                Button("Cancel") { processService.cancel() }
            }

        case .running(let input, let progress, let eta):
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Text("Processing: \(input.lastPathComponent)")
                        .foregroundColor(.secondary).lineLimit(1).truncationMode(.middle)
                    Spacer()
                    Text(progressLabel(progress: progress, eta: eta))
                        .monospacedDigit().foregroundColor(.secondary)
                    Button("Cancel") { processService.cancel() }
                }
                ProgressView(value: progress)
            }

        case .finished(let input, let outputPath):
            HStack(spacing: 8) {
                Image(systemName: "checkmark.circle.fill").foregroundColor(.green)
                Text("Done: \(input.lastPathComponent)").lineLimit(1).truncationMode(.middle)
                Spacer()
                Button("Reveal in Finder") {
                    NSWorkspace.shared.activateFileViewerSelecting([URL(fileURLWithPath: outputPath)])
                }
                Button("Process again") {
                    processService.reset()
                    startProcessing(url: currentURL, player: player)
                }
                .keyboardShortcut(.return, modifiers: [.command])
                .disabled(state.scriptPath == nil)
            }

        case .failed(let input, let message):
            VStack(alignment: .leading, spacing: 4) {
                HStack(spacing: 8) {
                    Image(systemName: "xmark.octagon.fill").foregroundColor(.red)
                    Text("Failed: \(input.lastPathComponent)").lineLimit(1).truncationMode(.middle)
                    Spacer()
                    Button("Dismiss") { processService.reset() }
                    Button("Try again") {
                        processService.reset()
                        startProcessing(url: currentURL, player: player)
                    }
                    .keyboardShortcut(.return, modifiers: [.command])
                    .disabled(state.scriptPath == nil)
                }
                Text(message)
                    .font(.caption)
                    .foregroundColor(.red)
                    .lineLimit(4)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .textSelection(.enabled)
            }
        }
    }

    private func progressLabel(progress: Double, eta: Double?) -> String {
        let pct = String(format: "%3.0f%%", progress * 100)
        guard let eta else { return pct }
        return "\(pct)  ·  ETA \(formatDuration(eta))"
    }

    private func formatDuration(_ seconds: Double) -> String {
        let s = Int(seconds.rounded())
        if s >= 3600 { return String(format: "%dh%02dm", s / 3600, (s % 3600) / 60) }
        if s >= 60   { return String(format: "%dm%02ds", s / 60, s % 60) }
        return String(format: "%ds", s)
    }

    // MARK: - Empty State

    private var emptyState: some View {
        VStack(spacing: 14) {
            Image(systemName: "film")
                .font(.system(size: 56))
                .foregroundColor(.secondary)
            Text("Open a video file").font(.title2)
            Text("Right-click a movie in Finder → Quick Actions → Karaoke Process v2")
                .foregroundColor(.secondary).font(.callout)
            Button("Open File…", action: openFile)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding()
    }

    private func openFile() {
        let panel = NSOpenPanel()
        panel.allowedContentTypes = [.movie, .mpeg4Movie, .quickTimeMovie]
        panel.allowsMultipleSelection = false
        if panel.runModal() == .OK, let url = panel.url {
            state.fileURL = url
        }
    }

    // MARK: - Actions

    private func initPlayer() {
        guard let url = state.fileURL else { return }
        player = AVPlayerWrapper(url: url)
    }

    private func userTouchedParameters() {
        if currentPreset != .custom {
            currentPreset = .custom
        }
    }

    private func refreshPreviews() {
        guard let url = state.fileURL,
              let scriptPath = state.scriptPath,
              let player else { return }
        let t = max(0, player.currentSeconds)
        isLoadingPreview = true
        statusNote = nil
        statusError = nil

        Task {
            do {
                let result = try await PreviewService.shared.generate(
                    scriptPath: scriptPath,
                    cacheDir: state.cacheDir,
                    input: url,
                    timeSeconds: t,
                    parameters: parameters
                )
                await MainActor.run {
                    self.maskedImage = result.masked
                    self.processedImage = result.processed
                    self.isLoadingPreview = false
                    self.statusNote = "Preview at t=\(String(format: "%.2f", t))s."
                }
            } catch {
                await MainActor.run {
                    self.isLoadingPreview = false
                    self.statusError = "Preview failed: \(error.localizedDescription)"
                }
            }
        }
    }

    private func startProcessing(url: URL, player: AVPlayerWrapper) {
        guard let scriptPath = state.scriptPath else { return }
        statusNote = nil
        statusError = nil
        processService.start(
            scriptPath: scriptPath,
            input: url,
            parameters: parameters,
            totalDurationSeconds: player.durationSeconds
        )
    }
}
