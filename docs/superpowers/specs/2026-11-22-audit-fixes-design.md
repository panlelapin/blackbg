# Correctifs de l’audit BlackBG 1.0.1

## Objectif et contraintes
Corriger les résultats erronés du sélecteur, l’accessibilité en fenêtre basse,
la signature, les dépendances de build et les écarts de documentation. Conserver
les quatre choix, Kotlin, Android API 36 minimum, arm64 uniquement, R8 et la
réduction des ressources. Ne jamais lire ni sauvegarder les anciens fonds.

## Approches
Pour la signature, le propriétaire a choisi deux modes plutôt que de réserver
tous les builds release au détenteur de la clé officielle. `./build-local.sh`
vérifie le certificat de la release publiée et exige la clé historique dans
`~/.android/blackbg-release/`. Un mode `--personal` explicite utilise un
répertoire privé distinct et n'initialise une clé que sur une première
installation. Un état incomplet est une erreur. Distinguer les artefacts et
vérifier le signataire de l'APK produit. Conserver `app.blackbg` en mode
personnel pour permettre la mise à jour d'une installation personnelle avec
la même clé. Documenter la migration d'une ancienne clé personnelle et
l'impossibilité de remplacer l'APK officiel avec un autre certificat.

## Comportement et vérification
- Avant le choix, Retour et Cancel ferment sans écrire. Après le choix, une
  seule opération reste en cours malgré Retour ou une rotation. Le sélecteur
  reçoit `RESULT_OK` après succès ; un refus affiche `Couldn’t apply wallpaper.`
  et permet de réessayer. Conserver l'opération à travers les recréations de
  configuration plutôt que de relancer l'écriture.
- Garder les quatre actions centrées lorsque la hauteur suffit ; permettre le
  défilement sinon. Respecter les encoches et les barres système. Fournir une
  image noire opaque de dimensions appropriées pour les écrans secondaires
  pris en charge par Android sans allocation proportionnelle à la résolution
  en mémoire de l'application.
- Utiliser une combinaison stable et corrigée de Gradle et d'AGP. Vérifier
  les dépendances de build résolues contre les avis de l'audit et contrôler
  séparément les dépendances de l'APK. Vérifier les bulletins Gradle applicables
  à 9.1.0, notamment GHSA-xwqc-3h47-hg64 et GHSA-35pj-rg5r-8rpv. Sur le
  classpath du build, vérifier Guava (GHSA-xxph-c9ww-hj94), commons-lang3
  (GHSA-j288-q9x7-2f5v), jose4j (GHSA-3677-xxcr-wjqv), bcpkix
  (GHSA-wg6q-6289-32hp), bcprov (GHSA-574f-3g2m-x479, GHSA-9pwp-9qqc-pr26,
  GHSA-c3fc-8qff-9hwx, GHSA-p93r-85wp-75v3, GHSA-qp49-qgx5-5m26), JDOM
  (GHSA-2363-cqg2-863c) et le plugin Kotlin (GHSA-r937-wjx7-w2jp).
- Corriger le README et les instructions du dépôt. Rendre les tests hôtes
  découvrables et tester sur Android les résultats du sélecteur, les cibles
  modifiées, l'annulation, les changements de configuration et la visibilité
  des actions en fenêtre basse. Vérifier le build signé, le certificat, le
  manifeste et l'ABI. Ne pas publier ni changer la clé officielle.
