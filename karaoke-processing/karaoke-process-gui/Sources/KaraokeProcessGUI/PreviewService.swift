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
        args += parameters.cliArgs(includeSplash: false)
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

            process.terminationHandler = { proc in
                let outData = outPipe.fileHandleForReading.readDataToEndOfFile()
                let errData = errPipe.fileHandleForReading.readDataToEndOfFile()
                let stdout = String(data: outData, encoding: .utf8) ?? ""
                let stderr = String(data: errData, encoding: .utf8) ?? ""
                cont.resume(returning: Result(
                    terminationStatus: proc.terminationStatus,
                    stdout: stdout,
                    stderr: stderr
                ))
            }

            do {
                try process.run()
            } catch {
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
