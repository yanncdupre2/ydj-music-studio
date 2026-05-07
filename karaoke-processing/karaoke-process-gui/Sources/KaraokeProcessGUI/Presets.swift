import Foundation
import AppKit

final class PresetStore: ObservableObject {
    @Published private(set) var presets: [String: ProcessingParameters] = [:]
    private let storeURL: URL

    static let builtIns: [String: ProcessingParameters] = {
        var singKing = ProcessingParameters()
        singKing.topPct = 5; singKing.bottomPct = 15; singKing.leftPct = 15; singKing.rightPct = 5
        singKing.lowThreshold = 40; singKing.highThreshold = 80
        singKing.cornersOnly = false; singKing.invertBands = false
        singKing.outlineN = 2

        var musisi = ProcessingParameters()
        musisi.topPct = 5; musisi.bottomPct = 15; musisi.leftPct = 15; musisi.rightPct = 5
        musisi.lowThreshold = 24; musisi.highThreshold = 80
        musisi.cornersOnly = false; musisi.invertBands = false
        musisi.outlineN = 2

        return ["Sing King": singKing, "Musisi": musisi]
    }()

    init() {
        let support = FileManager.default
            .urls(for: .applicationSupportDirectory, in: .userDomainMask).first!
            .appendingPathComponent("KaraokeProcessGUI", isDirectory: true)
        try? FileManager.default.createDirectory(at: support, withIntermediateDirectories: true)
        self.storeURL = support.appendingPathComponent("presets.json")
        load()
    }

    var sortedNames: [String] {
        presets.keys.sorted { $0.localizedCaseInsensitiveCompare($1) == .orderedAscending }
    }

    func parameters(for name: String) -> ProcessingParameters? {
        presets[name]
    }

    func exists(_ name: String) -> Bool {
        presets[name] != nil
    }

    func save(name: String, parameters: ProcessingParameters) {
        presets[name] = parameters
        persist()
    }

    func delete(name: String) {
        guard presets.removeValue(forKey: name) != nil else { return }
        persist()
    }

    private func load() {
        guard let data = try? Data(contentsOf: storeURL),
              let decoded = try? JSONDecoder().decode([String: ProcessingParameters].self, from: data)
        else {
            presets = Self.builtIns
            persist()
            return
        }
        presets = decoded
    }

    private func persist() {
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        if let data = try? encoder.encode(presets) {
            try? data.write(to: storeURL, options: .atomic)
        }
    }
}

enum PresetSaveDialog {
    /// Returns the entered name on save, nil on cancel. Handles overwrite confirmation inline.
    static func runModal(presetStore: PresetStore, suggestedName: String? = nil) -> String? {
        let alert = NSAlert()
        alert.messageText = "Save Preset"
        alert.informativeText = "Enter a name. Reusing an existing name will overwrite that preset (with confirmation)."
        alert.alertStyle = .informational

        let textField = NSTextField(frame: NSRect(x: 0, y: 0, width: 260, height: 24))
        textField.placeholderString = "Preset name"
        textField.stringValue = suggestedName ?? ""
        alert.accessoryView = textField

        alert.addButton(withTitle: "Save")
        alert.addButton(withTitle: "Cancel")
        alert.window.initialFirstResponder = textField

        let response = alert.runModal()
        guard response == .alertFirstButtonReturn else { return nil }

        let name = textField.stringValue.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !name.isEmpty else { return nil }

        if presetStore.exists(name) {
            let confirm = NSAlert()
            confirm.messageText = "Overwrite preset “\(name)”?"
            confirm.informativeText = "A preset with this name already exists. Saving will replace it."
            confirm.alertStyle = .warning
            confirm.addButton(withTitle: "Overwrite")
            confirm.addButton(withTitle: "Cancel")
            if confirm.runModal() != .alertFirstButtonReturn { return nil }
        }
        return name
    }
}

enum PresetDeleteDialog {
    /// Returns true if the user confirmed deletion, false on cancel.
    static func runConfirmation(name: String) -> Bool {
        let alert = NSAlert()
        alert.messageText = "Delete preset “\(name)”?"
        alert.informativeText = "This permanently removes the preset. This action cannot be undone."
        alert.alertStyle = .warning
        alert.addButton(withTitle: "Delete")
        alert.addButton(withTitle: "Cancel")
        return alert.runModal() == .alertFirstButtonReturn
    }
}
