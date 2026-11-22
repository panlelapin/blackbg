# Picker regression suite

From the repository root, boot an **unlocked, disposable AOSP arm64 emulator**
(API 36+; no accounts, secondary users, device owner or passcode). The suite
replaces its wallpapers, installs the supplied APK and resets display overrides.
Do not use an AVD whose data you want to keep.

```sh
./build-local.sh
python3 tests/device/wallpaper.py --disposable-emulator emulator-5582 \
    app/build/outputs/apk/release/app-release.apk
```

Pass the exact emulator serial from `adb devices`. The runner checks both the
serial and Android’s QEMU property. It builds a temporary test-only picker with
SDK platform 37.1, Build Tools 36.0.0 and JDK 21 (`ANDROID_HOME`, `JAVA_HOME`
if outside the macOS defaults). The picker is temporarily made device owner to
toggle `no_set_wallpaper` for the retry check. Its key, owner and package are
removed on normal exit (including test failures). After an interrupted run,
wipe the disposable AVD or, on that emulator, run:

```sh
adb -s SERIAL shell "dpm remove-active-admin 'audit.check/.Probe\$Admin'"
adb -s SERIAL uninstall audit.check
```

The suite launches `SET_WALLPAPER` for result, drives visible actions, and
checks system/lock IDs from `dumpsys wallpaper` (AOSP English dump format).
Back and rotation are injected immediately after the confirming tap in one
device shell. A single new ID and `RESULT_OK` must follow. The Back check
also requires the preview's diagnostic for a Back received *during* the write;
the rotation check requires the preview to retain a pending write during an
orientation change. Each check allows up to three attempts to observe the
overlap; every attempt must still satisfy the ID and result checks. In a 960 × 580
px window at 480 dpi the suite scrolls down to confirm, checks that the error
comes into view, clears the restriction and retries in the same preview. It
also scrolls to Cancel. UI checks wait for the BlackBG window and report the
focused activity, display settings and last UI tree on timeout.
Host tests (`python3 -m unittest
discover`) also decode the 1-bit PNG samples and validate the manifest/icons.
