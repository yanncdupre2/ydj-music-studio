# YDJ Music Studio

## Status
- [x] Planning
- [ ] In Progress
- [ ] On Hold
- [ ] Completed

## Project Metadata
- **Project Number:** 02
- **Folder:** `ydj-music-studio` (permanent identifier)
- **Original Name:** DJ Music Library Manager
- **Current Name:** YDJ Music Studio
- **Status:** Planning
- **Created:** 2026-02-13
- **GitHub:** https://github.com/fydupre/ydj-music-studio

## Vision and Scope

A comprehensive DJ music production and library management system encompassing three interconnected domains:

1. **Intelligent Playlist Optimization** - Harmonic mixing and BPM continuity using Camelot wheel system and simulated annealing
2. **Automated Library Management** - Metadata tagging, cleanup, and LLM-powered genre categorization for Apple Music library
3. **Efficient Media Processing** - YouTube download conversion and optimization for Apple ecosystem compatibility

### In Scope
- Harmonic mixing optimizer using Camelot wheel and key shifting
- Apple Music library XML parsing and metadata analysis
- Duplicate/discrepancy detection and cleanup workflows
- Genre taxonomy with 31 compound categories (e.g., "EDM, House, Techno")
- YouTube media processing (MKV→MP4, Opus→AAC conversion)
- File renaming based on metadata tags
- Safe read-only Apple Music integration (initial phase)

### Out of Scope (Initial Release)
- Direct Apple Music library write operations (deferred to Phase 4 for safety)
- Real-time DJ performance tools or live mixing
- Music streaming service integration beyond metadata lookup
- Mobile apps or web interfaces
- Collaborative playlist features

## Problem Statement

As an amateur DJ (YDJ), maintaining an organized music library and creating compelling mixes involves several time-consuming challenges:

**Library Management:**
- Tracks often have missing or incorrect metadata (year, genre, BPM, key)
- Manual tagging is tedious and error-prone
- Genre classification is subjective; need consistent taxonomy (solution: compound genres)
- Apple Music's native tools are limited for bulk operations
- Duplicate/similar tracks have inconsistent tagging across library

**Playlist Optimization:**
- Creating harmonically mixed sets manually is extremely time-consuming
- Balancing BPM continuity with harmonic compatibility is complex optimization problem
- No efficient way to optimize track order for flow and energy
- Current Python mixer script works but is slow (tens of minutes for 30-song playlist)

**Media Processing:**
- YouTube downloads recently changed from .mp4 to .mkv format
- Need efficient batch conversion to Apple-compatible formats (MP4/M4A)
- Want quick preview capability on macOS (QuickLook doesn't support MKV well)

## Strategy and Phases

### Phase 1: Foundation & Organization (Current)
**Goal:** Establish clean modular structure and migrate existing tools

- Organize existing scripts into modular subfolder structure
- Extract canonical 31-genre taxonomy from library to `common/genres.json`
- Create shared Apple Music XML reader in `common/`
- Set up Git repository and push to GitHub
- Create fresh Python virtual environment with requirements.txt
- Move existing YDJ folder contents into organized structure

**Success Criteria:**
- Clean separation: mixer/, library-management/, downloads/, common/
- Each subfolder has focused CLAUDE.md for AI agent context
- All existing scripts functional in new structure

### Phase 2: Library Management Enhancement
**Goal:** Improve metadata quality and consistency across library

- Audit library metadata quality (missing years, genres, BPMs, keys)
- Enhance cleanup.py for interactive discrepancy resolution
- LLM-powered genre auto-tagging using canonical 31-genre taxonomy
- Batch year lookup from online databases (MusicBrainz, Discogs)
- BPM detection and tagging for tracks missing tempo data

**Success Criteria:**
- <5% of library missing year or genre
- Consistent genre categorization using compound taxonomy
- Interactive cleanup workflow for resolving discrepancies

### Phase 3: Mixer Improvements
**Goal:** Make playlist optimization more seamless and practical

- Dynamic playlist management (read from Apple Music playlists, not hardcoded arrays)
- Better visualization of optimization results (transition costs, flow chart)
- Export optimized playlist back to Apple Music
- Performance profiling and Python-level optimization
- Command-line interface with progress reporting

**Success Criteria:**
- Optimize playlist directly from Apple Music playlist name
- Export results back to Apple Music as new playlist
- Improve performance by 2-3x through algorithmic optimization

### Phase 4: Safe Apple Music Write Testing
**Goal:** Enable direct library modification without risk

- Research AppleScript/JXA capabilities for Apple Music
- Create isolated test library for experimentation
- Implement safe write operations with validation and rollback
- Extensive testing on test library
- Gradual rollout to production library with backup requirements

**Success Criteria:**
- Can safely update track metadata (year, genre, BPM, key) via AppleScript
- Validation ensures no data corruption
- Backup/restore workflow documented and tested

### Phase 5: Rust Performance Engine (Future)
**Goal:** 10-100x performance improvement for large playlists

- Port mixer optimization core to Rust
- Maintain Python wrapper for ease of use and integration
- Target: 30-song optimization in seconds (vs. current tens of minutes)
- Benchmark and validate against Python implementation

**Success Criteria:**
- Rust engine produces identical results to Python version
- 10x+ performance improvement on typical 20-30 song playlists
- Seamless integration with existing Python tooling

## Key Decisions and Rationale

### Decision: Compound Genre Taxonomy
**Context:** Is a song "House" or "Techno"? Classification ambiguity causes inconsistency.

**Decision:** Use compound genres exactly as they appear in library (e.g., "EDM, House, Techno", "New-Wave, Techno-Pop, Electro-Pop, Synth-Pop")

**Rationale:**
- Solves classification ambiguity by design (both House AND Techno)
- Reflects actual music overlap (Depeche Mode = New-Wave, CHVRCHES = Synth-Pop, but very similar music)
- Enables LLMs to categorize without forcing false precision
- 31 canonical genres cover 95%+ of library

**Alternatives Considered:**
- Single-genre per track: Rejected due to classification difficulty
- Hierarchical taxonomy: Too complex, doesn't reflect DJ use case
- Free-form tags: Too inconsistent for filtering/searching

### Decision: XML Export (Read-Only) Before Direct AppleScript Integration
**Context:** Need to read/write Apple Music library metadata safely.

**Decision:** Start with XML export (read-only), defer direct write operations to Phase 4.

**Rationale:**
- Safety first: Don't risk corrupting production music library (10,000+ tracks)
- XML export is well-tested, reliable, and low-risk
- Allows development of library management tools without write risk
- AppleScript testing can happen in isolation with test library

**Alternatives Considered:**
- Direct AppleScript from start: Rejected as too risky without testing
- File-level metadata editing: Rejected because Apple Music uses proprietary database

### Decision: Python First, Rust Later for Mixer
**Context:** Current Python mixer is slow but works.

**Decision:** Enhance Python implementation first (Phase 3), port to Rust later (Phase 5).

**Rationale:**
- Python mixer is functional; performance is acceptable for now
- Focus on user experience improvements first (dynamic playlists, visualization)
- Rust port is significant effort; defer until Python version is feature-complete
- Performance optimization at Python level (algorithmic) may be sufficient

### Decision: Modular Structure with Subfolder AI Context
**Context:** Project has three distinct domains (mixer, library, downloads).

**Decision:** Separate into subfolders, each with its own CLAUDE.md for focused AI agent context.

**Rationale:**
- Clean separation of concerns
- Enables focused AI assistance within each domain
- Common utilities shared via common/ folder
- Each domain can evolve independently

## Risks and Dependencies

### Risks
1. **Apple Music Library Corruption**
   - Mitigation: Read-only XML approach initially; extensive testing in Phase 4; backup requirements
   - Impact: High (could lose metadata for entire library)

2. **Genre Taxonomy Drift**
   - Risk: Over time, new genres added inconsistently
   - Mitigation: LLM auto-tagging enforces canonical 31-genre list; periodic audits

3. **Mixer Performance Bottleneck**
   - Risk: Python optimization may not be sufficient; Rust port required sooner
   - Mitigation: Performance profiling in Phase 3; consider algorithmic improvements first

4. **AppleScript API Limitations**
   - Risk: AppleScript may not support all metadata fields we need
   - Mitigation: Research in Phase 4; fallback to XML workflow if necessary

### Dependencies
- **Apple Music**: macOS-specific; project tied to Apple ecosystem
- **ffmpeg/ffprobe**: Required for media processing; must be installed via Homebrew
- **Python 3.x**: Core scripting language for automation
- **Apple Music XML Export**: Manual export required; need to keep up-to-date

### External APIs (Future Phases)
- MusicBrainz API (release dates, genres)
- Discogs API (vinyl/DJ metadata)
- Spotify API (audio features, genres)
- Last.fm API (genre tags, similar artists)

## Success Criteria

### Phase 1 (Foundation)
- ✅ Clean modular structure (mixer/, library-management/, downloads/, common/)
- ✅ Genre taxonomy extracted and stored in `common/genres.json`
- ✅ Git repository initialized and pushed to GitHub
- ✅ All existing scripts functional in new structure

### Phase 2 (Library Management)
- <5% of library missing critical metadata (year, genre)
- Duplicate detection identifies all track variants
- LLM genre tagging achieves 90%+ agreement with manual tagging
- Interactive cleanup workflow handles 20+ discrepancies/minute

### Phase 3 (Mixer)
- Optimize playlist from Apple Music playlist name (no hardcoding)
- Export results back to Apple Music as new playlist
- 2-3x performance improvement (10-15 minutes for 30 songs)
- Visual flow chart shows harmonic/tempo transitions

### Phase 4 (Safe Write)
- Zero data loss or corruption incidents in test library (100+ write operations)
- Backup/restore workflow tested and documented
- Production library updates validated against XML export

### Phase 5 (Rust Engine)
- 10x+ performance improvement (30 songs in <3 minutes)
- Bit-identical optimization results vs. Python
- Seamless Python wrapper integration

## Open Questions

1. **Genre Taxonomy Evolution**
   - How do we handle new music styles not covered by 31 canonical genres?
   - Should we periodically review and expand taxonomy, or enforce strict list?

2. **Playlist Management**
   - What's the best UX for specifying which playlist to optimize? (CLI arg, interactive picker, config file?)
   - Should mixer support multiple playlists in one run?

3. **Apple Music Integration**
   - Can AppleScript reliably handle all metadata fields we need (year, genre, BPM, key, comments)?
   - What's the safe concurrency model for batch updates (one-at-a-time, batched, transactional)?

4. **MusicBrainz/Discogs Integration**
   - Which API provides better metadata for DJ-oriented music (electronic, house, techno)?
   - How to handle API rate limits for large batch operations?

5. **Performance Target**
   - What's the acceptable optimization time for a 30-song playlist? (Current: ~30 min, Python optimized: ~10 min?, Rust: <3 min?)
   - Is Rust port worth the effort if Python can achieve 10-minute runtime?

## Resources & References

- [Apple Music AppleScript Dictionary](https://developer.apple.com/library/archive/documentation/AppleScript/Conceptual/AppleScriptLangGuide/)
- [MusicBrainz API Documentation](https://musicbrainz.org/doc/MusicBrainz_API)
- [Discogs API Documentation](https://www.discogs.com/developers)
- [Mutagen Library](https://mutagen.readthedocs.io/) - Python audio metadata
- [beets.io](https://beets.io/) - Reference music library manager
- [Camelot Wheel](https://en.wikipedia.org/wiki/Camelot_Wheel) - Harmonic mixing system
- [ffmpeg Documentation](https://ffmpeg.org/documentation.html)

## Notes

- **Genre Philosophy**: Compound genres solve the "is it House or Techno?" problem by allowing both
- **Safety First**: Read-only XML approach until AppleScript is thoroughly tested
- **Performance**: Python mixer works but is slow; Rust is future optimization, not immediate blocker
- **Backup**: Always backup Apple Music library before any batch metadata operations
