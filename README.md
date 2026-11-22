# BlackBG

Un fond noir statique pour l’écran d’accueil et l’écran de verrouillage, sans
sauvegarde des anciens fonds ni accès aux fichiers. Pour Android 16 (API 36)
ou ultérieur, sur appareil ARM 64 bits (`arm64-v8a`).

## Installation

Avec F-Droid, [ajouter le catalogue « panlelapin »](https://panlelapin.github.io/panlelapin/fdroid/repo/?fingerprint=363DEB527CD0C41ABBC30359005EE6F2A5A6869716D32CF42CEED66DCC3A7A7A),
actualiser le catalogue, puis installer **BlackBG**. Le même APK signé est
disponible dans les [releases GitHub](https://github.com/panlelapin/blackbg/releases/latest).

BlackBG n’a pas d’icône dans le lanceur.
Dans un sélecteur de fonds d’écran compatible, choisir **BlackBG**, puis
**Lockscreen** (verrouillage), **Homescreen** (accueil) ou **Both** (les deux).
**Cancel** ou Retour ferme l’aperçu sans rien changer avant ce choix. Une fois
la cible choisie, attendre la fin de l’application du fond ; en cas de refus,
l’aperçu affiche une erreur et permet de réessayer. En fenêtre basse, faire
défiler les choix. Si le sélecteur du téléphone ne liste pas les applications
tierces, ouvrir l’aperçu via ADB :

```sh
adb shell am start -a android.intent.action.SET_WALLPAPER -p app.blackbg
```

Pour publier une mise à jour : [Publier le dépôt F-Droid](fdroid/README.md).

## Compilation locale

Sur macOS avec Android Studio, installer la plateforme SDK 37.1, les Build Tools
36.0.0, le NDK 30.0.16248370 et CMake 3.22.1. Pour d’autres emplacements,
définir `JAVA_HOME` (JDK 21) et `ANDROID_HOME` (SDK Android).

```sh
./build-local.sh
```

Cette commande exige la clé officielle (`release.p12`, alias `blackbg`) et son
fichier `password` dans `~/.android/blackbg-release/`. Elle vérifie l’empreinte
SHA-256 du certificat publié
(`d7f02e4701a55950eba482d631b4df25d9fd8100c21f18f99e8897f1aab2ec5e`),
puis la signature de `app/build/outputs/apk/release/app-release.apk`.

Pour signer avec votre propre clé :

```sh
./build-local.sh --personal
```

Ce mode crée `~/.android/blackbg-personal/` avec des permissions privées au
premier lancement, puis réutilise sa clé. Sauvegardez le dossier en lieu sûr :
si un fichier manque, restaurez la paire `release.p12` et `password` à partir
de la même sauvegarde. L’APK personnel vérifié se trouve dans
`app/build/personal/outputs/apk/release/app-release.apk`.

Dans les deux modes, le dossier de signature et les deux fichiers doivent
vous appartenir et n’être accessibles qu’à vous (par exemple `700` pour le
dossier, `600` pour les fichiers, sans ACL supplémentaire sur macOS).
Le mode personnel refuse le certificat officiel. Pour exécuter aussi Lint,
ajoutez `:app:lintRelease` à la commande ; c’est le seul argument Gradle admis.

Si une ancienne version du script a créé **votre clé personnelle** dans
`~/.android/blackbg-release/`, migrez-la **avant** le premier `--personal` :
avec `umask 077`, créez `~/.android/blackbg-personal/` et copiez-y les deux
fichiers personnels, sans écraser de clé existante. Les deux modes conservent
l’identifiant `app.blackbg` : Android accepte une mise à jour avec la même clé,
mais exige de désinstaller l’application avant de passer à une autre signature.

Pour vérifier les dépendances résolues, définir `JAVA_HOME` et `ANDROID_HOME`,
puis exécuter `python3 tools/audit-dependencies.py`. Le script interroge OSV
séparément pour les dépendances Maven des plugins Gradle et celles d’exécution
de la release. Il échoue si un avis est trouvé ou si la réponse est incomplète.
Il ne couvre ni les JAR locaux sans coordonnées Maven (aucun dans ce projet),
ni les binaires de Gradle, du SDK ou du NDK.
