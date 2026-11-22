"""Signing regressions. All test identities and APKs live in temporary homes."""
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
JDK = Path(os.environ.get("JAVA_HOME", "/Applications/Android Studio.app/Contents/jbr/Contents/Home"))
SDK = Path(os.environ.get("ANDROID_HOME", Path.home() / "Library/Android/sdk"))
PUBLISHED = "d7f02e4701a55950eba482d631b4df25d9fd8100c21f18f99e8897f1aab2ec5e"


class Signing(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.home = Path(temp.name)
        self.project = self.home / "project"
        self.project.mkdir()
        shutil.copy2(ROOT / "build-local.sh", self.project)
        self.official = self.home / ".android/blackbg-release"
        self.personal = self.home / ".android/blackbg-personal"
        self.env = dict(os.environ, HOME=str(self.home), JAVA_HOME=str(JDK),
                        ANDROID_HOME=str(SDK), ANDROID_USER_HOME=str(self.home / ".android"),
                        GRADLE_USER_HOME=os.environ.get("GRADLE_USER_HOME", str(Path.home() / ".gradle")))
        self.gradle = self.project / "gradlew"
        self.gradle.write_text("#!/bin/sh\ntouch gradle-called\n")
        self.gradle.chmod(0o755)

    def build(self, *args):
        return subprocess.run(["./build-local.sh", *args], cwd=self.project, env=self.env,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    def assert_refused_before_build(self, *args):
        result = self.build(*args)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertFalse((self.project / "gradle-called").exists(), result.stdout)
        return result.stdout

    def test_missing_official_never_created(self):
        self.assert_refused_before_build()
        self.assertFalse(self.official.exists())

    def test_partial_credentials_untouched(self):
        for directory, args in [(self.official, []), (self.personal, ["--personal"])]:
            for filename in [None, "password", "release.p12"]:
                with self.subTest(directory=directory.name, filename=filename):
                    directory.mkdir(parents=True)
                    if filename:
                        (directory / filename).write_bytes(b"original\n")
                    try:
                        self.assert_refused_before_build(*args)
                        self.assertEqual({p.name: p.read_bytes() for p in directory.iterdir()},
                                         {filename: b"original\n"} if filename else {})
                    finally:
                        shutil.rmtree(directory)
                        (self.project / "gradle-called").unlink(missing_ok=True)

    def create_identity(self, directory):
        directory.mkdir(parents=True, mode=0o700)
        password = directory / "password"
        password.write_text("test-only\n")
        password.chmod(0o600)
        store = directory / "release.p12"
        subprocess.run([JDK / "bin/keytool", "-genkeypair", "-alias", "blackbg",
                        "-keystore", store, "-storetype", "PKCS12",
                        "-storepass:file", password, "-keyalg", "EC", "-dname", "CN=Other"],
                       check=True, capture_output=True)
        store.chmod(0o600)

    def test_different_official_certificate_refused(self):
        self.create_identity(self.official)
        self.assertIn("does not match the published", self.assert_refused_before_build())

    def test_official_certificate_refused_for_personal_build(self):
        self.create_identity(self.personal)
        cert = subprocess.check_output([JDK / "bin/keytool", "-exportcert", "-alias", "blackbg",
                                        "-keystore", self.personal / "release.p12",
                                        "-storepass:file", self.personal / "password"])
        # Pin the temporary identity in the test copy; never use the release key.
        script = self.project / "build-local.sh"
        script.write_text(script.read_text().replace(PUBLISHED, hashlib.sha256(cert).hexdigest()))
        self.assertIn("official certificate", self.assert_refused_before_build("--personal"))

    def test_restored_credentials_must_be_private_in_both_modes(self):
        for directory, args in [(self.official, []), (self.personal, ["--personal"])]:
            self.create_identity(directory)
            for path, mask in [(directory, 0o010), (directory / "password", 0o004),
                               (directory / "release.p12", 0o020)]:
                with self.subTest(path=path):
                    mode = path.stat().st_mode & 0o777
                    path.chmod(mode | mask)
                    try:
                        output = self.assert_refused_before_build(*args)
                        self.assertIn("private permissions", output)
                        self.assertIn(str(path), output)
                        self.assertEqual(path.stat().st_mode & 0o777, mode | mask)
                    finally:
                        path.chmod(mode)
                        (self.project / "gradle-called").unlink(missing_ok=True)

    def test_cannot_skip_assembly_or_inject_gradle_arguments(self):
        self.create_identity(self.personal)
        for args in [["--dry-run"], ["-m"], ["-x", "packageRelease"],
                     [":app:lintRelease", "--exclude-task=:app:assembleRelease"],
                     ["--init-script", "other.gradle"]]:
            with self.subTest(args=args):
                self.assertIn("Usage:", self.assert_refused_before_build("--personal", *args))
            (self.project / "gradle-called").unlink(missing_ok=True)

    @unittest.skipUnless(sys.platform == "darwin", "macOS extended ACLs")
    def test_extended_acl_cannot_grant_access_to_private_key(self):
        self.create_identity(self.personal)
        store = self.personal / "release.p12"
        subprocess.run(["chmod", "+a", "everyone allow read", store], check=True)
        self.assertEqual(store.stat().st_mode & 0o777, 0o600)
        self.assertIn("private permissions", self.assert_refused_before_build("--personal"))

    def test_personal_apk_reuses_private_identity_and_rejects_wrong_output(self):
        shutil.copytree(ROOT, self.project, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns(".git", ".superpowers", ".gradle", ".kotlin",
                                                      "build", ".cxx", "local.properties"))
        official_apk = self.project / "app/build/outputs/apk/release/app-release.apk"
        apk = self.project / "app/build/personal/outputs/apk/release/app-release.apk"
        result = self.build("--personal")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertFalse(self.official.exists())
        self.assertFalse(official_apk.exists())
        store = self.personal / "release.p12"
        password = self.personal / "password"
        for path in [self.personal, store, password]:
            self.assertEqual(path.stat().st_mode & 0o077, 0, str(path))
        cert = subprocess.check_output([JDK / "bin/keytool", "-exportcert", "-alias", "blackbg",
                                        "-keystore", store, "-storepass:file", password])
        digest = hashlib.sha256(cert).hexdigest()
        for attempt in range(2):
            if attempt:
                apk.unlink()
                result = self.build("--personal", ":app:lintRelease")
                self.assertEqual(result.returncode, 0, result.stdout)
            verification = subprocess.check_output([
                JDK / "bin/java", "-jar", SDK / "build-tools/36.0.0/lib/apksigner.jar",
                "verify", "--print-certs", apk], text=True)
            signers = re.findall(r"^Signer #\d+ certificate SHA-256 digest: (.+)$",
                                 verification, flags=re.MULTILINE)
            self.assertEqual(signers, [digest], verification)
        # Simulate a successful build returning an APK signed with the old identity.
        self.personal.rename(self.home / "previous")
        self.gradle.write_text("#!/bin/sh\nexit 0\n")
        result = self.build("--personal")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("Unexpected APK signing certificate:", result.stdout)
