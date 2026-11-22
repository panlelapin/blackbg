#include <jni.h>

// An all-DEX APK is ABI-neutral. This small library gives PackageManager
// a real arm64-v8a payload without moving Android UI code out of Kotlin.
#if !defined(__aarch64__)
#error BlackBG requires 64-bit ARM.
#endif

JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM *vm, void *reserved) {
    return JNI_VERSION_1_6;
}
