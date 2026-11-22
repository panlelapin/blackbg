"""Destructive picker checks. Run only on a dedicated AOSP emulator (see README)."""
import argparse
import os
import re
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

HERE = Path(__file__).resolve().parent
OWNER = "audit.check/.Probe$Admin"
LABELS = ["Lockscreen", "Homescreen", "Both", "Cancel"]


def adb(*args):
    return subprocess.check_output([adb_path, "-s", serial, *args], text=True, timeout=45,
                                   stderr=subprocess.STDOUT).strip()


def sh(cmd):
    return adb("shell", cmd)


def diagnostics():
    return sh("wm size; wm density; wm user-rotation; dumpsys window | grep -E 'mCurrentFocus|mFocusedApp'; "
              "logcat -d -t 1000 -s AndroidRuntime:E InputDispatcher:I WallAuditResult:I BlackBG:D")


def input_window():
    """Return the ready Preview input-window record, or None and the blocking state."""
    tracks = sh("wm shell dump | sed -n '/Pending Transitions:/,/^$/p'")
    if not re.fullmatch(r"Pending Transitions:\s+none\s+Ready-during-sync Transitions:\s+none\s+"
                        r"Tracks:(?:\s+Track #\d+\s+active=null)*", tracks):
        return None, f"WM transitions: {tracks}"
    windows = sh("dumpsys input | sed -n '/^  FocusedWindows:/,+1p; /: name=.*blackbg.*inputConfig=/p'")
    focus = re.search(r"displayId=0, name='(\w+ app\.blackbg/app\.blackbg\.Preview)'", windows)
    # InputDispatcher lists layers front-to-back. A sink behind Preview is normal.
    for line in windows.splitlines():
        if "displayId=0, inputConfig=" not in line or "touchableRegion=<empty>" in line or "NOT_TOUCHABLE" in line:
            continue
        if "ActivityRecordInputSink app.blackbg/.Preview," in line:
            break
        if focus and f"name={focus[1]}," in line and "NO_INPUT_CHANNEL" not in line and "DROP_INPUT" not in line:
            return line, windows
    return None, f"InputDispatcher: {windows}"


def preview_ui(description, condition):
    end = time.monotonic() + 12
    while time.monotonic() < end:
        try:
            before, last = input_window()
            if before is None:
                time.sleep(.1)
                continue
            path = "/data/local/tmp/blackbg-ui.xml"
            xml = sh(f"rm -f {path}; uiautomator dump {path} >/dev/null && cat {path}")
            root = ET.fromstring(xml).find("node")
            if root is not None and root.get("package") == "app.blackbg" and condition(root):
                # A wallpaper-colors config change can relaunch Preview while the
                # hierarchy is being dumped. Re-observe it before injecting any input.
                after, last = input_window()
                if after == before:
                    return root
            else:
                last = xml
        except (ET.ParseError, subprocess.CalledProcessError) as e:
            last = f"{e}: {getattr(e, 'output', '')}"
        time.sleep(.1)
    raise AssertionError(f"Timed out waiting for {description}\n{diagnostics()}\nLast observation: {last}")


def row(root, label):
    return root.find(f".//node[@text='{label}']")


def bounds(node):
    return tuple(map(int, re.findall(r"-?\d+", node.get("bounds"))))


def short_viewport():
    return preview_ui("scrollable 960x580 BlackBG window", lambda r:
                      bounds(r) == (0, 0, 960, 580) and r.find(".//node[@scrollable='true']") is not None)


def short_display():
    # Resize the foreground preview, not the launcher or the policy command.
    # Wait for the resize before rotating; wm/settings changes are asynchronous.
    preview_ui("foreground chooser", lambda r: row(r, "Lockscreen") is not None)
    sh("wm size 580x960; wm density 480")
    preview_ui("resized chooser", lambda r: sorted(bounds(r)[2:]) == [580, 960])
    sh("wm user-rotation lock 1")
    return short_viewport()


def swipe_up():
    sh("input swipe 450 445 450 120 300")


def ids():
    """Effective (home, lock): a shared lock inherits the system ID."""
    dump = sh("dumpsys wallpaper")
    system, lock = dump.split("System wallpaper state:")[1].split("Fallback wallpaper state:")[0].split("Lock wallpaper state:")
    home = int(re.search(r"User 0: id=(\d+)", system)[1])
    separate = re.search(r"User 0: id=(\d+)", lock)
    return home, int(separate[1]) if separate else home


def open_picker(mode=""):
    # Policy commands run in their own task, even when the original Probe is
    # underneath Preview waiting for its result.
    sh("am start -W -n audit.check/.Probe" + (f" -f 0x18000000 --es mode {mode}" if mode else ""))


def tap(label, follow=""):
    root = preview_ui(f"enabled {label}", lambda r: r.find(f".//node[@text='{label}'][@enabled='true']") is not None)
    x, y, right, bottom = bounds(row(root, label))
    sh(f"input tap {(x + right) // 2} {(y + bottom) // 2}" + (f"; {follow}" if follow else ""))


class Picker(unittest.TestCase):
    def setUp(self):
        sh("am force-stop app.blackbg; am force-stop audit.check; wm user-rotation lock 0")
        sh("input keyevent KEYCODE_WAKEUP; wm dismiss-keyguard")
        self.addCleanup(sh, "wm size reset; wm density reset; wm user-rotation free")

    def start(self):
        adb("logcat", "-b", "all", "-c")
        open_picker()

    def result(self, expected):
        end = time.monotonic() + 10
        while time.monotonic() < end:
            matches = re.findall(r"result=(-?\d+)", adb("logcat", "-d", "-s", "WallAuditResult:I"))
            if matches:
                if matches != [str(expected)]:
                    self.fail(f"expected {expected}, got {matches}; wallpaper IDs {ids()}\n{diagnostics()}")
                return
            time.sleep(.15)
        self.fail(f"caller received no result; wallpaper IDs {ids()}\n{diagnostics()}")

    def test_cancel_and_back(self):
        before = ids()
        for action in ["Cancel", "Back"]:
            self.start()
            root = preview_ui("picker choices", lambda r: row(r, "Cancel") is not None)
            self.assertEqual([n.get("text") for n in root.iter("node")
                              if n.get("class") == "android.widget.Button"], LABELS)
            tap(action) if action == "Cancel" else sh("input keyevent 4")
            self.result(0)
            self.assertEqual(ids(), before)

    def test_targets(self):
        for label, changes in [("Both", (True, True)), ("Lockscreen", (False, True)),
                               ("Homescreen", (True, False)), ("Both", (True, True))]:
            before = ids()
            self.start()
            tap(label)
            self.result(-1)
            after = ids()
            self.assertEqual(tuple(a != b for a, b in zip(after, before)), changes, label)
            if label == "Both":
                self.assertEqual(*after)
            print(f"{label}: {before} -> {after}", flush=True)
        dump = sh("dumpsys wallpaper").split("Lock wallpaper state:")[0]
        self.assertIn("mAllowBackup=false", dump)
        self.assertIn("mCropHint=Rect(0, 0 - 4096, 4096)", dump)

    def confirmed_then(self, follow):
        self.start()
        tap("Both")
        self.result(-1)
        before = ids()[0]
        self.start()
        tap("Both", follow)
        self.result(-1)
        self.assertEqual(ids(), (before + 1, before + 1), "expected exactly one new wallpaper")

    def test_back_during_write(self):
        for _ in range(3):
            self.confirmed_then("input keyevent 4")
            evidence = adb("logcat", "-d", "-s", "BlackBG:D")
            if "Back ignored while applying wallpaper" in evidence:
                print(evidence, flush=True)
                return
        self.fail("Back never reached the preview during a pending write\n" + diagnostics())

    def test_recreate_during_write(self):
        self.confirmed_then("wm user-rotation lock 1")
        events = adb("logcat", "-b", "events", "-d", "-s", "wm_on_create_called:I")
        self.assertGreaterEqual(events.count("app.blackbg.Preview"), 2, events)

    def test_refusal_and_retry(self):
        before = ids()
        open_picker("deny")
        self.addCleanup(open_picker, "restore")
        self.start()
        top = bounds(row(short_display(), "Lockscreen"))[1]
        swipe_up()
        preview_ui("scrolled down to Cancel", lambda r: row(r, "Cancel") is not None and row(r, "Lockscreen") is None)
        tap("Both")
        error = "Couldn’t apply wallpaper."
        preview_ui("error visible at the top inset", lambda r: row(r, error) is not None and bounds(row(r, error))[1] == top
                   and row(r, "Lockscreen") is not None)
        self.assertEqual(ids(), before)
        self.assertNotIn("result=", adb("logcat", "-d", "-s", "WallAuditResult:I"))
        open_picker("restore")
        short_viewport()
        swipe_up()
        tap("Both")
        self.result(-1)
        self.assertNotEqual(ids(), before)

    def test_short_window(self):
        before = ids()
        self.start()
        short_display()
        swipe_up()
        tap("Cancel")
        self.result(0)
        self.assertEqual(ids(), before)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--disposable-emulator", required=True)
    parser.add_argument("apk", type=Path)
    args = parser.parse_args()
    serial = args.disposable_emulator
    adb_path = Path(os.environ.get("ANDROID_HOME", Path.home() / "Library/Android/sdk")) / "platform-tools/adb"
    if not re.fullmatch(r"emulator-\d+", serial) or sh("getprop ro.boot.qemu") != "1":
        parser.error("a local disposable Android emulator is required")
    if sh("am get-current-user") != "0" or sh("dpm list-owners").lower() not in ("", "no owners"):
        parser.error("use an owner-free emulator running as user 0")
    if sh("pm list packages audit.check"):
        parser.error("remove the existing test fixture first")
    adb("install", "-r", str(args.apk))
    with tempfile.TemporaryDirectory() as temp:
        subprocess.run(["sh", HERE / "build-picker.sh", temp], check=True)
        adb("install", "-t", str(Path(temp) / "test.apk"))
        try:
            sh(f"dpm set-device-owner '{OWNER}'")
            try:
                suite = unittest.defaultTestLoader.loadTestsFromTestCase(Picker)
                result = unittest.TextTestRunner(verbosity=2).run(suite)
            finally:
                sh(f"dpm remove-active-admin '{OWNER}'")
        finally:
            adb("uninstall", "audit.check")
    raise SystemExit(not result.wasSuccessful())
