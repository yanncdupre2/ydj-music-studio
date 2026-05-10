import SwiftUI
import AppKit

struct ParametersPanel: View {
    @Binding var parameters: ProcessingParameters
    @Binding var currentPreset: CurrentPreset
    @ObservedObject var presetStore: PresetStore
    @ObservedObject var player: AVPlayerWrapper
    let canRefresh: Bool
    let isRefreshing: Bool
    let onUserTouched: () -> Void
    let onRefresh: () -> Void

    var body: some View {
        VStack(spacing: 0) {
            HStack(alignment: .top, spacing: 0) {
                leftColumn
                    .padding(.horizontal, 12)
                    .frame(maxWidth: .infinity, alignment: .topLeading)
                Divider()
                rightColumn
                    .padding(.horizontal, 12)
                    .frame(maxWidth: .infinity, alignment: .topLeading)
            }
            .padding(.vertical, 8)

            Divider()
            refreshBar
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
        }
    }

    // MARK: - Left column: Mask + Zoom

    private var leftColumn: some View {
        VStack(alignment: .leading, spacing: 8) {
            sectionHeader("Margins (% of frame)")
            slider("Top",    binding: $parameters.topPct,    range: 0...50, step: 1, suffix: "%")
            slider("Bottom", binding: $parameters.bottomPct, range: 0...50, step: 1, suffix: "%")
            slider("Left",   binding: $parameters.leftPct,   range: 0...50, step: 1, suffix: "%")
            slider("Right",  binding: $parameters.rightPct,  range: 0...50, step: 1, suffix: "%")
            Toggle("Corners only", isOn: $parameters.cornersOnly)
                .onChange(of: parameters.cornersOnly) { _ in onUserTouched() }

            Divider().padding(.vertical, 2)

            sectionHeader("Background darken")
            HStack {
                Toggle("Enable", isOn: $parameters.bgDarkenEnabled)
                    .onChange(of: parameters.bgDarkenEnabled) { _ in onUserTouched() }
                Spacer()
                ColorPicker("Background color", selection: bgColorBinding, supportsOpacity: false)
                    .labelsHidden()
                    .disabled(!parameters.bgDarkenEnabled)
            }
            if parameters.bgDarkenEnabled {
                slider("Strength", binding: $parameters.bgStrength, range: 0...100, step: 1, suffix: "%")
                slider("Range",    binding: $parameters.bgRange,    range: 0...100, step: 1, suffix: "%")
                slider("Blend",    binding: $parameters.bgBlend,    range: 0...100, step: 1, suffix: "%")
            }

            Divider().padding(.vertical, 2)

            sectionHeader("Zoom")
            Toggle("Enable zoom", isOn: $parameters.zoomEnabled)
                .onChange(of: parameters.zoomEnabled) { _ in onUserTouched() }
            if parameters.zoomEnabled {
                slider("Amount", binding: $parameters.zoomPercent, range: -20...20, step: 1, suffix: "%")
            }
        }
    }

    // MARK: - Right column: LUT + Outline + Intro/Outro + Preset

    private var rightColumn: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                sectionHeader(parameters.applyLut ? "Luminance thresholds (0–255)" : "Black floor (0–255)")
                Spacer()
                Toggle("Apply LUT", isOn: $parameters.applyLut)
                    .onChange(of: parameters.applyLut) { _ in onUserTouched() }
            }
            slider("Low",  binding: $parameters.lowThreshold,  range: 0...255, step: 1, suffix: "")
            if parameters.applyLut {
                slider("High", binding: $parameters.highThreshold, range: 0...255, step: 1, suffix: "")
                HStack {
                    Toggle("Invert bands", isOn: $parameters.invertBands)
                        .onChange(of: parameters.invertBands) { _ in onUserTouched() }
                    Spacer()
                    Text("Sung color").font(.callout).foregroundColor(.secondary)
                    ColorPicker("Sung text color", selection: sungColorBinding, supportsOpacity: false)
                        .labelsHidden()
                }
            }

            Divider().padding(.vertical, 2)

            sectionHeader("Outline halo")
            Stepper(value: $parameters.outlineN, in: 0...20) {
                Text("N: \(parameters.outlineN)\(parameters.outlineN == 0 ? "  (off)" : "")")
            }
            .onChange(of: parameters.outlineN) { _ in onUserTouched() }

            Divider().padding(.vertical, 2)

            sectionHeader("Intro")
            Toggle("Apply intro effect", isOn: $parameters.introEnabled)
                .onChange(of: parameters.introEnabled) { newValue in
                    if newValue {
                        let captured = max(0.05, player.currentSeconds)
                        parameters.introSeconds = player.durationSeconds > 0
                            ? min(captured, max(0.05, player.durationSeconds - 0.05))
                            : captured
                    }
                    onUserTouched()
                }
            if parameters.introEnabled {
                HStack(spacing: 6) {
                    Text("Duration").frame(width: 60, alignment: .leading).font(.callout)
                    SplashSecondsField(value: $parameters.introSeconds, onCommit: onUserTouched)
                        .frame(width: 70)
                    Text("s").foregroundColor(.secondary).font(.callout)
                    Spacer()
                }
                Picker("", selection: $parameters.introMode) {
                    Text("Preserve").tag(IntroOutroMode.preserve)
                    Text("Blackout").tag(IntroOutroMode.blackout)
                }
                .pickerStyle(.radioGroup)
                .horizontalRadioGroupLayout()
                .labelsHidden()
                .onChange(of: parameters.introMode) { _ in onUserTouched() }
            }

            Divider().padding(.vertical, 2)

            sectionHeader("Outro")
            Toggle("Apply outro effect", isOn: $parameters.outroEnabled)
                .onChange(of: parameters.outroEnabled) { newValue in
                    if newValue {
                        let dur = player.durationSeconds
                        if dur > 0 {
                            let remaining = max(0.05, dur - player.currentSeconds)
                            parameters.outroSeconds = min(remaining, max(0.05, dur - 0.05))
                        }
                    }
                    onUserTouched()
                }
            if parameters.outroEnabled {
                HStack(spacing: 6) {
                    Text("Duration").frame(width: 60, alignment: .leading).font(.callout)
                    SplashSecondsField(value: $parameters.outroSeconds, onCommit: onUserTouched)
                        .frame(width: 70)
                    Text("s").foregroundColor(.secondary).font(.callout)
                    Spacer()
                }
                Picker("", selection: $parameters.outroMode) {
                    Text("Preserve").tag(IntroOutroMode.preserve)
                    Text("Blackout").tag(IntroOutroMode.blackout)
                }
                .pickerStyle(.radioGroup)
                .horizontalRadioGroupLayout()
                .labelsHidden()
                .onChange(of: parameters.outroMode) { _ in onUserTouched() }
            }

            Divider().padding(.vertical, 2)

            sectionHeader("Preset")
            presetMenu
        }
    }

    private var presetMenu: some View {
        Menu {
            Button { currentPreset = .custom } label: {
                HStack {
                    Image(systemName: currentPreset == .custom ? "checkmark" : "")
                        .frame(width: 12)
                    Text("Custom")
                }
            }
            if !presetStore.sortedNames.isEmpty {
                Divider()
                ForEach(presetStore.sortedNames, id: \.self) { name in
                    Button { applyPreset(name) } label: {
                        HStack {
                            Image(systemName: currentPreset == .named(name) ? "checkmark" : "")
                                .frame(width: 12)
                            Text(name)
                        }
                    }
                }
            }
            Divider()
            Button("Save current as preset…") { presentSaveDialog() }
            if case .named(let activeName) = currentPreset, presetStore.exists(activeName) {
                Button(role: .destructive) {
                    presentDeleteConfirmation(name: activeName)
                } label: {
                    Text("Delete preset “\(activeName)”…")
                }
            }
        } label: {
            HStack {
                Text(currentPreset.label).lineLimit(1).truncationMode(.middle)
                Spacer()
                Image(systemName: "chevron.up.chevron.down")
                    .font(.caption2).foregroundColor(.secondary)
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 4).padding(.horizontal, 6)
        }
        .menuStyle(.borderlessButton)
        .background(RoundedRectangle(cornerRadius: 6).stroke(Color.secondary.opacity(0.4)))
    }

    // MARK: - Bottom refresh bar

    private var refreshBar: some View {
        HStack(spacing: 14) {
            Button {
                onRefresh()
            } label: {
                Label("Refresh Previews", systemImage: "arrow.clockwise.circle.fill")
                    .font(.headline)
                    .padding(.horizontal, 18)
                    .padding(.vertical, 4)
            }
            .buttonStyle(.borderedProminent)
            .controlSize(.large)
            .disabled(!canRefresh || isRefreshing)
            .keyboardShortcut("r", modifiers: [.command])

            if isRefreshing {
                HStack(spacing: 6) {
                    ProgressView().controlSize(.small)
                    Text("Generating…").font(.callout).foregroundColor(.secondary)
                }
            } else {
                Text("⌘R").font(.caption).foregroundColor(.secondary)
            }

            Spacer()

            Text("t = \(formatPlayhead(player.currentSeconds))")
                .monospacedDigit()
                .foregroundColor(.secondary)
                .font(.callout)
        }
    }

    private func formatPlayhead(_ seconds: Double) -> String {
        let s = max(0, seconds)
        let m = Int(s) / 60
        let sec = s.truncatingRemainder(dividingBy: 60)
        return String(format: "%d:%05.2f", m, sec)
    }

    // MARK: - Helpers

    @ViewBuilder
    private func sectionHeader(_ text: String) -> some View {
        Text(text).font(.subheadline.weight(.semibold)).foregroundColor(.secondary)
    }

    private func slider(_ label: String,
                        binding: Binding<Double>,
                        range: ClosedRange<Double>,
                        step: Double,
                        suffix: String,
                        format: String = "%.0f") -> some View {
        HStack {
            Text(label).frame(width: 56, alignment: .leading).font(.callout)
            Slider(value: binding, in: range, step: step) { editing in
                if !editing { onUserTouched() }
            }
            Text("\(String(format: format, binding.wrappedValue))\(suffix)")
                .monospacedDigit()
                .frame(width: 50, alignment: .trailing)
                .foregroundColor(.secondary)
                .font(.callout)
        }
    }

    private var sungColorBinding: Binding<Color> {
        Binding<Color>(
            get: { Color(hex: parameters.sungColor) ?? Color(red: 0, green: 200/255, blue: 0) },
            set: { newColor in
                let hex = newColor.toHex() ?? ProcessingParameters.defaultSungColor
                if hex != parameters.sungColor {
                    parameters.sungColor = hex
                    onUserTouched()
                }
            }
        )
    }

    private var bgColorBinding: Binding<Color> {
        Binding<Color>(
            get: { Color(hex: parameters.bgColor) ?? Color(red: 0, green: 64/255, blue: 192/255) },
            set: { newColor in
                let hex = newColor.toHex() ?? ProcessingParameters.defaultBgColor
                if hex != parameters.bgColor {
                    parameters.bgColor = hex
                    onUserTouched()
                }
            }
        )
    }

    private func applyPreset(_ name: String) {
        guard let p = presetStore.parameters(for: name) else { return }
        var merged = p
        merged.introEnabled = parameters.introEnabled
        merged.introSeconds = parameters.introSeconds
        merged.introMode = parameters.introMode
        merged.outroEnabled = parameters.outroEnabled
        merged.outroSeconds = parameters.outroSeconds
        merged.outroMode = parameters.outroMode
        parameters = merged
        currentPreset = .named(name)
    }

    private func presentSaveDialog() {
        let suggestion: String? = {
            if case .named(let n) = currentPreset { return n }
            return nil
        }()
        if let name = PresetSaveDialog.runModal(presetStore: presetStore, suggestedName: suggestion) {
            var toSave = parameters
            toSave.introEnabled = false
            toSave.introSeconds = 5
            toSave.introMode = .preserve
            toSave.outroEnabled = false
            toSave.outroSeconds = 5
            toSave.outroMode = .preserve
            presetStore.save(name: name, parameters: toSave)
            currentPreset = .named(name)
        }
    }

    private func presentDeleteConfirmation(name: String) {
        guard PresetDeleteDialog.runConfirmation(name: name) else { return }
        presetStore.delete(name: name)
        currentPreset = .custom
    }
}

struct SplashSecondsField: View {
    @Binding var value: Double
    let onCommit: () -> Void

    @State private var text: String = ""

    var body: some View {
        TextField("", text: $text, onCommit: commit)
            .textFieldStyle(.roundedBorder)
            .multilineTextAlignment(.trailing)
            .monospacedDigit()
            .onAppear { text = formatted(value) }
            .onChange(of: value) { newValue in
                let formattedNew = formatted(newValue)
                if formattedNew != text { text = formattedNew }
            }
    }

    private func commit() {
        let cleaned = text.replacingOccurrences(of: ",", with: ".")
        if let v = Double(cleaned), v.isFinite, v > 0 {
            value = v
            text = formatted(v)
            onCommit()
        } else {
            text = formatted(value)
        }
    }

    private func formatted(_ v: Double) -> String {
        String(format: "%.2f", v)
    }
}

extension Color {
    init?(hex: String) {
        let cleaned = hex.replacingOccurrences(of: "#", with: "")
        guard cleaned.count == 6,
              let r = Int(cleaned.prefix(2), radix: 16),
              let g = Int(cleaned.dropFirst(2).prefix(2), radix: 16),
              let b = Int(cleaned.dropFirst(4).prefix(2), radix: 16)
        else { return nil }
        self.init(.sRGB,
                  red: Double(r) / 255.0,
                  green: Double(g) / 255.0,
                  blue: Double(b) / 255.0)
    }

    func toHex() -> String? {
        let nsColor = NSColor(self).usingColorSpace(.sRGB) ?? .systemGreen
        let r = max(0, min(255, Int((nsColor.redComponent * 255).rounded())))
        let g = max(0, min(255, Int((nsColor.greenComponent * 255).rounded())))
        let b = max(0, min(255, Int((nsColor.blueComponent * 255).rounded())))
        return String(format: "%02X%02X%02X", r, g, b)
    }
}
