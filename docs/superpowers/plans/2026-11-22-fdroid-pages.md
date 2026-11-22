# Dépôt F-Droid GitHub Pages Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publier l’APK officiel de BlackBG dans un dépôt que le client F-Droid peut ajouter.

**Architecture:** Générer un index signé sur le Mac, puis servir les fichiers publics via GitHub Pages. Pages ne construit pas l’APK et ne détient aucune clé.

**Tech Stack:** Shell, Android SDK (`aapt`, `apksigner`), `fdroidserver`, GitHub Pages.

**Spec:** `docs/superpowers/specs/2026-11-22-fdroid-pages-design.md`

## Global Constraints

- `app.blackbg`, certificat officiel `d7f02e4701a55950eba482d631b4df25d9fd8100c21f18f99e8897f1aab2ec5e`.
- Android 16+ ARM64 ; aucune modification de l’application.
- Ne publier que les fichiers publics générés dans `repo/`.

## Review Focus

- APK absent, mauvais paquet, signature incorrecte ou plusieurs signataires : rejet avant toute écriture.
- `versionCode` déjà publié : pas de remplacement silencieux.
- Erreur de `fdroid update` : aucune publication.

### Task 1: Préparer et vérifier la génération

**Files:** `prepare-fdroid.sh`, `tests/test_fdroid.py`, `README.md`.

**Interface:** `./prepare-fdroid.sh <apk> <dossier-repo-initialisé>` vérifie l’APK et génère l’index local ; jamais de push.

- [ ] Écrire des tests avec commandes SDK et F-Droid simulées : `test_valid_apk_indexes`, `test_invalid_inputs_do_not_index`, `test_existing_version_is_not_overwritten`, `test_index_error_is_reported`. Vérifier le nom `repo/app.blackbg_<versionCode>.apk`, le rejet des quatre entrées invalides et la propagation d’un échec de génération.
- [ ] Exécuter `python3 -m unittest discover -s tests -p test_fdroid.py` et constater l’échec avant implémentation.
- [ ] Implémenter le script : comparer le paquet et le certificat, copier sans écraser, appeler `fdroid update --create-metadata` dans le dossier de travail et propager son statut.
- [ ] Documenter l’initialisation hors Git, les mises à jour et le lien avec empreinte.
- [ ] Relancer les tests et `bash -n prepare-fdroid.sh`.

### Task 2: Publier la nouvelle release

- [ ] Confirmer que la nouvelle release GitHub contient l’APK attendu ; ne pas substituer une ancienne release.
- [ ] Initialiser le dépôt local s’il n’existe pas, configurer `repo_url`, puis générer et vérifier l’index avec l’APK de la release.
- [ ] Publier uniquement `repo/` sous `fdroid/repo/` sur Pages sans écraser un site existant ; publier le lien d’ajout avec l’empreinte.
- [ ] Vérifier en HTTPS que l’index signé et l’APK sont accessibles et que l’APK servi correspond à celui de la release.
