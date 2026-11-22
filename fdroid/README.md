# Publier BlackBG

1. Augmenter `versionCode` et `versionName` dans `app/build.gradle.kts`.
2. Depuis GitHub, publier une release `v<versionName>` sur le commit correspondant.
3. L’action **APK BlackBG officiel** construit et signe l’APK ARM64 et le joint à cette release. Le lancement manuel de cette action vérifie la signature sans publier d’APK.

Le [catalogue partagé](https://github.com/panlelapin/android) importe les nouveaux APK signés. Il vérifie le certificat de BlackBG indépendamment de la signature de l’index. [Ajouter le catalogue F-Droid](https://panlelapin.github.io/android/fdroid/repo/?fingerprint=363DEB527CD0C41ABBC30359005EE6F2A5A6869716D32CF42CEED66DCC3A7A7A).
