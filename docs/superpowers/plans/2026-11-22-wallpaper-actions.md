# Wallpaper Actions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the selector icon and four wallpaper actions to BlackBG.

**Architecture:** Keep the native Kotlin activity and apply black wallpaper via the existing background operation. Use Android vector drawables for the selector and all four rows.

**Tech Stack:** Kotlin, Android SDK 36+, XML vector drawables, Gradle.

**Spec:** `docs/superpowers/specs/2026-11-22-wallpaper-actions-design.md`

## Global Constraints

- Kotlin, `minSdk = 36`, `arm64-v8a` only, R8 and resource shrinking.
- No launcher entry, storage access, or reading or saving existing wallpapers.
- Signed release through `./build-local.sh`, key outside the repository (`~/.android/blackbg-release/`).

## Review Focus

- Single-target calls pass exactly the chosen flag. Android may derive the lock wallpaper from the home wallpaper when they share a background; do not work around that by reading or copying an old wallpaper.
- Cancel and system Back before applying leave both wallpapers unchanged.
- A denied or failed write shows the exact English error and restores the controls.
- Rapid repeat taps cannot queue another write while one is pending.
- System bars do not cover controls; icons add no separate accessibility focus.

### Task 1: Selector and action rows

**Files:** Modify `app/src/main/AndroidManifest.xml` and `app/src/main/java/app/blackbg/Preview.kt`; add `app/src/main/res/drawable/ic_wallpaper.xml`, `ic_lockscreen.xml`, `ic_homescreen.xml`, `ic_both.xml`, and `ic_cancel.xml` in the same drawable directory.

- [ ] Capture a failing smoke check on API 36+: open the wallpaper picker, verify the icon and exact ordered labels `Lockscreen`, `Homescreen`, `Both`, `Cancel`. Record the baseline mismatch. If no device is available, record that limitation and use a local structural check against the manifest and activity instead.
- [ ] Register `@drawable/ic_wallpaper` as the app icon without changing the intent filter. Draw all five disk icons with a black fill and thin white outline and the four specified white glyphs.
- [ ] Replace the current buttons with four accessible, minimum 48 dp native clickable rows, positioned by `Gravity.START or Gravity.CENTER_VERTICAL` in the inset-adjusted container. Keep icons and labels in a single focusable control per action.
- [ ] Route taps to `FLAG_LOCK`, `FLAG_SYSTEM`, both flags ORed together, or `finish()` without a write. Keep the existing support/permission and result checks, disable all rows during the asynchronous write, and on failure show `Couldn’t apply wallpaper.` and re-enable them.
- [ ] Run `./build-local.sh` and confirm a signed, optimized `arm64-v8a` APK. Repeat the smoke check. On a device with distinct home and lock backgrounds, check all three targets, Cancel, Back, repeated taps, and a policy-denied write if available. Inspect the rows with system bars visible and verify one focus stop per row. Report device checks that could not be run.
- [ ] Review the diff against the spec and commit the implementation files together.
