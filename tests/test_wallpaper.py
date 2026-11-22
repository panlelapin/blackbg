"""Structural smoke checks; rendering and wallpaper writes require a device."""
import struct
import unittest
import zlib
from pathlib import Path
from xml.etree import ElementTree as ET

MAIN = Path(__file__).resolve().parents[1] / "app/src/main"
A = "{http://schemas.android.com/apk/res/android}"


class WallpaperSmoke(unittest.TestCase):
    def test_selector_icon_and_entry_point(self):
        manifest = ET.parse(MAIN / "AndroidManifest.xml")
        self.assertEqual([p.get(A + "name") for p in manifest.findall("uses-permission")],
                         ["android.permission.SET_WALLPAPER"])
        app = manifest.find("application")
        self.assertEqual(app.get(A + "icon"), "@drawable/ic_wallpaper")
        self.assertEqual(
            [action.get(A + "name") for action in app.findall(".//action")],
            ["android.intent.action.SET_WALLPAPER"],
        )

    def test_stream_payload_is_opaque_black_and_covers_4k_in_either_orientation(self):
        png = (MAIN / "res/raw/black.png").read_bytes()
        self.assertEqual(png[:8], b"\x89PNG\r\n\x1a\n")
        pos, data = 8, bytearray()
        while pos < len(png):
            size, kind = struct.unpack_from(">I4s", png, pos)
            chunk = png[pos + 8:pos + 8 + size]
            if kind == b"IHDR":
                width, height, depth, color, compression, filtering, interlace = struct.unpack(">IIBBBBB", chunk)
                self.assertEqual((width, height), (4096, 4096))
                self.assertEqual((depth, color, compression, filtering, interlace), (1, 0, 0, 0, 0))
            self.assertNotEqual(kind, b"tRNS", "black must be opaque")
            if kind == b"IDAT":
                data.extend(chunk)
            pos += 12 + size
        # Filter byte zero followed by packed grayscale samples zero, for every row.
        self.assertEqual(zlib.decompress(data), bytes(height * (1 + (width + 7) // 8)))

    def test_choice_block_centers_while_rows_stay_start_aligned(self):
        code = (MAIN / "java/app/blackbg/Preview.kt").read_text()
        self.assertRegex(code, r"root\.addView\(controls, FrameLayout\.LayoutParams\(\s*"
                         r"FrameLayout\.LayoutParams\.WRAP_CONTENT,\s*"
                         r"FrameLayout\.LayoutParams\.WRAP_CONTENT,\s*Gravity\.CENTER,?\s*\)\)")
        self.assertIn("scroll.addView(root)", code)
        self.assertIn("setContentView(scroll)", code)
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
