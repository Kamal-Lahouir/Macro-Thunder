# Feature Research

**Domain:** Windows desktop macro recorder — mouse/keyboard automation with GUI editor
**Researched:** 2026-02-25
**Confidence:** MEDIUM-HIGH (cross-validated across multiple competitor products and official documentation)

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete or broken.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Record mouse moves, clicks, scroll | Core function — reason the tool exists | LOW | pynput/pyWin32 handles raw capture; the challenge is filtering, not capturing |
| Record keyboard key presses | Every competitor has this; users expect it | LOW | Straightforward with pynput |
| Playback with timing fidelity | Macros must replay at the same speed they were recorded | MEDIUM | Timestamp replay vs. delay-between-action replay — both common |
| Repeat N times or infinite loop | Standard on every recorder including PyMacroRecord | LOW | Simple loop counter; stop hotkey required |
| Stop playback via hotkey | Without a kill switch, infinite loops are dangerous | LOW | Global hotkey (e.g., F6) registered even during playback |
| Save and load macros to disk | Users expect persistence; PyMacroRecord uses JSON | LOW | JSON is the correct choice — human-readable, shareable |
| Configurable playback speed | Every competitor (0.5x–25x range is standard) | LOW | Scale delays proportionally — not the timestamp math |
| Basic macro editor (list view) | Users expect to see and edit recorded actions | MEDIUM | A flat scrollable action list is the minimum; raw coordinate dumps are unacceptable UX |
| Delete/reorder/copy actions | Without edit operations, the editor is read-only, which is useless | MEDIUM | Drag-and-drop or up/down buttons; multi-select support |
| Action type: delay / wait | Users need to insert pauses (page load, animation wait) | LOW | Single duration field |
| Dark theme | Target audience (game users) strongly prefers dark themes | LOW | CSS/stylesheet choice; no functional complexity |
| Macro library panel | Users accumulate multiple macros; need to manage them | LOW | File list with names; load/delete operations |

**Confidence:** HIGH — present in all surveyed products (Macro Recorder, Jitbit, PyMacroRecord, Pulover's Macro Creator, Mini Mouse Macro)

---

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required by all users, but highly valued.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Mouse movement auto-grouping | Raw mouse data generates hundreds of lines per second; grouping makes editing tractable. Macro Recorder (macrorecorder.com) does this as a key feature. | HIGH | Must detect boundaries: group = consecutive move events between any non-move action. Core editing insight for game automation. |
| Group duration editing (proportional time scaling) | Users care about "how long did this path take," not individual coordinates. Scaling timestamps proportionally preserves the movement shape. | HIGH | Scale all timestamps in a group relative to a new total duration. Requires timestamp normalization logic. |
| Pixel threshold / movement filter on recording | Without filtering, recording produces thousands of micro-movement events that are noise. Threshold collapses sub-N-pixel jitter. | MEDIUM | Record into buffer; only emit event if Manhattan distance from last emitted point exceeds N pixels. N configurable (5–15px typical). |
| Visual block editor (action rows, not code) | Macro Recorder and Jitbit both highlight "no code" as differentiator. Text-script editors (AHK) alienate non-technical users. | MEDIUM | Each action = one structured row with type icon + fields. Not code. |
| Label + Goto flow control | Enables loops, retry logic, branching — without a full scripting language. Present in Macro Recorder's control commands. | MEDIUM | Label is a named no-op block. Goto jumps to label. Enough for most game automation flows. |
| Window Focus action with failure path | AutoIt's WinWait + WinActivate pattern. Match by executable + title substring. On timeout, jump to label instead of crashing. | HIGH | Requires Win32 FindWindow/EnumWindows + SetForegroundWindow. Title matching modes (contains/exact/starts-with) modeled after AutoIt's WinTitleMatchMode. |
| Interactive window picker ("Select Window...") | Eliminates manual trial-and-error finding executable names and window titles | MEDIUM | Click-to-capture: user clicks on running window, app fills executable + title fields automatically |
| Macro chaining ("Run macro" action) | Enables composition — shared utility macros called from multiple main macros | MEDIUM | Load and execute another saved macro file mid-playback. Dependency tracking needed to avoid circular references. |
| Configurable coordinates: absolute vs. relative | Jitbit's SMART-Rec uses relative coords. Absolute coords break when game window moves. Relative to window origin is the correct mode for game automation. | HIGH | Requires knowing window position at record time and subtracting from absolute coords. At playback, re-add window position. |
| Multi-select action blocks | Power users editing large macros need bulk delete/move operations | MEDIUM | Shift-click range select + Ctrl-click individual. Required for any macro over 50 actions. |
| Set window position/size on focus | Ensures game window is at expected screen position before actions execute — prevents coordinate drift | MEDIUM | Win32 MoveWindow + SetWindowPos |

**Confidence:** MEDIUM-HIGH — derived from Macro Recorder, AutoIt, Pulover's Macro Creator, and Jitbit feature documentation

---

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create complexity without proportional value for this specific use case.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Image recognition / visual click targeting | "What if the UI moves?" sounds compelling; Macro Recorder (macrorecorder.com) sells it as premium | Brittle across DPI, font rendering, anti-aliasing, GPU differences. High implementation cost. False positives. Game windows are fullscreen/fixed-position — the problem this solves doesn't exist for this use case. | Use relative-to-window coordinates + window focus action. The window is always at a known position after WinActivate. |
| Pixel color conditionals ("if pixel X,Y is red, goto label") | Power users ask for it; Jitbit has it | Fragile on game rendering pipelines — GPU, AA, HDR all shift pixel colors. High implementation complexity for low reliability. | Defer until validated as needed. Flag as v2+ if user feedback demands it. |
| If/Else conditional blocks (full branching) | Looks like scripting power; Pulover's Macro Creator has 200+ commands | For game automation, loops and window-check failure paths cover 90% of use cases. Full if/else leads to users writing unmaintainable spaghetti macros in a GUI editor. | Goto/label covers the needed branching. Conditional goto on window-not-found is the real requirement. |
| EXE compilation / distribution | "I want to share my macro" — Jitbit and Macro Scheduler offer this | Out of scope for personal-use tool. Adds packaging complexity, signing concerns, anti-cheat flag risk (compiled macro injectors get flagged by VAC/Vanguard). | Save JSON files. Sharing = share the JSON file. |
| Cloud sync / multi-device | Feature creep from productivity tool mindset | Adds auth, backend, and sync conflict complexity. Game automation is inherently single-machine. | Local file storage only. |
| AI-powered automation (OpenAI/Anthropic integration) | Macro Recorder enterprise tier sells this | Massive scope expansion. Requires internet dependency, API keys, cost. Entirely different product category. | Out of scope entirely. |
| Cross-platform support | "Why Windows only?" — PyMacroRecord is cross-platform | Win32 APIs (SetForegroundWindow, FindWindow, GetWindowRect) are the entire window management foundation. Cross-platform sacrifices the core differentiator. | Windows-only is a feature, not a limitation — it enables Win32 depth. |
| Scheduling (run at 8am daily) | Power Automate and Macro Scheduler offer this | Wrong use case. Game automation is manual-trigger, not scheduled. Adds complex background-service architecture. | Hotkey trigger is sufficient. |
| Record/replay in background windows | AutoHotkey control commands support background window interaction | Requires SendMessage/PostMessage Win32 injection — complex and game anti-cheat hostile. | Focus window before action. Window Focus block handles this. |
| Scripting language / code editor mode | AHK exports .ahk scripts; Jitbit allows C# snippets | The entire value proposition is "no code." Code mode is a different product. Mixing GUI and code creates incoherent UX. | Visual block editor only. Goto/label covers needed control flow. |

---

## Feature Dependencies

```
[Record mouse/keyboard]
    └──requires──> [Input capture library (pynput/pyWin32)]
                       └──enables──> [Pixel threshold filter]
                                         └──enables──> [Mouse move auto-grouping]

[Mouse move auto-grouping]
    └──requires──> [Record mouse/keyboard]
    └──enables──> [Group duration editing (proportional time scaling)]

[Group duration editing]
    └──requires──> [Mouse move auto-grouping]
    └──requires──> [Timestamp normalization math]

[Playback]
    └──requires──> [Save/load macros]
    └──requires──> [Record mouse/keyboard]
    └──enhances──> [Playback speed multiplier]
    └──enhances──> [Repeat N times / infinite loop]

[Stop hotkey]
    └──requires──> [Global hotkey registration]
    └──required-by──> [Repeat N times / infinite loop] (without stop = dangerous)

[Window Focus action]
    └──requires──> [Win32 FindWindow / EnumWindows]
    └──requires──> [Win32 SetForegroundWindow]
    └──requires──> [Label blocks] (failure path jumps to a label)
    └──enhances──> [Interactive window picker]

[Label blocks]
    └──required-by──> [Goto blocks]
    └──required-by──> [Window Focus action] (failure path destination)

[Goto blocks]
    └──requires──> [Label blocks]

[Macro chaining]
    └──requires──> [Save/load macros]
    └──requires──> [Playback engine]

[Relative coordinates]
    └──requires──> [Window position tracking at record time]
    └──requires──> [Window position lookup at playback time]
    └──enhances──> [Window Focus action] (window at known position post-focus)

[Multi-select]
    └──requires──> [Visual block editor]
    └──enhances──> [Delete/reorder/copy actions]
```

### Dependency Notes

- **Mouse move auto-grouping requires record first:** Grouping is a post-processing step on the raw recording. It cannot be implemented before recording works correctly.
- **Label blocks required before Goto and Window Focus:** The failure path of Window Focus jumps to a named label. Labels must exist before either feature ships.
- **Group duration editing requires grouping:** These are sequentially dependent — cannot edit group duration without groups existing.
- **Relative coordinates enhances Window Focus:** After WinActivate + SetWindowPos, the window is at a known position. Relative coordinates become reliable because the reference frame is predictable. These two features multiply each other's value.
- **Stop hotkey required with infinite loop:** Infinite loop without a kill switch is a product-breaking bug, not a missing feature. They must ship together.

---

## MVP Definition

### Launch With (v1)

Minimum viable product — what's needed to validate the core loop: record, edit, replay.

- [ ] Record mouse moves, clicks, scroll, keyboard — the core function
- [ ] Pixel threshold filter on recording — without this, the editor is unusable (hundreds of lines per second)
- [ ] Playback with timing fidelity — macros must replay correctly or the tool is worthless
- [ ] Playback speed multiplier — trivial complexity, immediate user value
- [ ] Repeat N times + stop hotkey — these ship as a pair; loops without stop are dangerous
- [ ] Visual block editor with list view — flat action list, each row editable
- [ ] Delete, reorder, copy/paste action blocks — minimum editing operations
- [ ] Mouse move auto-grouping — the core editing insight; without this, editing recorded macros is unworkable
- [ ] Group duration editing with proportional time scaling — this IS the value of grouping; useless without it
- [ ] Save/load macros (JSON) — persistence is required; without this, every session starts over
- [ ] Macro library panel — list of saved macros, load/delete
- [ ] Dark theme UI — non-negotiable for the target audience

### Add After Validation (v1.x)

Features to add once core record-edit-replay loop is proven.

- [ ] Label blocks + Goto — when users start running macros that need retry logic or loops within the macro itself
- [ ] Window Focus action + Interactive window picker — when users report macros breaking due to window position changes; this is the most requested power feature
- [ ] Set window position/size on focus — natural extension of Window Focus once that block exists
- [ ] Multi-select action blocks — when macros grow large and single-action editing becomes painful
- [ ] Macro chaining ("Run macro" action) — when users want to compose reusable utility macros

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] Relative-to-window coordinates — high value but high implementation cost; validate first that users are hitting absolute-coordinate drift problems
- [ ] Conditional goto (if pixel color / if window exists) — validate demand before building; pixel color conditionals are fragile for game automation

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Record mouse/keyboard | HIGH | LOW | P1 |
| Pixel threshold filter | HIGH | MEDIUM | P1 |
| Playback + speed | HIGH | LOW | P1 |
| Repeat N times + stop hotkey | HIGH | LOW | P1 |
| Visual block editor | HIGH | MEDIUM | P1 |
| Mouse move auto-grouping | HIGH | HIGH | P1 |
| Group duration editing | HIGH | HIGH | P1 |
| Save/load JSON | HIGH | LOW | P1 |
| Dark theme | MEDIUM | LOW | P1 |
| Macro library panel | MEDIUM | LOW | P1 |
| Delete/reorder/copy actions | HIGH | MEDIUM | P1 |
| Label + Goto flow control | HIGH | MEDIUM | P2 |
| Window Focus action | HIGH | HIGH | P2 |
| Interactive window picker | MEDIUM | MEDIUM | P2 |
| Multi-select action blocks | MEDIUM | MEDIUM | P2 |
| Macro chaining | MEDIUM | MEDIUM | P2 |
| Set window position/size | MEDIUM | LOW | P2 |
| Relative coordinates | HIGH | HIGH | P3 |
| Conditional goto (pixel color) | MEDIUM | HIGH | P3 |
| Image recognition click | LOW | VERY HIGH | NEVER |
| EXE compilation | LOW | HIGH | NEVER |
| Cloud sync | LOW | VERY HIGH | NEVER |
| AI integration | LOW | VERY HIGH | NEVER |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration
- NEVER: Deliberate anti-feature for this product

---

## Competitor Feature Analysis

| Feature | Macro Recorder (macrorecorder.com) | Jitbit Macro Recorder | PyMacroRecord | AutoIt / Pulover's | Our Approach |
|---------|-------------------------------------|----------------------|---------------|---------------------|--------------|
| Mouse recording | Yes — raw capture | Yes — SMART-Rec relative coords | Yes — fluid recording | Yes — scripted | Record raw, filter by pixel threshold |
| Movement consolidation | YES — key differentiator; groups moves between clicks | Partial — relative coord mode | No — all events recorded | N/A — scripted | Auto-group consecutive moves; threshold filter at capture time |
| Group duration editing | Partial — editing exists but basic | No | No | No | Core feature — proportional scaling of all timestamps in group |
| Playback speed | Yes (variable) | Yes (variable) | Yes | Yes | Yes — simple delay scaling |
| Flow control | Goto, Repeat, If-Then-Else, Window Focus | If-Then, Repeat, Wait-for-window | None | Full scripting (200+ commands) | Goto + Label + Window Focus failure path |
| Window management | Window Focus + restore position/size | Wait-for-window, detect position change | None | WinWait + WinActivate + WinTitleMatchMode | Window Focus: exe + title matching (contains/exact/starts-with) + failure path to label |
| Editor UX | Visual step list, no code | Visual editor + C# snippets | Minimal (record + play buttons) | Full scripting IDE | Visual block list — each action = one structured row, no code |
| Image recognition | YES — premium differentiator | YES — pixel color | No | YES — image search | NEVER — fragile, out of scope for fixed-position game windows |
| Macro chaining | YES — embed macro files | No | No | Yes via functions | "Run macro" action block — v1.x |
| File format | Proprietary .mrf | Proprietary | JSON | .ahk script | JSON — human-readable, shareable |
| Price | Paid | Paid | Free/open source | Free/open source | Personal use — no licensing |

---

## Sources

- [Macro Recorder (macrorecorder.com)](https://www.macrorecorder.com/) — mouse consolidation, visual path overlay, flow control documentation
- [Macro Recorder Control Commands](https://www.macrorecorder.com/doc/control/) — Goto, Repeat, If-Then-Else, Window Focus, Embed Macro
- [Jitbit Macro Recorder](https://www.jitbit.com/macro-recorder/) — SMART-Rec relative coords, If-Then, pixel color, EXE compilation
- [PyMacroRecord (GitHub)](https://github.com/LOUDO56/PyMacroRecord) — open source Python baseline, JSON format
- [Pulover's Macro Creator](https://www.macrocreator.com/) — 200 commands, AHK export, If/Else, window control
- [AutoIt WinActivate](https://www.autoitscript.com/autoit3/docs/functions/WinActivate.htm) — WinTitleMatchMode, WinWait, WinActivate patterns
- [AutoIt Window Titles (Advanced)](https://www.autoitscript.com/autoit3/docs/intro/windowsadvanced.htm) — partial/substring/exact matching modes
- [macrorecorder.org — Limitations of Macro Recorders](https://macrorecorder.org/2024/10/26/what-are-the-limitations-of-a-macro-recorder/) — coordinate fragility, DPI issues
- [Macro Scheduler Image Recognition](https://www.mjtnet.com/blog/2007/02/20/how-to-use-image-recognition/) — pixel tolerance, false positive risks
- [AutoHotkey vs Jitbit comparison](https://appmus.com/vs/autohotkey-vs-jitbit-macro-recorder) — code-required vs GUI-driven tradeoffs
- [Anti-cheat and macro detection analysis](https://attackshark.com/blogs/knowledges/anti-cheat-rapid-trigger-hardware-detection-guide) — behavioral analysis, injection detection

---

*Feature research for: Windows desktop macro recorder (Python, game automation focus)*
*Researched: 2026-02-25*
