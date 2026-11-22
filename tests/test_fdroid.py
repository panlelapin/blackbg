import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "prepare-fdroid.sh"
CERT = "d7f02e4701a55950eba482d631b4df25d9fd8100c21f18f99e8897f1aab2ec5e"
SIGNER = f"Signer #1 certificate SHA-256 digest: {CERT}"


class PrepareFDroid(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.apk = self.root / "Black BG.apk"
        self.apk.write_bytes(b"official release")
        self.work = self.root / "private repo"
        (self.work / "repo").mkdir(parents=True)
        (self.work / "config.yml").write_text("repo_name: BlackBG\n")
        self.dest = self.work / "repo/app.blackbg_12.apk"
        self.index = self.work / "repo/index-v2.json"
        self.env = dict(os.environ, PATH=f"{self.root}:{os.environ['PATH']}",
                        SIGNERS=SIGNER, PACKAGE="app.blackbg")
        for name, body in {
            "apksigner": 'test "$1 $2" = "verify --print-certs" && test -f "$3" || exit 2\n'
                         'echo "$SIGNERS"\nexit "${VERIFY_STATUS:-0}"',
            "aapt": 'test "$1 $2" = "dump badging" && test -f "$3" || exit 2\n'
                    '''echo "package: name='$PACKAGE' versionCode='12' versionName='1.2'"''',
            "fdroid": 'test "$1 $2" = "update --create-metadata" || exit 2\n'
                      'test -f repo/app.blackbg_12.apk || exit 3\n'
                      '[ "${INDEX_STATUS:-0}" = 0 ] || exit "$INDEX_STATUS"\n'
                      'echo "{}" > repo/index-v2.json',
        }.items():
            tool = self.root / name
            tool.write_text(f"#!/bin/sh\n{body}\n")
            tool.chmod(0o755)

    def prepare(self, **changes):
        return subprocess.run(["bash", SCRIPT, self.apk, self.work], cwd=self.root,
                              env={**self.env, **changes}, capture_output=True, text=True)

    def test_valid_apk_indexes(self):
        result = self.prepare()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.index.is_file())
        self.assertEqual(self.dest.read_bytes(), self.apk.read_bytes())

    def test_invalid_inputs_do_not_index(self):
        for changes in ({"PACKAGE": "app.other"}, {"SIGNERS": SIGNER[:-1]},
                        {"VERIFY_STATUS": "1"},
                        {"SIGNERS": SIGNER + "\n" + SIGNER.replace("#1", "#2")}):
            with self.subTest(changes=changes):
                self.assertNotEqual(self.prepare(**changes).returncode, 0)
                self.assertEqual(list((self.work / "repo").iterdir()), [])
        self.apk.unlink()
        self.assertNotEqual(self.prepare().returncode, 0)
        self.assertEqual(list((self.work / "repo").iterdir()), [])

    def test_existing_version_is_not_overwritten(self):
        self.dest.write_bytes(b"previous release")
        self.assertNotEqual(self.prepare().returncode, 0)
        self.assertEqual(self.dest.read_bytes(), b"previous release")
        self.assertFalse(self.index.exists())

    def test_index_error_is_reported(self):
        self.assertEqual(self.prepare(INDEX_STATUS="17").returncode, 17)
        self.assertFalse(self.index.exists())
        self.assertEqual(self.prepare().returncode, 0, "retry with the same APK")
