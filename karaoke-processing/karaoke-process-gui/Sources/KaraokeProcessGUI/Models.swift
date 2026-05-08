import Foundation

struct ProcessingParameters: Equatable, Codable {
    var topPct: Double = 5
    var bottomPct: Double = 15
    var leftPct: Double = 15
    var rightPct: Double = 5
    var lowThreshold: Double = 40
    var highThreshold: Double = 80
    var cornersOnly: Bool = false
    var invertBands: Bool = false
    var outlineN: Int = 2
    var splashEnabled: Bool = false
    var splashSeconds: Double = 5
    var zoomEnabled: Bool = false
    var zoomPercent: Double = 10
    var sungColor: String = "00C800"
    var bgDarkenEnabled: Bool = false
    var bgColor: String = "0040C0"
    var bgStrength: Double = 85
    var bgRange: Double = 35
    var bgBlend: Double = 10

    static let defaultSungColor = "00C800"
    static let defaultBgColor = "0040C0"

    init() {}

    enum CodingKeys: String, CodingKey {
        case topPct, bottomPct, leftPct, rightPct
        case lowThreshold, highThreshold
        case cornersOnly, invertBands, outlineN
        case splashEnabled, splashSeconds
        case zoomEnabled, zoomPercent
        case sungColor
        case bgDarkenEnabled, bgColor, bgStrength, bgRange, bgBlend
    }

    init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        self.topPct           = try c.decodeIfPresent(Double.self, forKey: .topPct)           ?? 5
        self.bottomPct        = try c.decodeIfPresent(Double.self, forKey: .bottomPct)        ?? 15
        self.leftPct          = try c.decodeIfPresent(Double.self, forKey: .leftPct)          ?? 15
        self.rightPct         = try c.decodeIfPresent(Double.self, forKey: .rightPct)         ?? 5
        self.lowThreshold     = try c.decodeIfPresent(Double.self, forKey: .lowThreshold)     ?? 40
        self.highThreshold    = try c.decodeIfPresent(Double.self, forKey: .highThreshold)    ?? 80
        self.cornersOnly      = try c.decodeIfPresent(Bool.self,   forKey: .cornersOnly)      ?? false
        self.invertBands      = try c.decodeIfPresent(Bool.self,   forKey: .invertBands)      ?? false
        self.outlineN         = try c.decodeIfPresent(Int.self,    forKey: .outlineN)         ?? 2
        self.splashEnabled    = try c.decodeIfPresent(Bool.self,   forKey: .splashEnabled)    ?? false
        self.splashSeconds    = try c.decodeIfPresent(Double.self, forKey: .splashSeconds)    ?? 5
        self.zoomEnabled      = try c.decodeIfPresent(Bool.self,   forKey: .zoomEnabled)      ?? false
        self.zoomPercent      = try c.decodeIfPresent(Double.self, forKey: .zoomPercent)      ?? 10
        self.sungColor        = try c.decodeIfPresent(String.self, forKey: .sungColor)        ?? Self.defaultSungColor
        self.bgDarkenEnabled  = try c.decodeIfPresent(Bool.self,   forKey: .bgDarkenEnabled)  ?? false
        self.bgColor          = try c.decodeIfPresent(String.self, forKey: .bgColor)          ?? Self.defaultBgColor
        self.bgStrength       = try c.decodeIfPresent(Double.self, forKey: .bgStrength)       ?? 85
        self.bgRange          = try c.decodeIfPresent(Double.self, forKey: .bgRange)          ?? 35
        self.bgBlend          = try c.decodeIfPresent(Double.self, forKey: .bgBlend)          ?? 10
    }

    func cliArgs(includeSplash: Bool) -> [String] {
        var args: [String] = []
        args += ["-t", "\(intStr(topPct))%"]
        args += ["-b", "\(intStr(bottomPct))%"]
        args += ["-l", "\(intStr(leftPct))%"]
        args += ["-r", "\(intStr(rightPct))%"]
        args += ["-lo", intStr(lowThreshold)]
        args += ["-hi", intStr(highThreshold)]
        if includeSplash, splashEnabled {
            args += ["-splash", String(format: "%.2f", splashSeconds)]
        }
        if zoomEnabled {
            args += ["-z", String(format: "%.2f", zoomPercent)]
        }
        if cornersOnly { args.append("--corners-only") }
        if invertBands { args.append("--invert-bands") }
        args += ["--outline", "\(outlineN)"]
        args += ["--sung-color", sungColor]
        if bgDarkenEnabled {
            args += ["--bg-color", bgColor]
            args += ["--bg-strength", intStr(bgStrength)]
            args += ["--bg-range", intStr(bgRange)]
            args += ["--bg-blend", intStr(bgBlend)]
        }
        return args
    }

    private func intStr(_ d: Double) -> String { "\(Int(d.rounded()))" }
}

enum CurrentPreset: Hashable {
    case custom
    case named(String)

    var label: String {
        switch self {
        case .custom: return "Custom"
        case .named(let s): return s
        }
    }
}
