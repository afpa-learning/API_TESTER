# Testeur d'API HTTP

Projet pédagogique Django permettant de tester des endpoints d'API HTTP
(GET/POST/PUT/DELETE) via une interface web, avec une communication front/back
en **JSON strict** (pas de formulaires HTML classiques ni de FormData). Ce dépôt
est le corrigé de référence du projet — voir la section [Bonus](#bonus-au-delà-du-cdc)
pour ce qui va au-delà du minimum demandé aux apprenants.

## Prérequis

- Python 3 (voir la version utilisée pour générer `venv/`)
- Un accès réseau sortant pour tester des API tierces (PokeAPI, httpbin.org, etc.)

## Installation

Un environnement virtuel existe déjà dans `venv/`. Sous Windows, invoquer
directement son Python plutôt que de dépendre d'une activation persistante du
shell :

```powershell
# Installer les dépendances
.\venv\Scripts\python.exe -m pip install -r requirements.txt

# Appliquer les migrations
.\venv\Scripts\python.exe manage.py migrate

# Lancer le serveur de développement
.\venv\Scripts\python.exe manage.py runserver
```

Puis ouvrir [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

(Équivalent : activer d'abord avec `.\venv\Scripts\Activate.ps1`, puis omettre
le préfixe `.\venv\Scripts\` dans les commandes ci-dessus.)

Si `venv/` n'existe pas (nouvel environnement) : `python -m venv venv` avant
la commande d'installation des dépendances.

## Fonctionnalités

- Formulaire de test d'API : méthode (GET/POST/PUT/DELETE), URL cible, et un
  payload JSON optionnel (pour PUT/POST).
- Exécution réelle de la requête via `requests` (`timeout=5` systématique),
  résultat affiché sans rechargement de page (`fetch` JSON, jeton CSRF transmis
  en en-tête `X-CSRFToken`).
- Gestion différenciée des cas :
  - réponse nominale (2xx/4xx/5xx) : badge de statut coloré, temps de réponse,
    corps de la réponse formaté (JSON indenté, ou texte brut avec mention
    explicite si la réponse n'est pas du JSON) ;
  - erreur réseau (timeout, hôte injoignable, etc.) : message d'erreur clair,
    sans faire planter l'interface ;
  - erreur de validation (méthode/URL manquante ou invalide) : message dédié,
    aucune requête sortante n'est effectuée.
- Historique des 10 derniers tests, persistant en base (`ApiLog`) et affiché
  à la fois au chargement de la page et mis à jour dynamiquement après chaque
  nouveau test (limite de 10 cartes respectée des deux côtés).
- Clic sur une carte d'historique : restaure la méthode et l'URL dans le
  formulaire (jamais le payload, volontairement — l'utilisateur doit
  resoumettre lui-même pour relancer un test).
- Badges de statut à code couleur unifié entre l'historique et le panneau de
  résultat : vert (2xx), jaune (4xx), rouge (5xx), gris "Erreur" (pas de
  réponse reçue).

## Bonus au-delà du CDC

Le cahier des charges de base demande "GET ou POST minimum". Ce corrigé va
plus loin, en extra :

- Support complet de **PUT** et **DELETE**, en plus de GET/POST.
- **Payload JSON optionnel** pour PUT/POST, saisi dans un textarea dédié,
  validé (parsé) côté client avant tout envoi réseau, et transmis à l'API
  cible via `requests` (`json=payload`). Stocké dans `ApiLog.payload_sent`.

## Limites connues

- Pas de liste blanche de domaines ni de restriction des plages d'IP internes
  (protection SSRF) : seule une validation basique du schéma d'URL
  (http/https uniquement) est en place. Voir la note de sécurité ci-dessous et
  le commentaire dédié dans `api_tester/views.py`. Conforme au périmètre du
  CDC, qui n'exige pas de protection SSRF complète pour ce projet pédagogique.
- Pas d'authentification/autorisation : l'outil est prévu pour un usage local
  de développement, pas pour être exposé publiquement tel quel.
- Le corps envoyé à l'API cible est toujours interprété comme JSON
  (`requests(..., json=payload)`) : pas de support de payloads
  multipart/form-data ou d'autres types de contenu.

## Note sur la sécurité

- **Timeout obligatoire** : chaque appel sortant (`requests.get/post/put/delete`)
  utilise `timeout=5`, pour ne jamais bloquer indéfiniment le serveur sur une
  cible qui ne répond pas.
- **Validation du schéma d'URL** : seules les URL `http://` et `https://` sont
  acceptées (rejet explicite de `ftp://`, `file://`, etc.) avant tout appel
  sortant.
- **Sensibilisation SSRF** : l'application effectue, sur demande de
  l'utilisateur, des requêtes vers une URL (et, pour PUT/POST, un payload)
  qu'il fournit lui-même — un vecteur SSRF classique si l'outil était exposé
  sans contrôle d'accès. En production, cela nécessiterait une liste blanche
  de domaines/IP autorisés et un blocage des plages d'IP privées ; voir le
  commentaire dédié dans `api_tester/views.py`.
- Protection CSRF Django active sur toute l'application (aucune vue n'est
  marquée `@csrf_exempt`).

## Commandes utiles

```powershell
.\venv\Scripts\python.exe manage.py runserver
.\venv\Scripts\python.exe manage.py makemigrations [app_label]
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py shell
.\venv\Scripts\python.exe manage.py test                          # suite complète
.\venv\Scripts\python.exe manage.py test api_tester                # une seule app
.\venv\Scripts\python.exe manage.py test api_tester.tests.NomClasse.test_methode  # un seul test
```

Voir `CLAUDE.md` pour le détail de l'architecture du projet.
