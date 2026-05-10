import Foundation

enum IntroOutroMode: String, Codable, Equatable {
    case preserve
    case blackout
}

struct ProcessingParameters: Equatable, Codable {
    var topPct: Double = 5
    var bottomPct: Double = 15
    var leftPct: Double = 15
    var rightPct: Double = 5
    var applyLut: Bool = true
    var lowThreshold: Double = 40
    var highThreshold: Double = 80
    var cornersOnly: Bool = false
    var invertBands: Bool = false
    var outlineN: Int = 2
    var introEnabled: Bool = false
    var introSeconds: Double = 5
    var introMode: IntroOutroMode = .preserve
    var outroEnabled: Bool = false
    var outroSeconds: Double = 5
    var outroMode: IntroOutroMode = .preserve
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
        case applyLut, lowThreshold, highThreshold
        case cornersOnly, invertBands, outlineN
        case introEnabled, introSeconds, introMode
        case outroEnabled, outroSeconds, outroMode
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
        self.applyLut         = try c.decodeIfPresent(Bool.self,   forKey: .applyLut)         ?? true
        self.lowThreshold     = try c.decodeIfPresent(Double.self, forKey: .lowThreshold)     ?? 40
        self.highThreshold    = try c.decodeIfPresent(Double.self, forKey: .highThreshold)    ?? 80
        self.cornersOnly      = try c.decodeIfPresent(Bool.self,   forKey: .cornersOnly)      ?? false
        self.invertBands      = try c.decodeIfPresent(Bool.self,   forKey: .invertBands)      ?? false
        self.outlineN         = try c.decodeIfPresent(Int.self,    forKey: .outlineN)         ?? 2
        self.introEnabled     = try c.decodeIfPresent(Bool.self,   forKey: .introEnabled)     ?? false
        self.introSeconds     = try c.decodeIfPresent(Double.self, forKey: .introSeconds)     ?? 5
        self.introMode        = try c.decodeIfPresent(IntroOutroMode.self, forKey: .introMode) ?? .preserve
        self.outroEnabled     = try c.decodeIfPresent(Bool.self,   forKey: .outroEnabled)     ?? false
        self.outroSeconds     = try c.decodeIfPresent(Double.self, forKey: .outroSeconds)     ?? 5
        self.outroMode        = try c.decodeIfPresent(IntroOutroMode.self, forKey: .outroMode) ?? .preserve
        self.zoomEnabled      = try c.decodeIfPresent(Bool.self,   forKey: .zoomEnabled)      ?? false
        self.zoomPercent      = try c.decodeIfPresent(Double.self, forKey: .zoomPercent)      ?? 10
        self.sungColor        = try c.decodeIfPresent(String.self, forKey: .sungColor)        ?? Self.defaultSungColor
        self.bgDarkenEnabled  = try c.decodeIfPresent(Bool.self,   forKey: .bgDarkenEnabled)  ?? false
        self.bgColor          = try c.decodeIfPresent(String.self, forKey: .bgColor)          ?? Self.defaultBgColor
        self.bgStrength       = try c.decodeIfPresent(Double.self, forKey: .bgStrength)       ?? 85
        self.bgRange          = try c.decodeIfPresent(Double.self, forKey: .bgRange)          ?? 35
        self.bgBlend          = try c.decodeIfPresent(Double.self, forKey: .bgBlend)          ?? 10
    }

    func cliArgs(includeIntroOutro: Bool) -> [String] {
        var args: [String] = []
        args += ["-t", "\(intStr(topPct))%"]
        args += ["-b", "\(intStr(bottomPct))%"]
        args += ["-l", "\(intStr(leftPct))%"]
        args += ["-r", "\(intStr(rightPct))%"]
        // -lo is reused as the floor threshold in --no-lut mode, so it always
        // applies. -hi is LUT-only.
        args += ["-lo", intStr(lowThreshold)]
        if applyLut {
            args += ["-hi", intStr(highThreshold)]
        }
        if includeIntroOutro, introEnabled {
            let flag = introMode == .blackout ? "--intro-blackout" : "--intro-preserve"
            args += [flag, String(format: "%.2f", introSeconds)]
        }
        if includeIntroOutro, outroEnabled {
            let flag = outroMode == .blackout ? "--outro-blackout" : "--outro-preserve"
            args += [flag, String(format: "%.2f", outroSeconds)]
        }
        if zoomEnabled {
            args += ["-z", String(format: "%.2f", zoomPercent)]
        }
        if cornersOnly { args.append("--corners-only") }
        if applyLut, invertBands { args.append("--invert-bands") }
        args += ["--outline", "\(outlineN)"]
        if applyLut {
            args += ["--sung-color", sungColor]
        }
        if bgDarkenEnabled {
            args += ["--bg-color", bgColor]
            args += ["--bg-strength", intStr(bgStrength)]
            args += ["--bg-range", intStr(bgRange)]
            args += ["--bg-blend", intStr(bgBlend)]
        }
        if !applyLut {
            args.append("--no-lut")
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
