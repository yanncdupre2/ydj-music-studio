import SwiftUI
import AVKit
import AppKit
import Combine

struct AVPlayerViewRepresentable: NSViewRepresentable {
    let player: AVPlayer

    func makeNSView(context: Context) -> AVPlayerView {
        let view = AVPlayerView()
        view.player = player
        view.controlsStyle = .inline
        view.showsFullScreenToggleButton = false
        view.allowsPictureInPicturePlayback = false
        return view
    }

    func updateNSView(_ nsView: AVPlayerView, context: Context) {
        if nsView.player !== player {
            nsView.player = player
        }
    }
}

final class AVPlayerWrapper: ObservableObject {
    let player: AVPlayer
    @Published var currentSeconds: Double = 0
    @Published var durationSeconds: Double = 0
    @Published var videoAspectRatio: Double = 16.0 / 9.0
    private var observer: Any?

    init(url: URL) {
        let asset = AVURLAsset(url: url)
        let item = AVPlayerItem(asset: asset)
        self.player = AVPlayer(playerItem: item)
        let interval = CMTime(seconds: 0.1, preferredTimescale: 600)
        observer = player.addPeriodicTimeObserver(forInterval: interval, queue: .main) { [weak self] time in
            let s = time.seconds
            self?.currentSeconds = s.isFinite ? s : 0
        }
        Task { [weak self] in
            if let dur = try? await asset.load(.duration) {
                let s = dur.seconds
                if s.isFinite, s > 0 {
                    await MainActor.run { [weak self] in
                        self?.durationSeconds = s
                    }
                }
            }
            if let tracks = try? await asset.loadTracks(withMediaType: .video),
               let track = tracks.first,
               let naturalSize = try? await track.load(.naturalSize),
               let xform = try? await track.load(.preferredTransform) {
                let displayed = naturalSize.applying(xform)
                let w = abs(displayed.width)
                let h = abs(displayed.height)
                if w > 0, h > 0 {
                    let ratio = Double(w / h)
                    await MainActor.run { [weak self] in
                        self?.videoAspectRatio = ratio
                    }
                }
            }
        }
    }

    deinit {
        if let observer { player.removeTimeObserver(observer) }
    }

    var currentTimeFormatted: String {
        let s = max(0, currentSeconds)
        let m = Int(s) / 60
        let sec = s.truncatingRemainder(dividingBy: 60)
        return String(format: "%d:%05.2f", m, sec)
    }
}

struct VideoPanel: View {
    @ObservedObject var player: AVPlayerWrapper

    var body: some View {
        ZStack {
            Color.black
            AVPlayerViewRepresentable(player: player.player)
                .aspectRatio(player.videoAspectRatio, contentMode: .fit)
                .overlay(Rectangle().stroke(Color.white, lineWidth: 2))
                .padding(6)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}
