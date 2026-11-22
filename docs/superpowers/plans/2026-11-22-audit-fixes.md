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

### Task 1: Signing
- [x] Add `tests/test_signing.py`: temporary identities and directories must prove refusal of missing/partial/wrong official credentials, private personal initialization and signer reuse.
- [x] Run `python3 -B -m unittest discover -s tests -p test_signing.py -v` against baseline for red, then against the fix.
- [x] Update `build-local.sh` and `app/build.gradle.kts`: `--personal` uses distinct keys and output; default requires published certificate. Validate the resulting APK certificate. Document both modes and personal migration in `README.md`.

### Task 2: Android behavior
- [x] Add device regression checks under `tests/` using a picker caller on a disposable emulator. Assert cancel/back before write, correct target IDs, Back during write, recreation, failure/retry and small window scrolling. Capture baseline failures.
- [x] In `app/src/main/java/app/blackbg/Preview.kt` retain one operation through configuration changes, deliver its result only to the current preview, consume Back while pending, and use a scrolling inset-aware column. Supply a memory-bounded opaque image for secondary displays.
- [x] Rename `tests/wallpaper_smoke.py` for discovery, update checks for actual contracts, and align `README.md` and `AGENTS.md` with the choices. Run discovered tests and the device regression checks on the signed build.

### Task 3: Build dependencies and delivery
- [x] Resolve build and APK dependency graphs, compare OSV results and Gradle advisories to the spec's baseline.
- [x] Upgrade the verified Gradle wrapper and `app/build.gradle.kts` plugin/dependencies to compatible corrected versions. Check the complete resolved graphs again.
- [x] Run `./build-local.sh :app:lintRelease`, verify signature, manifest and 16 KiB alignment, and confirm official APK can update the published APK on an isolated arm64 emulator. Review the final diff and test evidence.

## Verification record (2026-11-22)

BlackBG 1.0.2 (code 3) installed over the published 1.0.1 (code 2) without
changing the first-install timestamp on either AOSP arm64 emulator. Six device
scenarios passed on API 36 (4 KiB) and API 37 (16 KiB), including Back during
a confirmed write, configuration recreation, refusal in a scrolled window,
retry, and isolation of the home/lock destinations. The 4096-square wallpaper
was also bound on a simulated 1080p secondary display.

`python3 -B -m unittest discover -v` ran 12 host tests. The official release
build and lint passed; the sole warning recommends x86 for ChromeOS, outside
the arm64-only delivery requirement. The APK has one published signer, one
permission (`SET_WALLPAPER`), and a 16 KiB-aligned native library.

The project’s Maven OSV scan went from 11 advisory matches on the build
classpath to zero (112 build coordinates; two runtime coordinates). The Gradle
9.9.2 distribution and wrapper were checked against the upstream SHA-256s.
Gradle 9.9.2, AGP 9.5.2 and Kotlin 2.4.21 were verified together here; this
combination is outside Kotlin's published fully tested Gradle/AGP range.
