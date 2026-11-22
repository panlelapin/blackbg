#!/bin/sh
set -eu
cd "$(dirname "$0")"
export JAVA_HOME="${JAVA_HOME:-/Applications/Android Studio.app/Contents/jbr/Contents/Home}"
export ANDROID_HOME="${ANDROID_HOME:-$HOME/Library/Android/sdk}"
keys="$HOME/.android/blackbg-release"
if [ ! -f "$keys/release.p12" ]; then
    (
        umask 077
        mkdir -p "$keys"
        if [ ! -s "$keys/password" ]; then
            openssl rand -hex 32 > "$keys/password"
        fi
        "$JAVA_HOME/bin/keytool" -genkeypair -keystore "$keys/release.p12" \
            -storetype PKCS12 -storepass:file "$keys/password" -alias blackbg \
            -keyalg RSA -keysize 3072 -validity 10000 -dname "CN=BlackBG"
    )
fi
exec ./gradlew :app:assembleRelease "$@"
