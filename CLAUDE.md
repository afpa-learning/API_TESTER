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
  - `views.py`, `urls.py` — routage branché et logique métier implémentée pour le cas
    nominal et les erreurs réseau :
    - `index_view` (GET `/`, name `index`) récupère les 10 derniers `ApiLog`
      (`order_by('-created_at')[:10]`) et les passe au contexte sous la clé `history`,
      puis rend `templates/api_tester/index.html`.
    - `test_api_view` (POST `/api/test/`, name `test_api` ; `HttpResponseNotAllowed`
      sur les autres méthodes) parse `request.body` en JSON (`json.loads`, pas
      `request.POST`), valide la présence de `method`/`url` (400 sinon, sans créer
      d'`ApiLog`), puis appelle `requests.get`/`requests.post` avec `timeout=5`.
      `requests.exceptions.Timeout`, `ConnectionError` et `RequestException` (catch-all)
      sont interceptées explicitement et renvoient un `JsonResponse` **200** avec
      `status_code`/`response_time` à `null` et un `error_message` explicite (l'échec
      concerne l'API testée, pas notre endpoint). Le corps de la réponse est parsé en
      JSON avec fallback sur `response.text` si ce n'est pas du JSON
      (`response.json()` protégé par `try/except ValueError`).
    - Dans tous les cas où un test a réellement été exécuté (succès ou erreur réseau),
      un `ApiLog.objects.create(...)` est effectué avant le retour de la réponse.
      **Attention à l'unité de `response_time`** : stocké en **secondes** dans
      l'`ApiLog` (cohérent avec le commentaire de `models.py`), mais renvoyé en
      **millisecondes** (`* 1000`) dans le `JsonResponse` au client — ne pas confondre
      les deux lors de futures modifications.
    - Reste à faire : gestion des méthodes PUT/DELETE (seuls GET/POST sont gérés,
      cohérent avec `METHOD_CHOICES` du modèle), affinage du cas réponse non-JSON,
      restauration au clic depuis l'historique (JS, session dédiée à venir).
  - `templates/api_tester/index.html` — `<h1>` + `<form>` avec `{% csrf_token %}`, plus
    une section historique basique (`<ul>/<li>`, sans classes Bootstrap) listant les 10
    derniers tests (`method`, `url`, `status_code` ou "Erreur" si `null`,
    `response_time` reconverti en millisecondes via `{% widthratio %}`, `created_at`).
    Pas encore de mise en forme Bootstrap complète ni d'attributs `data-*`/JS (sessions
    dédiées à venir). `static/api_tester/{css,js}/` toujours scaffoldés mais vides.

`db.sqlite3` est la base de données locale de développement (ignorée par git, tout
comme `venv/`).
