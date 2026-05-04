import Foundation
import AppKit

final class ProcessService: ObservableObject {
    static let shared = ProcessService()

    enum Status: Equatable {
        case idle
        case starting(input: URL)
        case running(input: URL, progress: Double, etaSeconds: Double?)
        case finished(input: URL, outputPath: String)
        case failed(input: URL, message: String)
    }

    @Published private(set) var status: Status = .idle

    private var process: Process?
    private var stdoutPipe: Pipe?
    private var stderrPipe: Pipe?
    private var stderrTail: String = ""
    private var stdoutBuffer: String = ""
    private var totalDurationSec: Double = 0
    private var startTime: Date?
    private var detectedOutputPath: String?

    private static let timeRegex: NSRegularExpression = {
        try! NSRegularExpression(pattern: #"time=(\d+):(\d{2}):(\d{2}(?:\.\d+)?)"#)
    }()

    var isBusy: Bool {
        switch status {
        case .starting, .running: return true
        default: return false
        }
    }

    func reset() {
        status = .idle
        detectedOutputPath = nil
        stderrTail = ""
        stdoutBuffer = ""
        startTime = nil
    }

    func start(scriptPath: String, input: URL, parameters: ProcessingParameters, totalDurationSeconds: Double) {
        if isBusy { return }

        totalDurationSec = max(totalDurationSeconds, 0.001)
        startTime = Date()
        detectedOutputPath = nil
        stderrTail = ""
        stdoutBuffer = ""
        DispatchQueue.main.async { self.status = .starting(input: input) }

        var args = [input.path]
        args += parameters.cliArgs(includeSplash: true)

        let proc = Process()
        proc.executableURL = URL(fileURLWithPath: scriptPath)
        proc.arguments = args
        proc.environment = ShellRunner.enrichedEnvironment()

        let outPipe = Pipe()
        let errPipe = Pipe()
        proc.standardOutput = outPipe
        proc.standardError = errPipe

        outPipe.fileHandleForReading.readabilityHandler = { [weak self] handle in
            let data = handle.availableData
            if data.isEmpty { return }
            self?.handleStdoutChunk(data)
        }
        errPipe.fileHandleForReading.readabilityHandler = { [weak self] handle in
            let data = handle.availableData
            if data.isEmpty { return }
            self?.handleStderrChunk(data, input: input)
        }

        proc.terminationHandler = { [weak self] p in
            self?.handleTermination(input: input, exitCode: p.terminationStatus)
        }

        do {
            try proc.run()
            self.process = proc
            self.stdoutPipe = outPipe
            self.stderrPipe = errPipe
            DispatchQueue.main.async {
                self.status = .running(input: input, progress: 0, etaSeconds: nil)
            }
        } catch {
            DispatchQueue.main.async {
                self.status = .failed(input: input, message: error.localizedDescription)
            }
        }
    }

    func cancel() {
        process?.terminate()
    }

    private func handleStdoutChunk(_ data: Data) {
        guard let s = String(data: data, encoding: .utf8) else { return }
        stdoutBuffer += s
        while let nlRange = stdoutBuffer.range(of: "\n") {
            let line = String(stdoutBuffer[stdoutBuffer.startIndex..<nlRange.lowerBound])
                .trimmingCharacters(in: .whitespacesAndNewlines)
            stdoutBuffer.removeSubrange(stdoutBuffer.startIndex..<nlRange.upperBound)
            if line.hasPrefix("/") && (line.hasSuffix(".mp4") || line.hasSuffix(".png")) {
                detectedOutputPath = line
            }
        }
    }

    private func handleStderrChunk(_ data: Data, input: URL) {
        guard let s = String(data: data, encoding: .utf8) else { return }
        stderrTail.append(s)
        if stderrTail.count > 6000 { stderrTail = String(stderrTail.suffix(6000)) }

        guard let elapsed = parseLatestTime(from: s) else { return }
        let frac = min(max(elapsed / totalDurationSec, 0), 0.999)
        let eta: Double? = {
            guard let start = startTime, frac > 0.01 else { return nil }
            let wall = Date().timeIntervalSince(start)
            let estTotal = wall / frac
            return max(estTotal - wall, 0)
        }()
        DispatchQueue.main.async {
            if case .running = self.status {
                self.status = .running(input: input, progress: frac, etaSeconds: eta)
            }
        }
    }

    private func parseLatestTime(from chunk: String) -> Double? {
        let nsRange = NSRange(chunk.startIndex..., in: chunk)
        let matches = Self.timeRegex.matches(in: chunk, range: nsRange)
        guard let last = matches.last else { return nil }
        guard let h = Range(last.range(at: 1), in: chunk).flatMap({ Int(chunk[$0]) }),
              let m = Range(last.range(at: 2), in: chunk).flatMap({ Int(chunk[$0]) }),
              let s = Range(last.range(at: 3), in: chunk).flatMap({ Double(chunk[$0]) })
        else { return nil }
        return Double(h * 3600 + m * 60) + s
    }

    private func handleTermination(input: URL, exitCode: Int32) {
        // Drain remaining bytes (readabilityHandler may have stopped before EOF).
        if let outPipe = stdoutPipe {
            let remaining = outPipe.fileHandleForReading.readDataToEndOfFile()
            if !remaining.isEmpty { handleStdoutChunk(remaining) }
        }
        if let errPipe = stderrPipe {
            let remaining = errPipe.fileHandleForReading.readDataToEndOfFile()
            if !remaining.isEmpty { handleStderrChunk(remaining, input: input) }
        }
        stdoutPipe?.fileHandleForReading.readabilityHandler = nil
        stderrPipe?.fileHandleForReading.readabilityHandler = nil
        stdoutPipe = nil
        stderrPipe = nil
        process = nil

        DispatchQueue.main.async {
            if exitCode == 0, let outPath = self.detectedOutputPath {
                self.status = .finished(input: input, outputPath: outPath)
            } else if exitCode == 0 {
                self.status = .failed(input: input, message: "Script exited 0 but no output path was reported.")
            } else {
                let tail = String(self.stderrTail.suffix(1200)).trimmingCharacters(in: .whitespacesAndNewlines)
                self.status = .failed(input: input, message: "exit \(exitCode). \(tail)")
            }
        }
    }
}
