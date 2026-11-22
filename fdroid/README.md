# Publier BlackBG dans le catalogue panlelapin

Le catalogue partagé par BlackBG et WorkFlowy Quick Add est désormais
[`panlelapin/panlelapin`](https://github.com/panlelapin/panlelapin).
La publication se fait sur `main` dans ce dépôt, et non sur `blackbg/gh-pages`.
L’ancienne adresse reste accessible aux clients déjà configurés ; pour recevoir
les nouvelles versions, [ajouter le nouveau catalogue](https://panlelapin.github.io/panlelapin/fdroid/repo/?fingerprint=363DEB527CD0C41ABBC30359005EE6F2A5A6869716D32CF42CEED66DCC3A7A7A).

1. Télécharger l’APK signé de la release BlackBG. Utiliser le dossier privé
   F-Droid existant (`~/.local/share/blackbg-fdroid`) avec son index, toutes les
   applications et sa clé. Ne pas relancer `fdroid init`.
2. Depuis la racine de BlackBG, lancer `./prepare-fdroid.sh <apk> <dossier-privé>`.
   Ce script contrôle le paquet, le signataire et la version.
3. Vérifier dans `repo/index-v2.json` la présence de BlackBG et des autres
   applications. Suivre les [instructions de publication du catalogue](https://github.com/panlelapin/panlelapin#readme).
   Le script historique `fdroid/stage-pages.sh` cible l’ancien hébergement.
