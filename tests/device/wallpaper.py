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
    return subprocess.check_output([adb_path, "-s", serial, *args], text=True, timeout=45).strip()


def sh(cmd):
    return adb("shell", cmd)


def ui():
    xml = sh("uiautomator dump /data/local/tmp/blackbg-ui.xml >/dev/null && cat /data/local/tmp/blackbg-ui.xml")
    return ET.fromstring(xml)


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
    row = next((n for n in ui().iter("node") if n.get("text") == label), None)
    assert row is not None and row.get("enabled") == "true", f"{label} missing or disabled"
    x, y, right, bottom = map(int, re.findall(r"\d+", row.get("bounds")))
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
                self.assertEqual(matches, [str(expected)], f"wallpaper IDs {ids()}")
                return
            time.sleep(.15)
        self.fail(f"caller received no result; wallpaper IDs {ids()}")

    def test_cancel_and_back(self):
        before = ids()
        for action in ["Cancel", "Back"]:
            self.start()
            self.assertEqual([n.get("text") for n in ui().iter("node")
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
        self.confirmed_then("input keyevent 4")

    def test_recreate_during_write(self):
        self.confirmed_then("wm user-rotation lock 1")
        events = adb("logcat", "-b", "events", "-d", "-s", "wm_on_create_called:I")
        self.assertGreaterEqual(events.count("app.blackbg.Preview"), 2, events)

    def test_refusal_and_retry(self):
        before = ids()
        open_picker("deny")
        self.addCleanup(open_picker, "restore")
        self.start()
        tap("Both")
        self.assertIn("Couldn’t apply wallpaper.", [n.get("text") for n in ui().iter("node")])
        self.assertEqual(ids(), before)
        self.assertNotIn("result=", adb("logcat", "-d", "-s", "WallAuditResult:I"))
        open_picker("restore")
        tap("Both")
        self.result(-1)
        self.assertNotEqual(ids(), before)

    def test_short_window(self):
        sh("wm size 960x580; wm density 480")
        before = ids()
        self.start()
        self.assertTrue(any(n.get("scrollable") == "true" for n in ui().iter("node")))
        sh("input swipe 450 445 450 120 300")
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
