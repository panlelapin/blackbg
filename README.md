# BlackBG

Un fond noir statique pour l’écran d’accueil et l’écran de verrouillage, sans
sauvegarde des anciens fonds ni accès aux fichiers. Pour Android 16 (API 36)
ou ultérieur, sur appareil ARM 64 bits (`arm64-v8a`).

## Installation

Télécharger l’APK signé depuis les [releases](https://github.com/panlelapin/blackbg/releases/latest)
et l’installer sur le téléphone. BlackBG n’a pas d’icône dans le lanceur.
Dans un sélecteur de fonds d’écran compatible, choisir **BlackBG**, puis
**Appliquer aux deux écrans**. Si le sélecteur du téléphone ne liste pas les
applications tierces, ouvrir l’aperçu via ADB :

```sh
adb shell am start -a android.intent.action.SET_WALLPAPER -p app.blackbg
```

## Compilation locale

Sur macOS avec Android Studio, installer la plateforme SDK 36.1, les Build Tools
36.0.0, le NDK 28.2.13676358 et CMake 3.22.1. Pour d’autres emplacements,
définir `JAVA_HOME` (JDK 21) et `ANDROID_HOME` (SDK Android).

```sh
./build-local.sh
```

L’APK release optimisé est produit dans `app/build/outputs/apk/release/app-release.apk`.
La première compilation crée une clé de signature locale dans
`~/.android/blackbg-release/`. Sauvegarder ce dossier en lieu sûr :
Android exige la même clé pour mettre à jour une installation existante.
