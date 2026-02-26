---
phase: 01-foundation
plan: 02
subsystem: data-model
tags: [python, dataclasses, json, persistence, tdd, pytest]

# Dependency graph
requires:
  - phase: 01-01
    provides: Package skeleton with src/macro_thunder/ and models/, persistence/ subpackages
provides:
  - All 8 ActionBlock dataclasses (MouseMove, MouseClick, MouseScroll, KeyPress, Delay, WindowFocus, Label, Goto)
  - block_from_dict() dispatcher for JSON deserialization
  - MacroDocument dataclass (name, version, blocks)
  - save() and load() JSON persistence functions
  - default_macro_dir() returning ~/Documents/MacroThunder/
affects:
  - 01-03
  - 01-04
  - all subsequent phases (data model is the shared contract)

# Tech tracking
tech-stack:
  added:
    - pytest (test runner, installed into Python 3.14 env)
  patterns:
    - TDD (RED-GREEN) for data model and serializer
    - field(default="...", init=False) for type discriminator fields
    - _BLOCK_CLASSES registry + block_from_dict dispatcher pattern
    - dataclasses.asdict() for JSON serialization
    - MacroDocument.blocks is always a flat list (no nesting)

key-files:
  created:
    - src/macro_thunder/models/blocks.py
    - src/macro_thunder/models/document.py
    - src/macro_thunder/persistence/serializer.py
    - tests/test_serializer.py
  modified: []

key-decisions:
  - "type field declared as field(default=..., init=False) so block_from_dict strips it before calling cls(**kwargs)"
  - "block_from_dict raises KeyError on unknown type (no silent fallback)"
  - "load() raises ValueError with 'version' in message when version field missing"
  - "save() uses json.dumps(indent=2) and path.write_text(encoding=utf-8) — no extra dependencies"

patterns-established:
  - "TDD pattern: RED commit first, then GREEN commit after all tests pass"
  - "Discriminated union via _BLOCK_CLASSES dict — adding a new block type = add dataclass + add to dict"
  - "Serializer never stores nested documents — blocks list is always flat ActionBlock items"

requirements-completed: [FOUND-02, FOUND-03]

# Metrics
duration: 8min
completed: 2026-02-26
---

# Phase 1 Plan 02: ActionBlock Data Model and JSON Serializer Summary

**8-type ActionBlock discriminated union with block_from_dict dispatcher and JSON save/load using dataclasses.asdict(), fully TDD-tested with round-trip verification**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-02-26T11:22:38Z
- **Completed:** 2026-02-26T11:30:00Z
- **Tasks:** 2 (RED + GREEN)
- **Files modified:** 4

## Accomplishments
- All 8 ActionBlock dataclasses implemented with Literal type discriminators (init=False)
- block_from_dict dispatcher using _BLOCK_CLASSES registry — KeyError on unknown types
- MacroDocument dataclass with name, version, blocks fields and CURRENT_VERSION = 1
- JSON serializer: save() with 2-space indent, load() with version validation, default_macro_dir()
- 9 pytest tests passing: round-trip, edge cases, version guard, type field protection

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Write failing tests** - `83e72a1` (test)
2. **Task 2 (GREEN): Implement blocks.py, document.py, serializer.py** - `c7c551a` (feat)

## Files Created/Modified
- `src/macro_thunder/models/blocks.py` - All 8 ActionBlock dataclasses, ActionBlock union, _BLOCK_CLASSES dict, block_from_dict()
- `src/macro_thunder/models/document.py` - MacroDocument dataclass and CURRENT_VERSION = 1
- `src/macro_thunder/persistence/serializer.py` - save(), load(), default_macro_dir()
- `tests/test_serializer.py` - 9 pytest tests covering all block types, round-trip, and edge cases

## Decisions Made
- type field uses `field(default="...", init=False)` so dataclasses.asdict() includes it but cls(**kwargs) rejects it — block_from_dict strips it before dispatch
- block_from_dict raises KeyError for unknown type (no silent fallback, fail fast)
- load() raises ValueError with "version" in the message when version field is absent
- Python 3.14 is the installed runtime (despite pyproject.toml requiring >=3.12) — package installed with pip -e . and pytest installed directly

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Python launcher `py` defaulted to Python 3.14 (only installed version), not 3.12 as pyproject.toml targets. Python 3.14 is compatible for this plan's pure-Python code. pytest was not pre-installed and was added via pip install. No functional impact.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Data model contract is locked and tested — all subsequent phases can import from macro_thunder.models and macro_thunder.persistence
- 01-03 (UI scaffold) and 01-04 (pynput recorder) can now build on MacroDocument and ActionBlock types

---
*Phase: 01-foundation*
*Completed: 2026-02-26*
