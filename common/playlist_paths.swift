// Print the tracks of an Apple Music playlist as TSV lines: name, artist, POSIX path.
//
// Reads the library database through Apple's iTunesLibrary framework, which is
// orders of magnitude faster than asking Music.app for `location` over Apple
// Events (~0.2 s per track). Missing files print an empty path.
//
// Usage: swift common/playlist_paths.swift "MASTER LIST DJ VIDEO"

import Foundation
import iTunesLibrary

guard CommandLine.arguments.count == 2 else {
    FileHandle.standardError.write("usage: playlist_paths.swift PLAYLIST_NAME\n".data(using: .utf8)!)
    exit(2)
}
let name = CommandLine.arguments[1]

do {
    let library = try ITLibrary(apiVersion: "1.0")
    guard let playlist = library.allPlaylists.first(where: { $0.name == name }) else {
        FileHandle.standardError.write("playlist not found: \(name)\n".data(using: .utf8)!)
        exit(1)
    }
    for item in playlist.items {
        let fields = [item.title, item.artist?.name ?? "", item.location?.path ?? ""]
        print(fields.map { $0.replacingOccurrences(of: "\t", with: " ") }.joined(separator: "\t"))
    }
} catch {
    FileHandle.standardError.write("cannot open library: \(error)\n".data(using: .utf8)!)
    exit(1)
}
