import Foundation
import AppKit

final class PreviewService {
    static let shared = PreviewService()

    struct PreviewError: LocalizedError {
        let message: String
        var errorDescription: String? { message }
    }

    func generate(
        scriptPath: String,
        cacheDir: URL,
        input: URL,
        timeSeconds: Double,
        parameters: ProcessingParameters
    ) async throws -> (masked: NSImage, processed: NSImage) {
        var args: [String] = [input.path]
        args += ["-f", String(format: "%.3f", max(0, timeSeconds))]
        args += parameters.cliArgs(includeIntroOutro: false)
        args += ["-o", cacheDir.path]

        let result = try await ShellRunner.run(executable: scriptPath, args: args)
        guard result.terminationStatus == 0 else {
            let tail = String(result.stderr.suffix(800))
            throw PreviewError(message: "exit \(result.terminationStatus). \(tail)")
        }
        let paths = parseCreatedPaths(stdout: result.stdout)
        guard paths.count >= 2 else {
            throw PreviewError(message: "Could not parse created PNG paths from script output.")
        }
        guard let masked = NSImage(contentsOfFile: paths[0]) else {
            throw PreviewError(message: "Could not load masked preview: \(paths[0])")
        }
        guard let processed = NSImage(contentsOfFile: paths[1]) else {
            throw PreviewError(message: "Could not load processed preview: \(paths[1])")
        }
        return (masked, processed)
    }

    private func parseCreatedPaths(stdout: String) -> [String] {
        var paths: [String] = []
        var inCreated = false
        for raw in stdout.components(separatedBy: "\n") {
            let line = raw.trimmingCharacters(in: .whitespacesAndNewlines)
            if line == "Created:" { inCreated = true; continue }
            if inCreated && !line.isEmpty {
                paths.append(line)
            }
        }
        return paths
    }
}

private final class PipeBuffers: @unchecked Sendable {
    private let queue = DispatchQueue(label: "ShellRunner.buffer")
    private var out = Data()
    private var err = Data()

    func appendOut(_ data: Data) { queue.async { self.out.append(data) } }
    func appendErr(_ data: Data) { queue.async { self.err.append(data) } }

    func finish(out outRemaining: Data, err errRemaining: Data) -> (String, String) {
        queue.sync {
            out.append(outRemaining)
            err.append(errRemaining)
            return (
                String(data: out, encoding: .utf8) ?? "",
                String(data: err, encoding: .utf8) ?? ""
            )
        }
    }
}

enum ShellRunner {
    struct Result {
        let terminationStatus: Int32
        let stdout: String
        let stderr: String
    }

    static func run(executable: String, args: [String]) async throws -> Result {
        try await withCheckedThrowingContinuation { (cont: CheckedContinuation<Result, Error>) in
            let process = Process()
            process.executableURL = URL(fileURLWithPath: executable)
            process.arguments = args
            process.environment = enrichedEnvironment()

            let outPipe = Pipe()
            let errPipe = Pipe()
            process.standardOutput = outPipe
            process.standardError = errPipe

            // Drain pipes incrementally. macOS pipe buffers are ~64 KB; ffmpeg dumps
            // input metadata to stderr on every invocation, and files with embedded
            // Serato/MixedInKey markers can produce 30-40 KB per call. The script
            // invokes ffmpeg twice for previews, so waiting until terminationHandler
            // to read deadlocks the child once the buffer fills.
            let buffers = PipeBuffers()
            outPipe.fileHandleForReading.readabilityHandler = { handle in
                let chunk = handle.availableData
                if chunk.isEmpty { return }
                buffers.appendOut(chunk)
            }
            errPipe.fileHandleForReading.readabilityHandler = { handle in
                let chunk = handle.availableData
                if chunk.isEmpty { return }
                buffers.appendErr(chunk)
            }

            process.terminationHandler = { proc in
                let outRemaining = outPipe.fileHandleForReading.readDataToEndOfFile()
                let errRemaining = errPipe.fileHandleForReading.readDataToEndOfFile()
                outPipe.fileHandleForReading.readabilityHandler = nil
                errPipe.fileHandleForReading.readabilityHandler = nil
                let (stdout, stderr) = buffers.finish(out: outRemaining, err: errRemaining)
                cont.resume(returning: Result(
                    terminationStatus: proc.terminationStatus,
                    stdout: stdout,
                    stderr: stderr
                ))
            }

            do {
                try process.run()
            } catch {
                outPipe.fileHandleForReading.readabilityHandler = nil
                errPipe.fileHandleForReading.readabilityHandler = nil
                cont.resume(throwing: error)
            }
        }
    }

    static func enrichedEnvironment() -> [String: String] {
        var env = ProcessInfo.processInfo.environment
        let extras = ["/opt/homebrew/bin", "/usr/local/bin", "/usr/bin", "/bin"]
        let cur = env["PATH"] ?? ""
        let merged = (extras + (cur.isEmpty ? [] : [cur])).joined(separator: ":")
        env["PATH"] = merged
        return env
    }
}
