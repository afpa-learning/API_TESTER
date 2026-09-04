# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projet

Testeur d'API HTTP — projet pédagogique Django permettant à un utilisateur de tester
des endpoints d'API HTTP (GET/POST/PUT/DELETE, etc.) via une interface web, avec une
communication front/back en **JSON strict** (pas de FormData/multipart).

## Commandes

Un environnement virtuel existe déjà dans `venv/`. Sous Windows, invoquer directement
son Python plutôt que de dépendre d'une activation persistante du shell :

```powershell
.\venv\Scripts\python.exe manage.py runserver
.\venv\Scripts\python.exe manage.py makemigrations [app_label]
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py shell
.\venv\Scripts\python.exe manage.py test                          # suite complète
.\venv\Scripts\python.exe manage.py test api_tester                # une seule app
.\venv\Scripts\python.exe manage.py test api_tester.tests.NomClasse.test_methode  # un seul test
```

(Équivalent : activer d'abord avec `.\venv\Scripts\Activate.ps1`, puis omettre le
préfixe `.\venv\Scripts\`.)

Les dépendances sont figées dans `requirements.txt` (`Django==6.0.8`,
`requests==2.34.2`) et installées dans `venv/` — installer les nouveaux paquets à cet
endroit et mettre à jour `requirements.txt`, ne pas dépendre d'un interpréteur global.

## Architecture

Structure Django classique en deux parties :

- `api_tester_project/` — squelette du projet : `settings.py`, `urls.py` racine, points
  d'entrée WSGI/ASGI. Le `urls.py` racine monte `admin/` et inclut `api_tester.urls` sur
  `''`.
- `api_tester/` — l'unique app (pour l'instant) ; toute la logique métier vit ici.
  - `models.py` — couche de données. `ApiLog` est le modèle central : une ligne par test
    d'API exécuté (`url`, `method` restreint à `METHOD_CHOICES`, `status_code`/
    `response_time` nullables car un test peut échouer avant réception de toute réponse
    — timeout, erreur réseau —, `payload_sent`/`response_body` en `JSONField` natifs,
    `error_message`, `created_at`). Le tri par défaut est du plus récent au plus ancien
    (`-created_at`), cohérent avec son usage en tant qu'historique de requêtes. La
    migration `0001_initial` est appliquée.
  - `views.py`, `urls.py` — pas encore implémentés (`urlpatterns = []`) ; rien n'est
    branché en dehors de l'admin Django.
  - `templates/api_tester/`, `static/api_tester/{css,js}/` — scaffoldés mais vides.

Comme le front communique avec le backend en JSON strict (et non via des formulaires
HTML/FormData), les vues à construire ici devront parser `request.body` en JSON et
renvoyer des `JsonResponse`, plutôt que de s'appuyer sur la gestion des formulaires/du
dict `POST` de Django.

`db.sqlite3` est la base de données locale de développement (ignorée par git, tout
comme `venv/`).
