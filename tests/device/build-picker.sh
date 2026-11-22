#!/bin/sh
# Build the test-only caller/owner outside the app's Gradle build.
set -eu
here=$(cd "$(dirname "$0")/picker" && pwd)
cd "$1" # empty temporary directory
sdk=${ANDROID_HOME:-"$HOME/Library/Android/sdk"}
bt="$sdk/build-tools/36.0.0"
jar="$sdk/platforms/android-37.1/android.jar"
export JAVA_HOME=${JAVA_HOME:-"/Applications/Android Studio.app/Contents/jbr/Contents/Home"}
export PATH="$JAVA_HOME/bin:$PATH"
mkdir classes dex
"$bt/aapt2" compile --dir "$here/res" -o res.zip
"$bt/aapt2" link -I "$jar" --manifest "$here/AndroidManifest.xml" \
    --min-sdk-version 36 --target-sdk-version 36 -o picker.apk res.zip
javac --release 17 -classpath "$jar" -d classes "$here/Probe.java"
"$bt/d8" --lib "$jar" --min-api 36 --output dex classes/audit/check/*.class
(cd dex && zip -q ../picker.apk classes.dex)
"$bt/zipalign" -f 4 picker.apk aligned.apk
keytool -genkeypair -keystore test.p12 -storepass fixture -alias picker \
    -keyalg RSA -keysize 2048 -validity 1 -dname CN=DisposableTest
"$bt/apksigner" sign --ks test.p12 --ks-pass pass:fixture --out test.apk aligned.apk
