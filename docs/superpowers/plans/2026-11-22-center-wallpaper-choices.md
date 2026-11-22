# Center Wallpaper Choices Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Center the four choices as one content-sized block.

**Architecture:** Put the vertical list in an inset-aware full-screen `FrameLayout`. Center the list, but leave each button’s compound drawable and text start-aligned.

**Tech Stack:** Kotlin, native Android views, Python smoke tests.

**Spec:** `docs/superpowers/specs/2026-11-22-center-wallpaper-choices-design.md`

## Global Constraints

- Keep the existing labels, icons, actions, error handling and build configuration.
- Preserve the black background and system bar insets.

## Review Focus

- Only the block is centered; shorter labels and their icons must not shift independently.
- Width must follow native measurements, including changes to font scale, rather than a hard-coded value.
- System bars must remain outside the usable centering area.

### Task 1: Center the content-sized list

**Files:** `tests/wallpaper_smoke.py`, `app/src/main/java/app/blackbg/Preview.kt`.

- [ ] Add `test_choice_block_centers_while_rows_stay_start_aligned` to check `FrameLayout.LayoutParams(WRAP_CONTENT, WRAP_CONTENT, Gravity.CENTER)`, that the activity displays the outer frame, and that rows retain `Gravity.START or Gravity.CENTER_VERTICAL`.
- [ ] Run `python3 tests/wallpaper_smoke.py`; expect the new layout test to fail because there is no centered frame.
- [ ] In `Preview.onCreate`, move background and inset handling onto the outer frame. Add the vertical list to the frame with content-sized dimensions and centered gravity. Keep equal row widths and preserve row internals and listeners.
- [ ] Run `python3 tests/wallpaper_smoke.py` (all tests pass), `git diff --check` and `./build-local.sh` (signed build succeeds). If a device is available, verify the two alignments with default and enlarged font and visible system bars; otherwise report the visual check as not run.
- [ ] Commit the separately verified layout change. Do not push or publish a release unless requested.
