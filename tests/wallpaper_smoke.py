"""Structural smoke checks; rendering and wallpaper writes require a device."""
import re
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

MAIN = Path(__file__).resolve().parents[1] / "app/src/main"
A = "{http://schemas.android.com/apk/res/android}"


class WallpaperSmoke(unittest.TestCase):
    def test_selector_icon_and_entry_point(self):
        app = ET.parse(MAIN / "AndroidManifest.xml").find("application")
        self.assertEqual(app.get(A + "icon"), "@drawable/ic_wallpaper")
        self.assertEqual(
            [action.get(A + "name") for action in app.findall(".//action")],
            ["android.intent.action.SET_WALLPAPER"],
        )

    def test_ordered_actions_and_targets(self):
        code = (MAIN / "java/app/blackbg/Preview.kt").read_text()
        self.assertEqual(re.findall(r'addChoice\("([^"]+)",', code),
                         ["Lockscreen", "Homescreen", "Both", "Cancel"])
        for label, icon, action in [
            ("Lockscreen", "lockscreen", "applyWallpaper(WallpaperManager.FLAG_LOCK)"),
            ("Homescreen", "homescreen", "applyWallpaper(WallpaperManager.FLAG_SYSTEM)"),
            ("Both", "both", "applyWallpaper(WallpaperManager.FLAG_SYSTEM or WallpaperManager.FLAG_LOCK)"),
            ("Cancel", "cancel", "finish()"),
        ]:
            self.assertIn(f'addChoice("{label}", R.drawable.ic_{icon}) {{ {action} }}', code)
        self.assertIn("Couldn’t apply wallpaper.", code)

    def test_choice_block_centers_while_rows_stay_start_aligned(self):
        code = (MAIN / "java/app/blackbg/Preview.kt").read_text()
        self.assertRegex(code, r"root\.addView\(controls, FrameLayout\.LayoutParams\(\s*"
                         r"FrameLayout\.LayoutParams\.WRAP_CONTENT,\s*"
                         r"FrameLayout\.LayoutParams\.WRAP_CONTENT,\s*Gravity\.CENTER,?\s*\)\)")
        self.assertIn("setContentView(root)", code)
        self.assertIn("gravity = Gravity.START or Gravity.CENTER_VERTICAL", code)

    def test_vector_disks_and_glyphs(self):
        for name in ("wallpaper", "lockscreen", "homescreen", "both", "cancel"):
            with self.subTest(name=name):
                file = MAIN / f"res/drawable/ic_{name}.xml"
                self.assertTrue(file.is_file(), f"missing {file.name}")
                vector = ET.parse(file).getroot()
                self.assertEqual(vector.tag, "vector")
                disk, *glyphs = vector.findall("path")
                self.assertEqual(disk.get(A + "fillColor"), "#000000")
                self.assertEqual(disk.get(A + "strokeColor"), "#FFFFFF")
                self.assertEqual(len(glyphs), {"wallpaper": 0, "both": 2}.get(name, 1))
                for glyph in glyphs:
                    self.assertIn("#FFFFFF", (glyph.get(A + "fillColor"), glyph.get(A + "strokeColor")))


if __name__ == "__main__":
    unittest.main()
