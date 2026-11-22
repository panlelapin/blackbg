# Dépôt F-Droid BlackBG sur GitHub Pages

Permettre l’installation et les mises à jour de BlackBG dans le client F-Droid après ajout manuel du dépôt. Préférer GitHub Pages à IzzyOnDroid (admission externe) et au dépôt officiel (recette de compilation et signature à régler).

Réutiliser l’APK officiel de la release GitHub, sans le reconstruire ni le signer de nouveau. Vérifier `app.blackbg` et son certificat officiel avant de générer l’index. Ne pas modifier l’application ni sa compatibilité Android 16+ ARM64.

Le dossier de travail et la clé d’index restent sur le Mac, hors du dépôt Git. Seul `repo/` est publié, à l’adresse `https://panlelapin.github.io/blackbg/fdroid/repo/`. Le README indique comment l’ajouter avec l’empreinte de la clé d’index et comment publier les mises à jour.
