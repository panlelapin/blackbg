# BlackBG audit fixes implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Correct all findings from the 1.0.1 review and verify the signed APK.

**Architecture:** Keep a native Kotlin activity observing a retained asynchronous write. Stream a solid black image to the wallpaper service. Select and validate signing identity before invoking Gradle.

**Tech Stack:** Android SDK 36+, Kotlin, POSIX sh, Gradle, Python/ADB.

**Spec:** `docs/superpowers/specs/2026-11-22-audit-fixes-design.md`

## Global Constraints
Keep `app.blackbg`, `arm64-v8a`, R8, resource shrinking, no launcher, no storage permission and no reading previous wallpaper. Keep the official key outside the repository.

## Review Focus
Partial key restore; wrong official certificate; Back or rotation during an accepted write; scrollability under cutouts; dependency findings masked by inspecting only the runtime classpath.

### 1. Signing
- [ ] Add `tests/test_signing.py`: temporary identities and directories must prove refusal of missing/partial/wrong official credentials, private personal initialization and signer reuse.
- [ ] Run `python3 -B -m unittest discover -s tests -p test_signing.py -v` against baseline for red, then against the fix.
- [ ] Update `build-local.sh` and `app/build.gradle.kts`: `--personal` uses distinct keys and output; default requires published certificate. Validate the resulting APK certificate. Document both modes and personal migration in `README.md`.

### 2. Android behavior
- [ ] Add device regression checks under `tests/` using a picker caller on a disposable emulator. Assert cancel/back before write, correct target IDs, Back during write, recreation, failure/retry and small window scrolling. Capture baseline failures.
- [ ] In `app/src/main/java/app/blackbg/Preview.kt` retain one operation through configuration changes, deliver its result only to the current preview, consume Back while pending, and use a scrolling inset-aware column. Supply a memory-bounded opaque image for secondary displays.
- [ ] Rename `tests/wallpaper_smoke.py` for discovery, update checks for actual contracts, and align `README.md` and `AGENTS.md` with the choices. Run discovered tests and the device regression checks on the signed build.

### 3. Build dependencies and delivery
- [ ] Resolve build and APK dependency graphs, compare OSV results and Gradle advisories to the spec's baseline.
- [ ] Upgrade the verified Gradle wrapper and `app/build.gradle.kts` plugin/dependencies to compatible corrected versions. Check the complete resolved graphs again.
- [ ] Run `./build-local.sh :app:lintRelease`, verify signature, manifest and 16 KiB alignment, and confirm official APK can update the published APK on an isolated arm64 emulator. Review the final diff and test evidence.
