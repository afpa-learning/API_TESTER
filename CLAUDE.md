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
    d'API exécuté (`url`, `method` restreint à `METHOD_CHOICES` — `GET`/`POST`/`PUT`/
    `DELETE` —, `status_code`/`response_time` nullables car un test peut échouer avant
    réception de toute réponse — timeout, erreur réseau —, `payload_sent`/
    `response_body` en `JSONField` natifs, `error_message`, `created_at`). Le tri par
    défaut est du plus récent au plus ancien (`-created_at`), cohérent avec son usage en
    tant qu'historique de requêtes. Migrations `0001_initial` et `0002_alter_apilog_method`
    (extension de `METHOD_CHOICES` à PUT/DELETE) appliquées.
  - `views.py`, `urls.py` — routage branché et logique métier implémentée pour le cas
    nominal et les erreurs réseau :
    - `index_view` (GET `/`, name `index`) récupère les 10 derniers `ApiLog`
      (`order_by('-created_at')[:10]`) et les passe au contexte sous la clé `history`,
      puis rend `templates/api_tester/index.html`.
    - `test_api_view` (POST `/api/test/`, name `test_api` ; `HttpResponseNotAllowed`
      sur les autres méthodes) parse `request.body` en JSON (`json.loads`, pas
      `request.POST`), valide la présence de `method`/`url` (400 sinon, sans créer
      d'`ApiLog`), puis valide que `method` (mis en majuscules) fait partie de
      `ApiLog.METHOD_CHOICES` (400 `{"error": "..."}` sinon, même format). Le dispatch
      vers `requests.get`/`post`/`put`/`delete` se fait via un dict `{méthode: fonction}`
      (single source of truth : `METHOD_CHOICES` du modèle), `timeout=5` sur chaque appel.
      Un champ optionnel `payload` du corps JSON reçu est transmis via `json=payload` à
      `requests` **uniquement pour POST/PUT** ; pour GET/DELETE, un payload fourni par
      erreur est ignoré silencieusement (mis à `None`) plutôt que de bloquer le test.
      `requests.exceptions.Timeout`, `ConnectionError` et `RequestException` (catch-all)
      sont interceptées explicitement et renvoient un `JsonResponse` **200** avec
      `status_code`/`response_time` à `null` et un `error_message` explicite (l'échec
      concerne l'API testée, pas notre endpoint). Le corps de la réponse est parsé en
      JSON avec fallback sur `response.text` si ce n'est pas du JSON
      (`response.json()` protégé par `try/except ValueError`).
    - Dans tous les cas où un test a réellement été exécuté (succès ou erreur réseau),
      un `ApiLog.objects.create(...)` est effectué avant le retour de la réponse.
      `payload_sent` stocke le payload réellement envoyé à la cible (`None` pour
      GET/DELETE ou si absent), pas le corps brut reçu du client.
      **Attention à l'unité de `response_time`** : stocké en **secondes** dans
      l'`ApiLog` (cohérent avec le commentaire de `models.py`), mais renvoyé en
      **millisecondes** (`* 1000`) dans le `JsonResponse` au client — ne pas confondre
      les deux lors de futures modifications.
  - `templates/api_tester/index.html` — template Bootstrap 5 (CDN, CSS + bundle JS avec
    Popper ; pas de copie locale dans `static/`) à deux colonnes :
    - Colonne gauche : `<form id="test-form">` (`<select id="method">` GET/POST/PUT/
      DELETE, `<input id="url" type="url">`, `<textarea id="payload">` optionnel pour
      un payload JSON — pertinent pour PUT/POST, ignoré côté serveur pour GET/DELETE —,
      bouton submit, `{% csrf_token %}` ; pas d'`action`/`method` HTML, la soumission
      est entièrement gérée en JS) suivi du conteneur `#result-panel` (`.card`) où le
      résultat d'un test est injecté dynamiquement.
    - Colonne droite : historique dans `#history-list`, une `.card` Bootstrap par
      `ApiLog` de `history` (badge méthode, badge `status_code` coloré, `response_time`
      reconverti en millisecondes via `{% widthratio %}`, `created_at`). Badge de statut
      sur un schéma de couleurs unifié avec `createStatusBadge` (JS) via une chaîne
      `{% if %}/{% elif %}` : vert `bg-success` (2xx), jaune `bg-warning text-dark`
      (4xx), rouge `bg-danger` (5xx), gris `bg-secondary` "Erreur" (`status_code` null —
      timeout/erreur réseau, pas de réponse reçue). Chaque carte porte
      `data-method="{{ log.method }}"` et `data-url="{{ log.url }}"`, pour être
      strictement équivalente aux cartes ajoutées dynamiquement en JS (mêmes attributs,
      ciblés par le même écouteur de clic).
    - `{% load static %}` en tête, script `main.js` chargé après le bundle Bootstrap.
  - `static/api_tester/js/main.js` — script JS natif (pas de framework front) qui pilote
    entièrement l'interaction :
    - Écoute `submit` sur `#test-form`, `preventDefault()` immédiat.
    - Récupère le jeton CSRF via `document.querySelector('[name=csrfmiddlewaretoken]')`
      et les valeurs de `#method`/`#url`/`#payload`. Si `#payload` est renseigné, il est
      parsé (`JSON.parse`) **avant tout envoi réseau** ; en cas d'échec,
      `displayValidationError` s'affiche directement sans solliciter le serveur (erreur
      purement côté client). Le payload n'est inclus dans le corps envoyé (clé
      `payload`) que s'il a été saisi. Envoie ensuite `fetch('/api/test/', {...})` en
      JSON strict (`Content-Type: application/json`, header `X-CSRFToken`), en capturant
      `response.status` (utilisé ensuite pour distinguer un 400 d'un test réellement
      exécuté, cf. point historique ci-dessous).
    - `createStatusBadge(statusCode)` — schéma unifié avec les badges server-rendus :
      vert `bg-success` (2xx), jaune `bg-warning text-dark` (4xx), rouge `bg-danger`
      (5xx), gris `bg-secondary` "Erreur" (`null`, pas de réponse reçue) ; réutilisée
      partout (résultat, historique) plutôt que dupliquée.
    - Si `responseStatus === 400` (format de réponse différent, `{ "error": "..." }`,
      aucun `ApiLog` créé côté serveur), `displayValidationError(data.error)` affiche
      clairement qu'il s'agit d'une erreur de saisie — pas de carte d'historique dans
      ce cas.
    - Sinon, `displayResult(data)` peuple `#result-panel` : badge de statut, temps de
      réponse en ms si présent, puis soit `error_message` en texte simple (cas
      d'erreur réseau), soit `response_body` dans un `<pre>` (`JSON.stringify(...,
      null, 2)` si objet/array, tel quel si déjà une chaîne — précédé dans ce cas d'une
      mention explicite "Réponse non-JSON (texte brut) :", CDC §2.2). Tous les éléments
      sont construits via `createElement`/`textContent` (pas d'`innerHTML` avec des
      données serveur, pour éviter toute injection).
    - `displayFetchError(message)` couvre l'échec du `fetch` lui-même (`.catch`), pour
      ne jamais laisser l'utilisateur sans retour visuel.
    - Après un test réellement exécuté (statut de réponse ≠ 400, donc un `ApiLog` a été
      créé côté serveur), `createHistoryCard(method, url, data)` construit une carte
      identique à celles rendues côté serveur (mêmes classes, réutilise
      `createStatusBadge`, pose `data-method`/`data-url`), insérée en tête de
      `#history-list` (`prepend`) ; la carte la plus ancienne est retirée si le
      conteneur dépasse 10 cartes. Le message `{% empty %}` éventuel est retiré avant
      la première insertion.
    - Un unique écouteur `click` délégué sur `#history-list` (pas un par carte, pour
      suivre les cartes ajoutées dynamiquement) utilise
      `event.target.closest('[data-method]')` pour retrouver la carte cliquée (même si
      le clic tombe sur un badge ou un texte enfant) et pré-remplit `#method`/`#url`
      avec ses `data-*` — sans relancer le test, l'utilisateur doit soumettre
      lui-même le formulaire. **Ne restaure jamais `#payload`** (CDC §5.2), même si un
      payload est bien stocké en base pour cette entrée ; les cartes (server-rendues ou
      JS) n'affichent jamais le payload non plus.
    - `static/api_tester/css/` toujours scaffoldé mais vide.

`db.sqlite3` est la base de données locale de développement (ignorée par git, tout
comme `venv/`).
