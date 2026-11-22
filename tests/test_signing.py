"""Signing regressions. All test identities and APKs live in temporary homes."""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
JDK = Path(os.environ.get("JAVA_HOME", "/Applications/Android Studio.app/Contents/jbr/Contents/Home"))
SDK = Path(os.environ.get("ANDROID_HOME", Path.home() / "Library/Android/sdk"))


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

    def test_different_official_certificate_refused(self):
        self.official.mkdir(parents=True)
        password = self.official / "password"
        password.write_text("test-only\n")
        subprocess.run([JDK / "bin/keytool", "-genkeypair", "-alias", "blackbg",
                        "-keystore", self.official / "release.p12", "-storetype", "PKCS12",
                        "-storepass:file", password, "-keyalg", "EC", "-dname", "CN=Other"],
                       check=True, capture_output=True)
        self.assert_refused_before_build()

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
                result = self.build("--personal")
                self.assertEqual(result.returncode, 0, result.stdout)
            verification = subprocess.check_output([
                JDK / "bin/java", "-jar", SDK / "build-tools/36.0.0/lib/apksigner.jar",
                "verify", "--print-certs", apk], text=True)
            self.assertIn("Signer #1 certificate SHA-256 digest: " + digest, verification)
        # Simulate a successful build returning an APK signed with the old identity.
        self.personal.rename(self.home / "previous")
        self.gradle.write_text("#!/bin/sh\nexit 0\n")
        result = self.build("--personal")
        self.assertNotEqual(result.returncode, 0, result.stdout)
