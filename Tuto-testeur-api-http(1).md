# Tutoriel pas-à-pas — Testeur d'API HTTP avec Python et Django

Édition Windows — Titres DWWM (RNCP37674) et CDA (RNCP37873) — Python 3.13 · Django 6.0.8 · requests 2.34.2 · Bootstrap 5.3

*Version texte du tutoriel Word, générée à partir des mêmes sources. Les captures d'écran sont remplacées par leur légende.*

# Partie 0 — Avant de commencer

## 0.1 Ce que vous allez construire

Dans ce tutoriel, vous allez construire de A à Z un **Testeur d'API HTTP** : une petite application web, écrite en Python avec le framework Django, qui permet d'envoyer une requête HTTP vers n'importe quelle API et d'en afficher le résultat. C'est un outil du même type que Postman ou Insomnia, en version simplifiée.

À la fin du tutoriel, votre application saura :

- envoyer une requête **GET, POST, PUT ou DELETE** vers une URL saisie par l'utilisateur, avec un **payload JSON** optionnel pour POST et PUT ;
- afficher le **code de statut** (avec un badge de couleur), le **temps de réponse** en millisecondes et le **corps de la réponse** formaté ;
- gérer proprement les cas d'erreur : URL invalide, API qui ne répond pas (timeout), serveur introuvable, réponse qui n'est pas du JSON ;
- enregistrer chaque test en base de données et afficher un **historique des 10 derniers tests** ;
- restaurer la méthode et l'URL d'un ancien test d'un simple clic sur l'historique ;
- faire tout cela **sans jamais recharger la page**, grâce à JavaScript et `fetch`.

Vous terminerez par une **suite de tests automatisés** qui vérifie que tout fonctionne, et par la publication de votre projet sur GitHub.

*[Figure : fig-application.png] L'application terminée : le formulaire et le résultat d'un test à gauche, l'historique des derniers tests à droite, avec un badge de couleur par statut.*

## 0.2 Comment l'application fonctionne

Avant d'écrire la moindre ligne de code, il faut comprendre le trajet d'un test, du clic de l'utilisateur jusqu'à l'affichage du résultat. Ce trajet fait intervenir **quatre acteurs** :

| Acteur | Rôle |
| --- | --- |
| **Le navigateur** | Affiche la page (HTML + Bootstrap). Un script JavaScript intercepte le formulaire et discute avec le serveur Django en JSON. |
| **Le serveur Django** | Reçoit la demande de test, la valide, exécute la vraie requête HTTP avec la bibliothèque `requests`, enregistre le résultat et le renvoie au navigateur. |
| **L'API cible** | L'API que l'on veut tester (par exemple PokeAPI). Elle ne voit que le serveur Django, jamais le navigateur. |
| **La base de données** | Un fichier SQLite qui contient la table `ApiLog` : une ligne par test exécuté. |

Voici le trajet complet d'un test :

1. **Au chargement de la page** (`GET /`), Django lit les 10 derniers tests en base et génère la page HTML avec le formulaire et l'historique.
2. L'utilisateur remplit le formulaire (méthode, URL, payload éventuel) et clique sur « Tester ». **JavaScript bloque l'envoi classique** du formulaire.
3. JavaScript envoie une requête `POST /api/test/` au serveur Django, avec un corps JSON du type `{"method": "GET", "url": "https://..."}` et le jeton de sécurité CSRF dans un en-tête.
4. Django valide les données, puis **appelle lui-même l'API cible** avec `requests`. Il mesure le temps de réponse et récupère le statut et le corps.
5. Django **enregistre le test** dans la table `ApiLog`, puis renvoie le résultat au navigateur, en JSON.
6. JavaScript **affiche le résultat** dans la page et **ajoute une carte** en haut de l'historique, sans recharger la page.

> **Pourquoi ?**
>
> Pourquoi ne pas appeler l'API cible directement depuis JavaScript ? Parce que le navigateur est soumis à la règle **CORS** : la plupart des API refusent les appels venant d'un autre site. Un serveur, lui, n'a pas cette contrainte. Passer par Django permet aussi de **mesurer le temps**, de **contrôler l'URL** avant de l'appeler et d'**enregistrer l'historique** en base.

## 0.3 La structure finale du projet

Voici l'arborescence que vous aurez à la fin du tutoriel. Ne créez rien pour l'instant : chaque fichier sera créé au bon moment, dans la partie qui l'explique.

*Arborescence finale*
````
TesterAPI/
├── .gitignore
├── README.md
├── manage.py
├── requirements.txt
├── db.sqlite3                  (créé automatiquement, jamais commité)
├── venv/                       (environnement virtuel, jamais commité)
├── api_tester_project/         ← la configuration du projet
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── api_tester/                 ← l'application : toute la logique métier
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── models.py               ← le modèle ApiLog
    ├── views.py                ← index_view et test_api_view
    ├── urls.py                 ← les routes de l'application
    ├── tests.py                ← les tests automatisés
    ├── migrations/
    │   ├── __init__.py
    │   ├── 0001_initial.py
    │   └── 0002_alter_apilog_method.py
    ├── templates/api_tester/
    │   └── index.html          ← la page (Bootstrap 5)
    └── static/api_tester/
        ├── css/
        │   └── .gitkeep
        └── js/
            └── main.js         ← toute l'interactivité
````

## 0.4 Comment utiliser ce tutoriel

### Environnement

Ce tutoriel est écrit pour **Windows 10 ou 11**. Toutes les commandes sont à taper dans **PowerShell**, de préférence dans le terminal intégré de VS Code. Les versions utilisées sont les suivantes :

| Outil | Version utilisée | Remarque |
| --- | --- | --- |
| Python | 3.13 | Django 6.0 fonctionne avec Python 3.12 ou plus récent. |
| Django | 6.0.8 | Installez exactement cette version. |
| requests | 2.34.2 | Installez exactement cette version. |
| Bootstrap | 5.3 | Chargé depuis un CDN, rien à installer. |

### Les blocs de code

Chaque bloc de code porte une étiquette qui indique **où** il se place :

- **PowerShell** : une commande à taper dans le terminal, puis Entrée.
- **Un chemin de fichier** (par exemple `api_tester/models.py`) : le contenu à écrire dans ce fichier.
- **Sortie attendue** : ce que le terminal doit afficher. Votre sortie peut différer sur des détails (dates, chemins, durées).

> **À retenir**
>
> Tapez le code vous-même plutôt que de le copier-coller. C'est plus lent, mais c'est en tapant que l'on comprend et que l'on retient. Et chaque bloc est accompagné d'explications : lisez-les **avant** de taper.

### Les encadrés

| Encadré | Signification |
| --- | --- |
| **À retenir** | Une notion importante, à comprendre et à retenir. |
| **Pourquoi ?** | L'explication d'un choix technique. |
| **Attention** | Un piège fréquent ou une erreur classique. |
| **Point de vérification** | Un test à faire **obligatoirement** avant de continuer. Si le résultat n'est pas celui attendu, ne passez pas à la suite : corrigez d'abord. |
| **Commit** | Le moment d'enregistrer votre travail avec Git. |

### Un commit par partie

Chaque partie se termine par un **commit Git**. À la fin du tutoriel, votre historique Git racontera donc la construction du projet, étape par étape. C'est l'un des livrables attendus : un historique de commits lisible, qui reflète une progression logique.

## 0.5 Les compétences travaillées

Ce projet mobilise des compétences des titres professionnels **DWWM** (RNCP37674) et **CDA** (RNCP37873) :

| Partie | DWWM (RNCP37674) | CDA (RNCP37873) |
| --- | --- | --- |
| 1, 2 — Environnement et projet | BC01 — Installer et configurer son environnement de travail | BC01 — Installer et configurer son environnement de travail |
| 3 — Modèle ApiLog | BC02 — Mettre en place une base de données relationnelle<br>BC02 — Développer des composants d'accès aux données | BC02 — Concevoir et mettre en place une base de données relationnelle<br>BC02 — Développer des composants d'accès aux données |
| 4 — Routage et première vue | BC02 — Développer des composants métier côté serveur | BC02 — Définir l'architecture logicielle d'une application |
| 5 — Template Bootstrap | BC01 — Réaliser des interfaces utilisateur statiques | BC01 — Développer des interfaces utilisateur |
| 6, 7, 8 — Vue de test, requests, erreurs | BC02 — Développer des composants métier côté serveur | BC01 — Développer des composants métier |
| 9, 10, 11 — JavaScript, fetch, historique | BC01 — Développer la partie dynamique des interfaces | BC01 — Développer des interfaces utilisateur |
| 12 — Tests automatisés | — | BC03 — Préparer et exécuter les plans de tests |
| 13 — Sécurité, README, GitHub | BC02 — Documenter le déploiement | BC03 — Préparer et documenter le déploiement |

# Partie 1 — Installer l'environnement de travail

Dans cette partie, vous installez les trois outils nécessaires au projet : **Python**, **Git** et **Visual Studio Code**. Vous configurez aussi PowerShell pour qu'il accepte d'activer un environnement virtuel. Si un outil est déjà installé sur votre poste, vérifiez simplement sa version avec le point de vérification correspondant.

## 1.1 Installer Python

1. Rendez-vous sur **python.org**, rubrique **Downloads > Windows**.
2. Dans la liste des versions, repérez la dernière version **Python 3.13.x** et téléchargez le **Windows installer (64-bit)**.
3. Lancez l'installateur. **Sur le premier écran, avant toute autre action**, cochez la case **« Add python.exe to PATH »** en bas de la fenêtre.
4. Cliquez sur **Install Now** et patientez jusqu'à la fin de l'installation.
5. Sur le dernier écran, si l'option **« Disable path length limit »** apparaît, cliquez dessus (cela évite des erreurs avec les chemins de fichiers très longs), puis fermez l'installateur.

> **Attention**
>
> Si vous oubliez de cocher **« Add python.exe to PATH »**, Windows ne trouvera pas la commande `python`. Le plus simple est alors de relancer l'installateur, de choisir **Modify** puis de cocher l'option **« Add Python to environment variables »** à l'écran suivant.

> **À retenir**
>
> Selon la période, python.org peut mettre en avant le **Python install manager** plutôt que l'installateur classique. Dans ce cas, installez-le, puis tapez `py install 3.13` dans PowerShell. Le reste du tutoriel est identique.

Vérifiez maintenant l'installation. Ouvrez un **nouveau** PowerShell (menu Démarrer, tapez « PowerShell ») : une fenêtre ouverte avant l'installation ne connaît pas encore la commande `python`.

*PowerShell*
````
python --version
````

*Sortie attendue*
````
Python 3.13.7
````

Le dernier chiffre peut être différent chez vous : l'important est d'avoir une version **3.13**.

> **Attention**
>
> Si la commande `python` ouvre le **Microsoft Store** ou n'affiche rien, c'est un raccourci de Windows qui intercepte la commande. Ouvrez **Paramètres > Applications > Paramètres d'applications avancés > Alias d'exécution d'application** et désactivez les deux lignes **« Programme d'installation d'application python.exe »** et **« python3.exe »**. Fermez PowerShell, rouvrez-le et recommencez.

## 1.2 Installer et configurer Git

Git est l'outil de **gestion de versions** : il enregistre l'historique de votre code sous forme de « commits » et permettra de publier le projet sur GitHub.

1. Rendez-vous sur **git-scm.com**, rubrique **Downloads > Windows**, et téléchargez l'installateur 64 bits.
2. Lancez l'installateur. Vous pouvez garder les options par défaut, **sauf deux** :

  - écran **« Choosing the default editor used by Git »** : choisissez **Visual Studio Code** (plutôt que Vim, difficile à utiliser au début) ;
  - écran **« Adjusting the name of the initial branch »** : choisissez **« Override the default branch name »** et laissez `main`.

Une fois Git installé, ouvrez un **nouveau** PowerShell et indiquez votre nom et votre adresse e-mail. Ils apparaîtront dans chacun de vos commits. Utilisez la même adresse que sur votre compte GitHub.

*PowerShell*
````
git config --global user.name "Prénom Nom"
git config --global user.email "prenom.nom@exemple.fr"
git config --global init.defaultBranch main
````

La troisième ligne garantit que la branche principale s'appellera `main`, même si vous n'avez pas modifié l'option à l'installation.

> **Point de vérification**
>
> Tapez `git --version`. Le terminal doit afficher une ligne du type `git version 2.xx.x.windows.x`.
>
> Tapez `git config --global --list`. Vous devez retrouver votre `user.name`, votre `user.email` et `init.defaultbranch=main`.

## 1.3 Installer Visual Studio Code

1. Rendez-vous sur **code.visualstudio.com** et téléchargez la version Windows (**User Installer**).
2. Lancez l'installateur. Sur l'écran **« Sélection des tâches supplémentaires »**, cochez **« Ajouter l'action "Ouvrir avec Code" »** (pour les fichiers et pour les dossiers) et vérifiez que **« Ajouter à PATH »** est coché.
3. Terminez l'installation, puis lancez VS Code.
4. Ouvrez le panneau **Extensions** (icône des quatre carrés dans la barre de gauche, ou `Ctrl+Shift+X`).
5. Recherchez **Python** et installez l'extension publiée par **Microsoft**. Elle installe automatiquement **Pylance** (autocomplétion) et le **débogueur Python**.

*[Figure : fig-extension-python.png] L'extension **Python** de Microsoft dans le panneau Extensions. Le bouton **Uninstall** (ou **Désinstaller**) confirme qu'elle est installée. Pylance et Python Debugger apparaissent juste à côté dans la liste.*

> **Attention**
>
> Plusieurs extensions portent « Python » dans leur nom. Vérifiez que vous installez bien celle qui s'appelle exactement **Python**, publiée par **Microsoft** (badge bleu de vérification), et non une extension tierce.

> **À retenir**
>
> Facultatif mais pratique : l'extension **Django** (éditeur : Baptiste Darthenay) ajoute la coloration syntaxique des templates Django (`{% ... %}` et `{{ ... }}`), que vous écrirez à partir de la partie 4.

## 1.4 Autoriser PowerShell à activer un environnement virtuel

Dans la partie 2, vous allez **activer un environnement virtuel Python** en lançant un petit script PowerShell (`Activate.ps1`). Or, par défaut, Windows interdit l'exécution de scripts PowerShell. Si vous ne changez rien, vous obtiendrez une erreur en rouge du type :

*Erreur à éviter*
````
.\venv\Scripts\Activate.ps1 : Impossible de charger le fichier ... car l'exécution de scripts est désactivée sur ce système.
````

Pour l'éviter, autorisez les scripts locaux **pour votre utilisateur uniquement** (pas besoin d'être administrateur) :

*PowerShell*
````
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
````

Répondez `O` (Oui) si PowerShell demande une confirmation.

> **Pourquoi ?**
>
> La stratégie **RemoteSigned** autorise les scripts créés sur votre ordinateur (comme `Activate.ps1`, généré par Python), mais continue de bloquer les scripts téléchargés sur Internet qui ne sont pas signés. C'est le réglage recommandé pour un poste de développement. L'option `-Scope CurrentUser` limite le changement à votre compte.

> **Point de vérification**
>
> Tapez `Get-ExecutionPolicy -Scope CurrentUser`. Le terminal doit afficher `RemoteSigned`.

## 1.5 Utiliser le terminal intégré de VS Code

Pour la suite du tutoriel, vous travaillerez dans le **terminal intégré** de VS Code plutôt que dans une fenêtre PowerShell séparée. Ouvrez-le avec le menu **Terminal > Nouveau terminal** (raccourci `Ctrl+ù` sur un clavier AZERTY). Vérifiez en haut à droite du terminal qu'il s'agit bien de **powershell** : si ce n'est pas le cas, cliquez sur la flèche à côté du **+** et choisissez **PowerShell**.

## Récapitulatif de la partie 1

> **Point de vérification — fin de partie**
>
> Les quatre commandes suivantes fonctionnent dans le terminal intégré de VS Code :
>
> `python --version` → `Python 3.13.x`
>
> `git --version` → `git version 2.xx...`
>
> `code --version` → un numéro de version de VS Code
>
> `Get-ExecutionPolicy -Scope CurrentUser` → `RemoteSigned`

Il n'y a pas encore de projet, donc pas encore de commit : ce sera la première action de la partie 2.

# Partie 2 — Créer le projet Django

Dans cette partie, vous créez le squelette du projet : un dossier de travail, un environnement virtuel Python, le projet Django `api_tester_project` et l'application `api_tester`. À la fin, Django affichera sa page d'accueil par défaut et votre premier commit sera enregistré.

## 2.1 Créer le dossier de travail

Dans un terminal PowerShell, placez-vous dans votre dossier **Documents**, créez le dossier du projet et ouvrez-le dans VS Code :

*PowerShell*
````
cd $HOME\Documents
mkdir TesterAPI
cd TesterAPI
code .
````

Une nouvelle fenêtre VS Code s'ouvre sur le dossier vide `TesterAPI`. Si VS Code vous demande si vous faites confiance aux auteurs des fichiers de ce dossier, répondez **Oui**. **Travaillez désormais uniquement dans cette fenêtre**, avec son terminal intégré (**Terminal > Nouveau terminal**).

> **Attention**
>
> Évitez de créer le projet dans un dossier synchronisé par **OneDrive** (c'est souvent le cas du Bureau). OneDrive tente de synchroniser les milliers de petits fichiers de l'environnement virtuel, ce qui ralentit tout et peut bloquer certains fichiers.

## 2.2 Créer et activer l'environnement virtuel

Un **environnement virtuel** (ou *venv*) est un dossier qui contient une copie isolée de Python et les bibliothèques propres à **ce** projet. Ainsi, les bibliothèques installées pour ce projet n'interfèrent pas avec celles des autres projets.

*PowerShell*
````
python -m venv venv
````

Cette commande crée un dossier `venv` à la racine du projet. Activez-le maintenant :

*PowerShell*
````
.\venv\Scripts\Activate.ps1
````

Le début de la ligne de commande doit maintenant afficher `(venv)` :

*Sortie attendue*
````
(venv) PS C:\Users\VotreNom\Documents\TesterAPI>
````

> **À retenir**
>
> L'activation ne vaut que pour **le terminal en cours**. À chaque fois que vous ouvrez un nouveau terminal ou que vous rouvrez VS Code, **vérifiez la présence** de `(venv)` et, si elle manque, relancez `.\venv\Scripts\Activate.ps1`. La plupart des erreurs « module introuvable » viennent d'un environnement virtuel non activé.

Indiquez aussi à VS Code d'utiliser ce Python, pour que l'autocomplétion et la détection d'erreurs fonctionnent :

1. Ouvrez la palette de commandes avec `Ctrl+Shift+P`.
2. Tapez **Python: Select Interpreter** et validez.
3. Choisissez la ligne qui mentionne `.\venv\Scripts\python.exe`. Selon votre version de VS Code, elle porte la mention **Workspace** ou **Recommended**.

*[Figure : fig-interpreteur.png] La liste des interpréteurs Python. Choisissez celui du venv, `.\venv\Scripts\python.exe`, et non l'installation globale de Python (mention **Global**). En haut, « Selected Interpreter » confirme le choix.*

Désormais, les nouveaux terminaux ouverts dans VS Code activeront souvent le venv automatiquement.

> **Attention**
>
> Si la ligne du venv n'apparaît pas dans la liste, vérifiez que VS Code est bien ouvert **sur le dossier** `TesterAPI` (et pas sur un dossier parent), puis relancez la commande. En dernier recours, choisissez **Enter interpreter path...** et indiquez le chemin `.\venv\Scripts\python.exe`.

## 2.3 Installer Django et requests

Avec le venv activé, installez les deux bibliothèques du projet, dans leurs versions exactes :

*PowerShell*
````
python -m pip install Django==6.0.8 requests==2.34.2
````

La dernière ligne affichée commence par `Successfully installed` et liste plusieurs paquets, dont `Django-6.0.8` et `requests-2.34.2`. Les autres (`asgiref`, `sqlparse`, `tzdata`, `certifi`, `idna`, `urllib3`, `charset-normalizer`) sont des **dépendances** : des bibliothèques dont Django et requests ont eux-mêmes besoin, installées automatiquement.

> **À retenir**
>
> Si pip affiche un message `[notice] A new release of pip is available`, vous pouvez l'ignorer : ce n'est pas une erreur.

> **Pourquoi ?**
>
> Pourquoi `python -m pip` plutôt que simplement `pip` ? Cette forme garantit que c'est le pip **du Python actuellement actif** qui est utilisé, donc celui du venv. C'est plus fiable, en particulier sous Windows.

> **Point de vérification**
>
> Tapez `python -m django --version`. Le terminal doit afficher exactement `6.0.8`.

## 2.4 Créer le fichier requirements.txt

Le fichier `requirements.txt` liste les bibliothèques nécessaires au projet. Il permet à n'importe qui (un collègue, un formateur, un serveur) de réinstaller exactement les mêmes versions avec une seule commande. C'est l'un des livrables attendus.

Dans VS Code, créez un fichier `requirements.txt` **à la racine** du projet (clic droit dans la **zone vide** de l'explorateur de fichiers, sous le dossier `venv`, puis **Nouveau fichier**. Attention : un clic droit **sur** le dossier `venv` créerait le fichier à l'intérieur du venv), avec ce contenu :

*requirements.txt*
````
Django==6.0.8
requests==2.34.2
````

On n'y met que les deux bibliothèques que **le projet utilise directement** : pip installera leurs dépendances tout seul.

> **Attention**
>
> Vous rencontrerez souvent la commande `pip freeze > requirements.txt`. Elle écrit **toutes** les bibliothèques installées, dépendances comprises, ce qui rend le fichier moins lisible. De plus, sous Windows PowerShell 5.1, la redirection `>` enregistre le fichier en **UTF-16**, un encodage que GitHub affiche mal. Pour ce projet, écrivez le fichier à la main.

> **Point de vérification**
>
> Tapez `python -m pip install -r requirements.txt`. Chaque ligne doit indiquer `Requirement already satisfied` : tout est déjà installé, et le fichier est bien lu.

## 2.5 Créer le projet Django

Un **projet** Django contient la configuration générale : réglages, routes principales, points d'entrée du serveur. Créez-le avec la commande suivante. **Attention au point final**, précédé d'un espace :

*PowerShell*
````
django-admin startproject api_tester_project .
````

> **Pourquoi ?**
>
> Le point final signifie « **crée le projet ici, dans le dossier courant** ». Sans lui, Django créerait un dossier `api_tester_project` contenant lui-même un autre dossier `api_tester_project` : une double imbrication source de confusion. Avec le point, `manage.py` se retrouve directement à la racine de `TesterAPI`.

Votre projet doit maintenant ressembler à ceci :

*Arborescence*
````
TesterAPI/
├── manage.py
├── requirements.txt
├── venv/
└── api_tester_project/
    ├── __init__.py
    ├── asgi.py
    ├── settings.py
    ├── urls.py
    └── wsgi.py
````

| Fichier | Rôle |
| --- | --- |
| `manage.py` | L'outil en ligne de commande du projet : lancer le serveur, créer les migrations, lancer les tests… Toutes les commandes `python manage.py ...` passent par lui. |
| `settings.py` | Tous les réglages du projet : applications installées, base de données, templates, fichiers statiques, sécurité. |
| `urls.py` | Les routes principales : quelle URL déclenche quel code. |
| `asgi.py`, `wsgi.py` | Les points d'entrée utilisés par un serveur web en production. Vous n'y toucherez pas. |
| `__init__.py` | Fichier vide qui indique à Python que ce dossier est un module importable. |

> **Attention**
>
> Si vous obtenez `CommandError: 'api_tester_project' conflicts with the name of an existing Python module`, c'est que ce nom existe déjà : vous avez probablement lancé la commande une deuxième fois, dans un dossier où le projet existe déjà. N'utilisez jamais non plus un nom de module Python existant, comme `django` ou `test`.
>
> Si vous avez oublié le point final, supprimez le dossier `api_tester_project` créé par erreur et relancez la commande.

## 2.6 Créer l'application api_tester

Dans Django, un **projet** regroupe une ou plusieurs **applications**. Chaque application est une brique fonctionnelle qui a ses propres modèles, vues et templates. Notre projet n'en contient qu'une : `api_tester`, qui portera toute la logique métier.

*PowerShell*
````
python manage.py startapp api_tester
````

Django crée le dossier `api_tester` avec ces fichiers :

| Fichier | Rôle | Utilisé en partie |
| --- | --- | --- |
| `models.py` | Les modèles : la structure des données stockées en base. | 3 |
| `views.py` | Les vues : le code exécuté quand une URL est appelée. | 4, 6, 7, 8 |
| `tests.py` | Les tests automatisés. | 12 |
| `migrations/` | L'historique des modifications de la base de données, généré par Django. | 3 |
| `admin.py` | La configuration de l'interface d'administration de Django. | Non utilisé |
| `apps.py` | La configuration de l'application (son nom). | Non modifié |

> **À retenir**
>
> `startapp` ne crée pas de fichier `urls.py` dans l'application. Vous le créerez vous-même dans la partie 4.

## 2.7 Déclarer l'application dans le projet

Créer le dossier de l'application ne suffit pas : il faut aussi **déclarer** l'application dans les réglages, sinon Django l'ignore (pas de modèles, pas de templates, pas de fichiers statiques). Ouvrez `api_tester_project/settings.py` et ajoutez `'api_tester'` à la fin de la liste `INSTALLED_APPS` :

*api_tester_project/settings.py*
````
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'api_tester',  # notre application
]
````

N'oubliez pas la **virgule** à la fin de la ligne précédente. C'est la **seule** modification à faire dans `settings.py` pour tout le projet : les autres réglages par défaut conviennent.

> **À retenir**
>
> Profitez-en pour parcourir `settings.py`. Vous y verrez notamment `DEBUG = True` (mode développement, avec des pages d'erreur détaillées), `SECRET_KEY` (une clé secrète à ne jamais publier en production), la base de données `db.sqlite3`, et le réglage `'APP_DIRS': True` dans `TEMPLATES`, qui dit à Django de chercher les templates dans le dossier `templates/` de chaque application.

## 2.8 Créer les dossiers templates et static

L'application aura besoin de deux dossiers que `startapp` ne crée pas :

- `templates/` pour les pages HTML (partie 5) ;
- `static/` pour les fichiers envoyés tels quels au navigateur : JavaScript (parties 9 à 11) et CSS.

*PowerShell*
````
New-Item -ItemType Directory -Force api_tester\templates\api_tester, api_tester\static\api_tester\css, api_tester\static\api_tester\js
````

> **Pourquoi ?**
>
> Pourquoi un sous-dossier `api_tester` **à l'intérieur** de `templates/` et de `static/` ? Django rassemble les templates (et les fichiers statiques) de **toutes** les applications en un seul ensemble. Si deux applications avaient chacune un fichier `index.html` à la racine de leur dossier `templates/`, Django prendrait le premier trouvé, sans prévenir. En rangeant nos fichiers dans un sous-dossier au nom de l'application, on les désigne sans ambiguïté par `api_tester/index.html`. C'est ce qu'on appelle l'**espace de noms** (*namespace*).

Git ne suit pas les dossiers vides. Pour que ces dossiers apparaissent dès le premier commit, on place dans chacun un fichier vide nommé `.gitkeep` (c'est une convention, pas une fonctionnalité de Git) :

*PowerShell*
````
New-Item -ItemType File api_tester\templates\api_tester\.gitkeep, api_tester\static\api_tester\css\.gitkeep, api_tester\static\api_tester\js\.gitkeep
````

L'application doit maintenant ressembler à ceci :

*Arborescence de l'application*
````
api_tester/
├── __init__.py
├── admin.py
├── apps.py
├── models.py
├── tests.py
├── views.py
├── migrations/
│   └── __init__.py
├── static/
│   └── api_tester/
│       ├── css/.gitkeep
│       └── js/.gitkeep
└── templates/
    └── api_tester/.gitkeep
````

## 2.9 Premier lancement du serveur

Django fournit des applications intégrées (authentification, sessions, administration) qui ont besoin de tables en base de données. Créez-les avec la commande `migrate`. Elle crée au passage le fichier `db.sqlite3`, votre base de données locale :

*PowerShell*
````
python manage.py migrate
````

*Sortie attendue (extrait)*
````
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, sessions
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  ...
  Applying sessions.0001_initial... OK
````

Vérifiez ensuite que la configuration ne contient aucune erreur :

*PowerShell*
````
python manage.py check
````

*Sortie attendue*
````
System check identified no issues (0 silenced).
````

Lancez enfin le serveur de développement :

*PowerShell*
````
python manage.py runserver
````

*Sortie attendue (extrait)*
````
System check identified no issues (0 silenced).
Django version 6.0.8, using settings 'api_tester_project.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.

WARNING: This is a development server. Do not use it in a production setting. Use a production WSGI or ASGI server instead.
For more information on production servers see: https://docs.djangoproject.com/en/6.0/howto/deployment/
````

Les deux lignes `WARNING` sont **normales** : Django rappelle simplement que `runserver` est un serveur de développement, à ne pas utiliser en production.

Ouvrez votre navigateur à l'adresse **http://127.0.0.1:8000/**. Vous devez voir la page d'accueil par défaut de Django, avec une fusée et le message **« The install worked successfully! Congratulations! »**.

Le serveur occupe le terminal tant qu'il tourne. Pour l'arrêter, cliquez dans le terminal et appuyez sur `Ctrl+C`. Vous pouvez aussi garder ce terminal pour le serveur et en ouvrir un second (bouton **+** du terminal) pour taper vos autres commandes. Pensez alors à vérifier la présence de `(venv)` dans ce second terminal.

> **À retenir**
>
> En mode développement, le serveur **redémarre automatiquement** à chaque fois que vous enregistrez un fichier Python. Il est inutile de l'arrêter et de le relancer après chaque modification.

> **Point de vérification**
>
> La page de la fusée s'affiche sur http://127.0.0.1:8000/.
>
> Le fichier `db.sqlite3` est apparu à la racine du projet.

## 2.10 Initialiser Git et faire le premier commit

Avant le premier commit, il faut dire à Git quels fichiers **ne jamais enregistrer**. C'est le rôle du fichier `.gitignore`. Créez-le **à la racine** du projet (attention au point au début du nom) avec ce contenu :

*.gitignore*
````
# Environnement virtuel
venv/
env/
.venv/

# Bytecode Python
__pycache__/
*.py[cod]
*$py.class

# Base de données locale
db.sqlite3
db.sqlite3-journal

# Variables d'environnement
.env
.env.*

# Fichiers Django
*.log
media/

# Éditeurs / OS
.vscode/
.idea/
.DS_Store
Thumbs.db
````

| Élément ignoré | Pourquoi |
| --- | --- |
| `venv/` | Des milliers de fichiers propres à votre ordinateur. Le `requirements.txt` suffit à le recréer. |
| `__pycache__/` | Des fichiers compilés que Python génère tout seul à chaque exécution. |
| `db.sqlite3` | Vos données locales de test. Chacun recrée sa propre base avec `migrate`. |
| `.env` | Les fichiers qui contiennent des secrets (mots de passe, clés). Ils ne doivent **jamais** être publiés. |
| `.vscode/`, `.idea/` | Les réglages personnels de votre éditeur. |

Initialisez maintenant le dépôt Git et regardez ce qu'il s'apprête à enregistrer :

*PowerShell*
````
git init
git status
````

*Sortie attendue*
````
On branch main

No commits yet

Untracked files:
  (use "git add <file>..." to include in what will be committed)
        .gitignore
        api_tester/
        api_tester_project/
        manage.py
        requirements.txt
````

> **Point de vérification**
>
> La première ligne indique `On branch main`.
>
> `venv/` et `db.sqlite3` **n'apparaissent pas** dans la liste. S'ils apparaissent, votre `.gitignore` est mal nommé ou mal placé : il doit s'appeler exactement `.gitignore` et se trouver à la racine, à côté de `manage.py`.

Tout est correct ? Enregistrez le premier commit :

*PowerShell*
````
git add .
git commit -m "Initialisation du projet Django et de l'application api_tester"
````

> **À retenir**
>
> Git peut afficher des avertissements du type `LF will be replaced by CRLF`. Ils concernent la façon dont Windows code les fins de ligne et sont sans conséquence ici.

> **Commit — fin de la partie 2**
>
> `git log --oneline` doit afficher votre premier commit. Votre projet est maintenant sous gestion de versions.

## Pièges fréquents de la partie 2

| Symptôme | Cause probable | Solution |
| --- | --- | --- |
| `django-admin` n'est pas reconnu | Le venv n'est pas activé. | Activez-le avec `.\venv\Scripts\Activate.ps1`, ou utilisez `python -m django startproject ...`. |
| `ModuleNotFoundError: No module named 'django'` | Le venv n'est pas activé dans ce terminal. | Vérifiez la présence de `(venv)` et activez-le si besoin. |
| Erreur « l'exécution de scripts est désactivée » | PowerShell bloque `Activate.ps1`. | Refaites l'étape 1.4 (`Set-ExecutionPolicy`). |
| Dossier `api_tester_project` imbriqué dans un autre | Point final oublié dans `startproject`. | Supprimez le dossier créé et relancez la commande avec le point. |
| `CommandError: ... conflicts with the name of an existing Python module` | Commande relancée dans un projet existant, ou nom réservé. | Vérifiez que vous êtes dans le bon dossier et que le projet n'existe pas déjà. |
| Vos modifications n'apparaissent pas dans le navigateur, ou une autre application s'affiche | Un ancien `runserver` tourne encore dans un autre terminal. Sous Windows, lancer un second serveur sur le même port ne provoque souvent **aucune erreur** : c'est l'ancien qui continue de répondre. | Faites `Ctrl+C` dans chaque terminal qui fait tourner un serveur, ou fermez les terminaux en trop (icône de corbeille), puis relancez **un seul** `runserver`. |
| `venv/` apparaît dans `git status` | `.gitignore` mal nommé ou mal placé. | Renommez-le exactement `.gitignore` et placez-le à la racine. |

# Partie 3 — Le modèle ApiLog

Chaque test exécuté par l'application doit être **enregistré en base de données** : c'est ce qui permettra d'afficher l'historique. Dans Django, la structure d'une table se décrit par un **modèle** : une classe Python dont chaque attribut devient une colonne. Dans cette partie, vous écrivez le modèle `ApiLog`, vous créez la table correspondante grâce aux **migrations**, puis vous la manipulez depuis le **shell Django**.

> **Blocs de compétences**
>
> Compétences travaillées : **DWWM BC02** (mettre en place une base de données relationnelle, développer des composants d'accès aux données) et **CDA BC02** (concevoir et mettre en place une base de données relationnelle, développer des composants d'accès aux données).

## 3.1 Ce qu'il faut enregistrer pour chaque test

Avant d'écrire le code, listez les informations utiles pour un test. Une ligne de la table `ApiLog` correspond à **un test exécuté** :

| Champ | Type Django | Obligatoire ? | Contenu |
| --- | --- | --- | --- |
| `url` | `URLField` | Oui | L'URL testée. Longueur maximale : 2048 caractères. |
| `method` | `CharField` | Oui | La méthode HTTP, choisie dans une liste fermée. |
| `status_code` | `IntegerField` | Non | Le code de statut renvoyé (200, 404…). **Vide** si l'API n'a jamais répondu (timeout, serveur introuvable). |
| `response_time` | `FloatField` | Non | Le temps de réponse, **en secondes**. Vide si l'API n'a pas répondu. |
| `payload_sent` | `JSONField` | Non | Le corps JSON envoyé à l'API (pour POST et PUT). |
| `response_body` | `JSONField` | Non | Le corps de la réponse reçue. |
| `error_message` | `TextField` | Non | Un message explicite en cas d'échec. |
| `created_at` | `DateTimeField` | Automatique | La date et l'heure du test, remplies par Django. |

Vous n'avez pas besoin de déclarer de clé primaire : Django ajoute automatiquement un champ `id` qui s'incrémente à chaque nouvelle ligne.

## 3.2 Écrire le modèle

Ouvrez le fichier `api_tester/models.py`, créé par `startapp`, et remplacez tout son contenu par :

*api_tester/models.py*
````
from django.db import models

# Création des models

class ApiLog(models.Model):
    """Historique d'un test d'appel API (une ligne = un test exécuté)."""

    METHOD_CHOICES = [
        ('GET', 'GET'),
        ('POST', 'POST'),
    ]

    url = models.URLField(max_length=2048)
    method = models.CharField(max_length=10, choices=METHOD_CHOICES)

    # Nul si le test a échoué avant réception d'une réponse
    # (timeout, erreur réseau, etc.)
    status_code = models.IntegerField(null=True, blank=True)

    # Temps de réponse mesuré, exprimé en secondes (float).
    response_time = models.FloatField(null=True, blank=True)

    payload_sent = models.JSONField(null=True, blank=True)
    response_body = models.JSONField(null=True, blank=True)

    error_message = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        url_tronquee = self.url if len(self.url) <= 50 else f"{self.url[:47]}..."
        return f"{self.method} {url_tronquee} [{self.status_code or 'échec'}]"
````

Reprenons ce code bloc par bloc.

### La liste des méthodes autorisées

`METHOD_CHOICES` est une liste de couples `(valeur stockée, libellé affiché)`. Passée au paramètre `choices` du champ `method`, elle indique à Django quelles valeurs sont acceptables. Pour l'instant, seules **GET** et **POST** sont autorisées. Vous ajouterez PUT et DELETE plus loin dans le tutoriel, ce qui vous montrera comment faire évoluer un modèle existant.

La liste est déclarée **dans la classe**, et pas en dehors. Elle sera donc accessible partout sous le nom `ApiLog.METHOD_CHOICES`. La vue s'en servira pour valider la méthode reçue : la liste des méthodes autorisées n'est écrite qu'**à un seul endroit**.

### null=True et blank=True

Ces deux paramètres se ressemblent mais n'agissent pas au même niveau :

| Paramètre | Agit sur | Signification |
| --- | --- | --- |
| `null=True` | La **base de données** | La colonne peut contenir la valeur `NULL` (vide). |
| `blank=True` | La **validation** Django | Le champ peut être laissé vide lors d'une validation (formulaire, `full_clean()`). |

Pour un champ facultatif, on utilise en général les deux ensemble. C'est le cas de `status_code` et `response_time` : quand une API ne répond pas du tout, il n'y a **ni statut ni temps de réponse** à enregistrer, mais le test doit quand même être conservé dans l'historique.

### Le temps de réponse en secondes

> **Attention**
>
> `response_time` est stocké **en secondes** (par exemple `0.427`), car c'est l'unité que fournit la bibliothèque `requests`. Pourtant, l'interface affichera des **millisecondes** (`427 ms`). La conversion sera faite au moment de l'affichage. Retenez bien cette règle : **secondes en base, millisecondes à l'écran**. Confondre les deux est l'erreur la plus fréquente de ce projet.

### Les champs JSON

`payload_sent` et `response_body` utilisent `JSONField`, le type JSON **natif** de Django. Vous lui donnez directement un dictionnaire ou une liste Python : Django le convertit en JSON pour l'enregistrer, puis le reconvertit en dictionnaire quand vous le relisez.

> **Pourquoi ?**
>
> Pourquoi pas un simple `TextField` contenant du texte JSON ? Parce qu'il faudrait alors convertir à la main avec `json.dumps()` à chaque écriture et `json.loads()` à chaque lecture, avec le risque d'oublier l'un des deux. Avec `JSONField`, vous manipulez toujours des objets Python : c'est plus simple et plus sûr.

### La date de création

`auto_now_add=True` demande à Django de remplir `created_at` **automatiquement**, avec la date et l'heure de l'enregistrement, au moment de la création de la ligne. Vous n'aurez jamais à le renseigner vous-même.

### La classe Meta et la méthode __str__

La classe interne `Meta` contient des réglages du modèle. `ordering = ['-created_at']` définit le **tri par défaut** : du plus récent au plus ancien (le signe moins inverse l'ordre). C'est l'ordre naturel d'un historique.

La méthode `__str__` définit comment un objet `ApiLog` s'affiche sous forme de texte, par exemple dans le shell. Ici : la méthode, l'URL (raccourcie si elle dépasse 50 caractères) et le statut entre crochets, ou `échec` s'il n'y en a pas.

## 3.3 Créer la migration

Écrire le modèle ne crée pas la table. Django procède en deux temps :

1. `makemigrations` compare vos modèles à l'état actuel de la base et **génère un fichier de migration** : une description, en Python, des changements à appliquer.
2. `migrate` **exécute** ces migrations sur la base de données, qui est alors réellement modifiée.

Générez la migration de l'application :

*PowerShell*
````
python manage.py makemigrations api_tester
````

*Sortie attendue*
````
Migrations for 'api_tester':
  api_tester\migrations\0001_initial.py
    + Create model ApiLog
````

Un nouveau fichier est apparu dans `api_tester/migrations/`. Ouvrez-le pour voir ce que Django a généré. **Ne le modifiez pas** : il est écrit par Django et doit rester tel quel.

*api_tester/migrations/0001_initial.py (extrait, généré par Django)*
````
from django.db import migrations, models

class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ApiLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.URLField(max_length=2048)),
                ('method', models.CharField(choices=[('GET', 'GET'), ('POST', 'POST')], max_length=10)),
                ('status_code', models.IntegerField(blank=True, null=True)),
                ('response_time', models.FloatField(blank=True, null=True)),
                ('payload_sent', models.JSONField(blank=True, null=True)),
                ('response_body', models.JSONField(blank=True, null=True)),
                ('error_message', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
````

On y retrouve tous vos champs, plus le champ `id` ajouté automatiquement (de type `BigAutoField`). Appliquez maintenant la migration :

*PowerShell*
````
python manage.py migrate
````

*Sortie attendue*
````
Operations to perform:
  Apply all migrations: admin, api_tester, auth, contenttypes, sessions
Running migrations:
  Applying api_tester.0001_initial... OK
````

La table `api_tester_apilog` existe maintenant dans `db.sqlite3`. Son nom est construit automatiquement : le nom de l'application, un tiret bas, puis le nom du modèle en minuscules.

> **À retenir**
>
> Les fichiers de migration font partie du code source : ils **doivent être commités**. C'est grâce à eux qu'une autre personne qui clone votre projet pourra recréer exactement la même base avec `python manage.py migrate`. À l'inverse, `db.sqlite3` reste en dehors de Git.

## 3.4 Manipuler le modèle dans le shell Django

Le **shell Django** est une console Python dans laquelle votre projet est déjà chargé. C'est l'outil idéal pour tester un modèle avant d'écrire la moindre vue. Lancez-le :

*PowerShell*
````
python manage.py shell
````

L'invite de commande devient `>>>` : vous tapez désormais du Python. Django peut afficher un message indiquant qu'il a importé automatiquement vos modèles ; importez quand même `ApiLog` explicitement, c'est plus lisible et cela fonctionne dans tous les cas.

### Créer un test réussi

*Shell Django*
````
from api_tester.models import ApiLog
log = ApiLog.objects.create(url="https://example.com/", method="GET", status_code=200, response_time=0.25, response_body={"ok": True})
log
````

*Sortie attendue*
````
<ApiLog: GET https://example.com/ [200]>
````

`ApiLog.objects` est le **gestionnaire** du modèle : c'est par lui que passent toutes les opérations sur la table. Sa méthode `create()` crée l'objet **et** l'enregistre en base en une seule instruction. L'affichage utilise votre méthode `__str__`.

Vérifiez que les champs automatiques et JSON sont correctement remplis :

*Shell Django*
````
log.id
log.created_at
log.response_body["ok"]
````

*Sortie attendue*
````
1
datetime.datetime(2026, 9, 30, 8, 12, 45, 123456, tzinfo=datetime.timezone.utc)
True
````

L'`id` vaut `1` pour le premier test créé. Si vous refaites l'exercice, il continuera à augmenter (2, 3…) même après une suppression : une base de données ne réutilise jamais un identifiant. `created_at` a été rempli tout seul, et `response_body` est redevenu un **dictionnaire Python** : `log.response_body["ok"]` fonctionne directement, sans aucune conversion.

> **À retenir**
>
> L'heure affichée est en **UTC** (`tzinfo=datetime.timezone.utc`), c'est-à-dire avec 1 ou 2 heures de décalage par rapport à l'heure française. C'est normal : le réglage `TIME_ZONE` du projet est resté à sa valeur par défaut, `'UTC'`. Vous retrouverez ce décalage dans l'historique affiché par la page.

### Créer un test en échec

Simulez maintenant un test pour lequel l'API n'a jamais répondu : pas de statut, pas de temps de réponse, mais un message d'erreur.

*Shell Django*
````
echec = ApiLog.objects.create(url="http://10.255.255.1/", method="GET", error_message="La requête a expiré (timeout).")
echec
````

*Sortie attendue*
````
<ApiLog: GET http://10.255.255.1/ [échec]>
````

Aucune erreur : grâce à `null=True`, la base accepte que `status_code` et `response_time` soient vides.

### Lire la table

*Shell Django*
````
ApiLog.objects.count()
ApiLog.objects.all()
````

*Sortie attendue*
````
2
<QuerySet [<ApiLog: GET http://10.255.255.1/ [échec]>, <ApiLog: GET https://example.com/ [200]>]>
````

Le test en échec, créé en dernier, apparaît **en premier** : c'est l'effet de `ordering = ['-created_at']`, appliqué sans que vous ayez à le demander.

### Les choix ne sont pas vérifiés par la base

Essayez de préparer un test avec une méthode qui n'est pas dans `METHOD_CHOICES`, puis demandez à Django de le valider avec `full_clean()` :

*Shell Django*
````
faux = ApiLog(url="https://example.com/", method="PATCH")
faux.full_clean()
````

*Sortie attendue (dernière ligne)*
````
django.core.exceptions.ValidationError: {'method': ["Value 'PATCH' is not a valid choice."]}
````

> **Attention**
>
> Le paramètre `choices` est vérifié **uniquement lors d'une validation** (`full_clean()`, formulaires Django). La base de données, elle, ne vérifie rien : un `ApiLog.objects.create(..., method="PATCH")` serait enregistré sans erreur. Conclusion : **c'est à votre code de valider les données avant de les enregistrer**. Vous le ferez dans la vue, en partie 6. Ici, `faux` n'a jamais été enregistré (`ApiLog(...)` crée l'objet en mémoire seulement).

### Nettoyer et quitter

Supprimez les données de test pour repartir d'une table vide, puis quittez le shell :

*Shell Django*
````
ApiLog.objects.all().delete()
exit()
````

*Sortie attendue (première commande)*
````
(2, {'api_tester.ApiLog': 2})
````

`delete()` renvoie le nombre de lignes supprimées, suivi du détail par modèle.

> **Point de vérification — fin de partie**
>
> `python manage.py showmigrations api_tester` affiche `[X] 0001_initial` : la migration est appliquée.
>
> Dans le shell, vous avez pu créer un test réussi et un test en échec, les relire dans le bon ordre (plus récent en premier), puis les supprimer.

## 3.5 Enregistrer votre travail

*PowerShell*
````
git add .
git commit -m "Ajout du modèle ApiLog et de sa migration initiale"
````

> **Commit — fin de la partie 3**
>
> `git show --stat` doit lister `api_tester/models.py` et `api_tester/migrations/0001_initial.py`, mais **pas** `db.sqlite3`.

## Pièges fréquents de la partie 3

| Symptôme | Cause probable | Solution |
| --- | --- | --- |
| `No changes detected` | L'application n'est pas déclarée dans `INSTALLED_APPS`, ou `models.py` n'a pas été enregistré. | Vérifiez l'étape 2.7 et enregistrez le fichier (`Ctrl+S`). |
| `OperationalError: no such table: api_tester_apilog` | La migration a été générée mais pas appliquée. | Lancez `python manage.py migrate`. |
| `NameError: name 'ApiLog' is not defined` dans le shell | Import oublié, ou shell ouvert avant la création du modèle. | Tapez `from api_tester.models import ApiLog`, ou quittez et relancez le shell. |
| `IndentationError` ou `SyntaxError` au lancement | Indentation incorrecte dans `models.py` (mélange d'espaces et de tabulations, `Meta` mal indentée). | Utilisez 4 espaces par niveau. La classe `Meta` et `__str__` sont indentées **dans** `ApiLog`. |
| Vous avez modifié le modèle mais rien ne change en base | Toute modification d'un modèle demande une **nouvelle** migration. | Relancez `makemigrations` puis `migrate`. Ne modifiez jamais une migration déjà appliquée. |

# Partie 4 — Routage et première vue

La table existe, mais aucune page de l'application ne l'affiche encore : l'adresse `http://127.0.0.1:8000/` montre toujours la fusée de Django. Dans cette partie, vous branchez la première **route** de l'application sur une **vue**, `index_view`, qui lit les 10 derniers tests en base et les transmet à un **template** HTML. La page sera encore très simple : elle deviendra une vraie interface Bootstrap en partie 5.

> **Blocs de compétences**
>
> Compétences travaillées : **DWWM BC02** (développer des composants métier côté serveur) et **CDA BC02** (définir l'architecture logicielle d'une application).

## 4.1 Le trajet d'une requête dans Django

Quand le navigateur demande une page, Django suit toujours le même chemin, qui correspond à une **architecture en couches** :

1. **Le routage** (`urls.py`) : Django compare l'adresse demandée à une liste de routes et trouve la vue à appeler.
2. **La vue** (`views.py`) : une fonction Python qui reçoit la requête, récupère les données nécessaires (ici, par le modèle) et prépare la réponse.
3. **Les données** (`models.py`) : le modèle `ApiLog` interroge la base de données.
4. **La présentation** (le template) : un fichier HTML dans lequel la vue injecte les données, avant de le renvoyer au navigateur.

Chaque couche a un seul rôle. Cette séparation rend le code plus lisible, plus facile à tester et à faire évoluer : c'est l'une des attentes de la conception d'une application organisée en couches.

## 4.2 Écrire la vue index_view

Ouvrez `api_tester/views.py` et remplacez son contenu par :

*api_tester/views.py*
````
from django.shortcuts import render

from .models import ApiLog

# Création des views

def index_view(request):
    history = ApiLog.objects.order_by('-created_at')[:10]
    return render(request, 'api_tester/index.html', {"history": history})
````

Trois lignes suffisent :

- `ApiLog.objects.order_by('-created_at')` trie les tests du plus récent au plus ancien ;
- `[:10]` ne garde que les **10 premiers**. Django traduit ce découpage en une clause `LIMIT 10` dans la requête SQL : seules 10 lignes sont lues en base, même si la table en contient des milliers ;
- `render()` charge le template `api_tester/index.html`, y injecte un **contexte** (un dictionnaire dont la clé `history` contient les 10 tests) et renvoie la page HTML obtenue.

> **Pourquoi ?**
>
> Le tri par défaut du modèle (`Meta.ordering`) donne déjà le bon ordre. Pourquoi l'écrire à nouveau avec `order_by()` ? Pour que la vue soit **explicite** : en lisant cette seule ligne, on sait exactement quels tests sont affichés, sans aller chercher le réglage dans `models.py`. Si un jour le tri par défaut du modèle change, l'historique, lui, ne changera pas.

> **À retenir**
>
> L'import `from .models import ApiLog` commence par un point : c'est un **import relatif**, qui signifie « le fichier `models.py` du même dossier ». Il fonctionne quel que soit le nom du projet.

## 4.3 Créer les routes de l'application

Comme vu en partie 2, `startapp` ne crée pas de fichier de routes dans l'application. Créez un nouveau fichier `urls.py` **dans le dossier `api_tester`** (à côté de `views.py`), avec ce contenu :

*api_tester/urls.py*
````
"""
Configuration des URL pour l'app api_tester.
"""
from django.urls import path

from . import views

urlpatterns = [
    path('', views.index_view, name='index'),
]
````

`path()` associe un **chemin** à une **vue**. Le chemin vide `''` correspond à la racine de l'application. Le paramètre `name` donne un nom à la route : il permettra de la désigner sans écrire l'adresse en dur, ce que vous ferez dans les tests automatisés (partie 12).

Il faut maintenant dire au projet de prendre en compte ces routes. Ouvrez `api_tester_project/urls.py` et remplacez son contenu par :

*api_tester_project/urls.py*
````
"""
Configuration des URL pour le projet api_tester_project.

"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('api_tester.urls')),
]
````

`include()` **délègue** une partie des adresses à l'application. Ici, toutes les adresses qui ne commencent pas par `admin/` sont confiées aux routes de `api_tester/urls.py`. Le projet n'a pas à connaître le détail des routes de l'application : chacun reste responsable de sa partie.

> **À retenir**
>
> N'oubliez pas d'ajouter `include` dans la ligne d'import : `from django.urls import include, path`.

## 4.4 Un premier template, volontairement simple

Créez le fichier `index.html` dans le dossier `api_tester/templates/api_tester/`, préparé en partie 2. Vous pouvez supprimer le fichier `.gitkeep` de ce dossier : il n'est plus vide, Git le suivra désormais.

*api_tester/templates/api_tester/index.html*
````
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Testeur d'API HTTP</title>
</head>
<body>
    <h1>Testeur d'API HTTP</h1>

    <h2>Historique</h2>
    <ul>
        {% for log in history %}
        <li>
            {{ log.method }} {{ log.url }} —
            {% if not log.status_code %}Erreur{% else %}{{ log.status_code }}{% endif %}
            {% if log.response_time %}
                — {% widthratio log.response_time 1 1000 %} ms
            {% endif %}
            — {{ log.created_at }}
        </li>
        {% empty %}
        <li>Aucun test effectué pour l'instant.</li>
        {% endfor %}
    </ul>
</body>
</html>
````

Ce fichier mélange du HTML et le **langage de template** de Django :

| Syntaxe | Rôle | Exemple dans le fichier |
| --- | --- | --- |
| `{{ ... }}` | Affiche une valeur. | `{{ log.url }}` affiche l'URL du test. |
| `{% ... %}` | Exécute une instruction (boucle, condition…). | `{% for log in history %}` parcourt les tests. |
| `{% empty %}` | Contenu affiché si la liste parcourue est vide. | Le message « Aucun test effectué ». |
| `{% if not ... %}` | Condition. | Affiche « Erreur » quand le statut est vide. |

### Convertir les secondes en millisecondes

Le temps de réponse est stocké **en secondes** (partie 3), mais on veut l'afficher **en millisecondes**. Le langage de template de Django ne permet pas d'écrire une multiplication comme `log.response_time * 1000`. On utilise donc la balise `{% widthratio %}`, prévue à l'origine pour calculer des largeurs de barres :

*Principe*
````
{% widthratio valeur maximum largeur %}   →   valeur ÷ maximum × largeur, arrondi à l'entier
````

Avec `{% widthratio log.response_time 1 1000 %}`, on obtient `response_time ÷ 1 × 1000`, soit le temps en millisecondes. Pour `0.427` secondes, la page affiche `427 ms`. Le résultat est **arrondi à l'entier**.

> **À retenir**
>
> Le `{% if log.response_time %}` évite d'afficher « ms » pour un test en échec, dont le temps de réponse est vide.

## 4.5 Vérifier le résultat

Si le serveur ne tourne plus, relancez-le avec `python manage.py runserver`, puis ouvrez **http://127.0.0.1:8000/**. La fusée a disparu : vous voyez le titre « Testeur d'API HTTP », la rubrique « Historique » et le message **« Aucun test effectué pour l'instant. »**, puisque la table est vide.

Remplissez maintenant la table pour vérifier la **limite de 10** et le **tri**. Dans un second terminal (avec le venv activé), ouvrez le shell Django :

*PowerShell*
````
python manage.py shell
````

Tapez ensuite ces lignes. La boucle `for` s'étend sur deux lignes : après la deuxième, appuyez **deux fois** sur Entrée pour l'exécuter.

*Shell Django*
````
from api_tester.models import ApiLog
for i in range(12):
    ApiLog.objects.create(url=f"https://example.com/{i}", method="GET", status_code=200, response_time=0.1 + i / 100)

ApiLog.objects.create(url="http://10.255.255.1/", method="GET", error_message="La requête a expiré (timeout).")
ApiLog.objects.count()
exit()
````

Pendant la boucle, le shell affiche une ligne par test créé (`<ApiLog: GET https://example.com/0 [200]>`, etc.) : c'est normal, il montre simplement le résultat de chaque `create()`. La commande `ApiLog.objects.count()` doit afficher `13` : 12 tests réussis, plus un test en échec.

Rechargez la page dans le navigateur (`F5`).

> **Point de vérification — fin de partie**
>
> La page affiche **exactement 10 lignes**, alors que la table contient 13 tests.
>
> La **première** ligne est le test en échec : `GET http://10.255.255.1/ — Erreur — ...`, sans temps de réponse.
>
> Viennent ensuite `https://example.com/11`, puis `/10`, et ainsi de suite jusqu'à `/3`. Les tests `/0`, `/1` et `/2`, les plus anciens, ne sont pas affichés.
>
> Les temps de réponse sont affichés en millisecondes : `210 ms` pour `/11`, `200 ms` pour `/10`, etc.

> **À retenir**
>
> **Gardez ces 13 tests en base** : ils vous serviront en partie 5 pour vérifier l'affichage de l'historique mis en forme.

> **À retenir**
>
> L'heure affichée est en UTC et au format anglais (par exemple `Sept. 30, 2026, 8:12 a.m.`) : c'est la conséquence des réglages par défaut `TIME_ZONE = 'UTC'` et `LANGUAGE_CODE = 'en-us'`. Ce n'est pas une erreur.

## 4.6 Enregistrer votre travail

*PowerShell*
````
git add .
git commit -m "Routage et vue index_view avec l'historique des 10 derniers tests"
````

> **Commit — fin de la partie 4**
>
> `git log --oneline` affiche maintenant trois commits, un par partie depuis la partie 2.

## Pièges fréquents de la partie 4

| Symptôme | Cause probable | Solution |
| --- | --- | --- |
| La fusée de Django s'affiche toujours | Le `include()` n'a pas été ajouté dans `api_tester_project/urls.py`, ou le fichier n'est pas enregistré. | Vérifiez la section 4.3 et enregistrez les deux fichiers `urls.py`. |
| `TemplateDoesNotExist at /` avec `api_tester/index.html` | Le template n'est pas au bon endroit. | Le chemin complet doit être `api_tester/templates/api_tester/index.html`. Vérifiez les noms de dossiers (au pluriel : `templates`). |
| `NameError: name 'include' is not defined` | Import oublié dans `api_tester_project/urls.py`. | `from django.urls import include, path`. |
| `AttributeError: module 'api_tester.views' has no attribute 'index_view'` | Nom de la fonction différent entre `views.py` et `urls.py`. | Les deux fichiers doivent utiliser exactement `index_view`. |
| `TemplateSyntaxError` | Une balise `{% ... %}` mal fermée ou mal orthographiée (`endfor`, `endif`). | Lisez le numéro de ligne indiqué par la page d'erreur de Django et comparez avec le code de la section 4.4. |
| La page affiche plus de 10 tests | Le `[:10]` a été oublié dans la vue. | `ApiLog.objects.order_by('-created_at')[:10]`. |

# Partie 5 — Le template Bootstrap

La page actuelle affiche les bonnes données, mais sous forme d'une simple liste. Dans cette partie, vous la remplacez par l'interface définitive : **deux colonnes** mises en forme avec **Bootstrap 5**, le **formulaire** de test à gauche avec son panneau de résultat, et l'**historique** sous forme de cartes à droite, avec un badge de couleur par statut. La page reste pour l'instant **statique** : le formulaire ne fera rien avant la partie 9, où JavaScript prendra le relais.

> **Blocs de compétences**
>
> Compétences travaillées : **DWWM BC01** (réaliser des interfaces utilisateur statiques) et **CDA BC01** (développer des interfaces utilisateur).

## 5.1 Bootstrap en quelques mots

**Bootstrap** est une bibliothèque CSS qui fournit une grille de mise en page et des composants prêts à l'emploi (formulaires, cartes, badges, boutons). On l'utilise en ajoutant des **classes** aux balises HTML : pas besoin d'écrire de CSS.

Vous le chargerez depuis un **CDN** (*Content Delivery Network*) : un serveur public qui héberge les fichiers de Bootstrap. Il suffit d'une balise `<link>` pour le CSS et d'une balise `<script>` pour la partie JavaScript de Bootstrap. Rien à installer ni à copier dans le projet.

Voici les classes utilisées dans ce projet :

| Classe | Effet |
| --- | --- |
| `container`, `py-4` | Centre le contenu avec des marges ; `py-4` ajoute un espacement vertical. |
| `row`, `col-lg-7`, `col-lg-5` | La **grille** : une ligne découpée en 12 unités. Sur un grand écran (`lg`, 992 px et plus), la colonne de gauche en prend 7 et celle de droite 5. Sur un écran plus petit, les colonnes s'empilent. |
| `g-4`, `g-2` | L'espacement (*gutter*) entre les colonnes. |
| `form-label`, `form-select`, `form-control` | La mise en forme des étiquettes, des listes déroulantes et des champs de saisie. |
| `btn btn-primary` | Un bouton bleu. |
| `card`, `card-body`, `card-text` | Une carte : un cadre avec une bordure et un espacement intérieur. |
| `badge bg-success`, `bg-warning`, `bg-danger`, `bg-secondary` | Une étiquette colorée : vert, jaune, rouge, gris. |
| `d-flex`, `justify-content-between`, `align-items-center` | Aligne des éléments sur une ligne (ici, les deux badges d'une carte, aux deux extrémités). |
| `text-break`, `text-muted` | Coupe les URL trop longues ; affiche un texte en gris. |

## 5.2 Le code de la page

Remplacez **tout** le contenu de `api_tester/templates/api_tester/index.html` par le code ci-dessous. Il est long : prenez le temps de le taper bloc par bloc, en vous aidant des explications de la section 5.3.

*api_tester/templates/api_tester/index.html*
````
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Testeur d'API HTTP</title>
    <link
        href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
        rel="stylesheet"
    >
</head>
<body>
<div class="container py-4">
    <div class="row g-4">
        <!-- Colonne gauche : formulaire de test + résultat -->
        <div class="col-lg-7">
            <h1 class="mb-4">Testeur d'API HTTP</h1>

            <!-- la soumission sera gérée en JavaScript : pas d'action/method ici -->
            <form id="test-form" class="mb-4">
                {% csrf_token %}
                <div class="row g-2">
                    <div class="col-3">
                        <label for="method" class="form-label">Méthode</label>
                        <select id="method" name="method" class="form-select">
                            <option value="GET">GET</option>
                            <option value="POST">POST</option>
                        </select>
                    </div>
                    <div class="col-7">
                        <label for="url" class="form-label">URL</label>
                        <input
                            type="url" id="url" name="url" class="form-control"
                            placeholder="https://exemple.com/api/..."
                        >
                    </div>
                    <div class="col-2 d-flex align-items-end">
                        <button type="submit" class="btn btn-primary w-100">Tester</button>
                    </div>
                </div>
                <div class="row g-2 mt-1">
                    <div class="col-12">
                        <label for="payload" class="form-label">Payload JSON (optionnel — PUT/POST)</label>
                        <textarea
                            id="payload" name="payload" class="form-control" rows="4"
                            placeholder='{"cle": "valeur"}'
                        ></textarea>
                    </div>
                </div>
            </form>

            <!-- panneau de résultat, rempli plus tard en JavaScript -->
            <div id="result-panel" class="card">
                <div class="card-body">
                    <p class="card-text text-muted mb-0">Aucun test exécuté.</p>
                </div>
            </div>
        </div>

        <!-- Colonne droite : historique -->
        <div class="col-lg-5">
            <h2 class="mb-4">Historique</h2>

            <!-- conteneur stable : JavaScript y ajoutera aussi des cartes -->
            <div id="history-list" class="d-flex flex-column gap-3">
                {% for log in history %}
                <div class="card" data-method="{{ log.method }}" data-url="{{ log.url }}">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <span class="badge bg-secondary">{{ log.method }}</span>
                            {# vert 2xx / jaune 4xx / rouge 5xx / gris "Erreur" sans réponse #}
                            {% if not log.status_code %}
                                <span class="badge bg-secondary">Erreur</span>
                            {% elif log.status_code >= 200 and log.status_code < 300 %}
                                <span class="badge bg-success">{{ log.status_code }}</span>
                            {% elif log.status_code >= 400 and log.status_code < 500 %}
                                <span class="badge bg-warning text-dark">{{ log.status_code }}</span>
                            {% elif log.status_code >= 500 and log.status_code < 600 %}
                                <span class="badge bg-danger">{{ log.status_code }}</span>
                            {% else %}
                                <span class="badge bg-secondary">{{ log.status_code }}</span>
                            {% endif %}
                        </div>
                        <p class="card-text text-break mb-1">{{ log.url }}</p>
                        <p class="card-text mb-0">
                            <small class="text-muted">
                                <!-- secondes en base, affichées en ms -->
                                {% if log.response_time %}
                                    {% widthratio log.response_time 1 1000 %} ms —
                                {% endif %}
                                {{ log.created_at }}
                            </small>
                        </p>
                    </div>
                </div>
                {% empty %}
                <p class="text-muted">Aucun test effectué pour l'instant.</p>
                {% endfor %}
            </div>
        </div>
    </div>
</div>

<script
    src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"
></script>
</body>
</html>
````

## 5.3 Comprendre la page

### L'en-tête

La balise `<meta name="viewport" ...>` indique aux téléphones d'afficher la page à la largeur de leur écran, sans la réduire : sans elle, la grille responsive de Bootstrap ne fonctionne pas sur mobile. Le `<link>` charge le CSS de Bootstrap. Le `<script>` de Bootstrap, lui, est placé **en fin de page**, juste avant `</body>`, pour ne pas retarder l'affichage.

### Le formulaire

Le formulaire contient les trois champs du CDC : la **méthode** (liste déroulante limitée à GET et POST pour l'instant, comme le modèle), l'**URL** et le **payload** JSON optionnel. Remarquez plusieurs choix :

- la balise `<form>` n'a **ni `action` ni `method`** : c'est JavaScript qui interceptera l'envoi en partie 9 ;
- chaque champ a un `id` (`method`, `url`, `payload`) : JavaScript s'en servira pour lire leurs valeurs, et chaque `<label for="...">` y fait référence, ce qui rend le formulaire accessible (un clic sur l'étiquette active le champ) ;
- `{% csrf_token %}` ajoute un champ caché qui contient le **jeton CSRF**, une protection de sécurité que vous utiliserez en partie 9 ;
- le champ URL est de type `url` : sur mobile, le clavier propose directement `/` et `.com`.

> **Attention**
>
> **Ne cliquez pas encore sur « Tester »**. Sans JavaScript, le navigateur envoie le formulaire de façon classique : la page se recharge avec les valeurs saisies ajoutées à l'adresse (`?csrfmiddlewaretoken=...&method=GET&url=...`), et aucun test n'est exécuté. Si cela arrive, revenez simplement sur http://127.0.0.1:8000/. Le bouton deviendra fonctionnel en partie 9.

### Le panneau de résultat

La carte `#result-panel` n'affiche pour l'instant que « Aucun test exécuté. ». Son `id` permettra à JavaScript de la retrouver pour y afficher le résultat de chaque test (partie 10).

### Les cartes de l'historique

Chaque test de `history` devient une carte avec, en haut, un badge gris pour la méthode et un badge coloré pour le statut. La couleur est choisie par une suite de conditions `{% if %}` / `{% elif %}` :

| Statut | Signification | Badge |
| --- | --- | --- |
| Vide | L'API n'a jamais répondu (timeout, serveur introuvable). | Gris, texte « Erreur » (`bg-secondary`) |
| 200 à 299 | Succès. | Vert (`bg-success`) |
| 400 à 499 | L'API a répondu, mais signale une erreur dans la requête (page introuvable, accès refusé…). | Jaune (`bg-warning text-dark`) |
| 500 à 599 | L'API a répondu, mais a rencontré une erreur de son côté. | Rouge (`bg-danger`) |
| Autre | Un statut inhabituel (1xx, 3xx). | Gris, avec le code |

> **À retenir**
>
> Le texte du badge jaune est forcé en noir (`text-dark`) : du blanc sur du jaune serait illisible. Pensez toujours au **contraste** des couleurs.

La première condition est `{% if not log.status_code %}` : elle est vraie quand le statut est vide (`None`). Elle doit être testée **en premier**, car les comparaisons suivantes (`>= 200`…) n'ont pas de sens sur une valeur vide.

Enfin, chaque carte porte deux attributs `data-method` et `data-url`. Les attributs `data-*` servent à attacher des informations à une balise HTML sans les afficher. En partie 11, un clic sur une carte lira ces attributs pour remplir le formulaire.

> **Pourquoi ?**
>
> Que se passerait-il si une URL testée contenait du code HTML, comme `https://exemple.com/<script>alert(1)</script>` ? Rien de dangereux : Django **échappe automatiquement** toutes les valeurs affichées avec `{{ ... }}`. Les caractères `<` et `>` sont transformés en `&lt;` et `&gt;`, et le navigateur les affiche comme du texte au lieu de les exécuter. C'est une protection contre les attaques **XSS** (*Cross-Site Scripting*).

## 5.4 Vérifier le résultat

Les 13 tests créés en partie 4 sont tous verts, sauf celui en échec. Pour vérifier les autres couleurs, ajoutez trois tests depuis le shell Django :

*Shell Django (python manage.py shell)*
````
from api_tester.models import ApiLog
ApiLog.objects.create(url="https://httpbin.org/status/404", method="GET", status_code=404, response_time=0.8)
ApiLog.objects.create(url="https://httpbin.org/status/500", method="GET", status_code=500, response_time=0.9)
ApiLog.objects.create(url="https://jsonplaceholder.typicode.com/posts", method="POST", status_code=201, response_time=0.7)
exit()
````

Rechargez http://127.0.0.1:8000/. La page doit ressembler à ceci (avec vos propres tests dans l'historique) :

*[Figure : fig-historique-bootstrap.png] La page mise en forme avec Bootstrap : formulaire et panneau de résultat vide à gauche, historique en cartes à droite, avec les quatre couleurs de badges (rouge 500, vert 2xx, jaune 404, gris « Erreur »).*

> **Point de vérification — fin de partie**
>
> La page s'affiche sur **deux colonnes** sur un écran d'ordinateur. En réduisant la largeur de la fenêtre, les colonnes s'**empilent** (l'historique passe sous le formulaire).
>
> Les trois premières cartes sont, dans l'ordre : **POST 201** (vert), **GET 500** (rouge) et **GET 404** (jaune, texte noir). Vient ensuite le test en échec, avec un badge **gris « Erreur »** et sans temps de réponse.
>
> L'historique contient toujours **10 cartes** au maximum.
>
> La liste « Méthode » propose GET et POST, et le panneau de gauche affiche « Aucun test exécuté. ».

> **À retenir**
>
> Un clic droit sur la page, puis **Afficher le code source**, montre le HTML envoyé par Django. Cherchez-y `csrfmiddlewaretoken` : c'est le champ caché généré par `{% csrf_token %}`. Vous y verrez aussi les attributs `data-method` et `data-url` de chaque carte, remplis avec les valeurs de la base.

## 5.5 Enregistrer votre travail

*PowerShell*
````
git add .
git commit -m "Interface Bootstrap : formulaire, panneau de résultat et historique en cartes"
````

> **Commit — fin de la partie 5**
>
> Un seul fichier a changé dans ce commit : `index.html`. Vérifiez-le avec `git show --stat`.

## Pièges fréquents de la partie 5

| Symptôme | Cause probable | Solution |
| --- | --- | --- |
| La page s'affiche sans aucune mise en forme | Le CSS de Bootstrap ne se charge pas : faute de frappe dans l'URL du `<link>`, ou pas de connexion Internet. | Vérifiez l'adresse du CDN caractère par caractère. Dans les outils de développement (F12), l'onglet **Console** signale les fichiers introuvables. |
| `TemplateSyntaxError: Invalid block tag ... 'elif'` | Un `{% if %}` mal fermé ou un `{% endif %}` manquant. | Chaque `{% if %}` doit avoir son `{% endif %}`. Comptez-les. |
| Tous les badges de statut sont gris | Les conditions sont écrites dans le mauvais ordre, ou il manque des espaces autour de `>=` et `<`. | Django exige un espace de chaque côté des opérateurs : `log.status_code >= 200`, pas `log.status_code>=200`. |
| Les colonnes ne se mettent pas côte à côte | La fenêtre est plus étroite que 992 px, ou la balise `<div class="row">` est absente. | Élargissez la fenêtre, puis vérifiez la structure `container` > `row` > `col-lg-*`. |
| L'adresse contient `?csrfmiddlewaretoken=...` après un clic sur Tester | Envoi classique du formulaire, sans JavaScript (normal à ce stade). | Revenez sur http://127.0.0.1:8000/. Le bouton fonctionnera en partie 9. |

# Partie 6 — La vue de test : validation

Le cœur de l'application est une deuxième vue, `test_api_view`. Elle reçoit une demande de test envoyée en JSON, appelle l'API cible, enregistre le résultat et le renvoie, lui aussi en JSON. Vous allez la construire en **trois étapes**, une par partie :

| Partie | Ce que fait la vue |
| --- | --- |
| **6 — Validation** (cette partie) | Refuser tout ce qui n'est pas correct **avant** le moindre appel réseau. |
| **7 — Appel avec requests** | Appeler l'API cible, enregistrer le test, renvoyer le résultat. |
| **8 — Erreurs réseau** | Rester fiable quand l'API cible ne répond pas. |

Commencer par la validation n'est pas un hasard : une vue qui reçoit des données de l'extérieur doit **d'abord** vérifier ce qu'elle reçoit. C'est un principe de base de la sécurité d'une application.

> **Blocs de compétences**
>
> Compétences travaillées : **DWWM BC02** (développer des composants métier côté serveur) et **CDA BC01** (développer des composants métier, sécuriser les entrées).

## 6.1 Le contrat de l'endpoint /api/test/

La nouvelle adresse `/api/test/` n'affiche pas de page : c'est un **endpoint d'API**, appelé par du code et non par un humain. Avant de l'écrire, fixez son **contrat**, c'est-à-dire ce qu'il accepte et ce qu'il renvoie :

- il n'accepte que la méthode **POST** ;
- le corps de la requête est du **JSON**, de la forme `{"method": "GET", "url": "https://...", "payload": {...}}`, où `payload` est facultatif ;
- la réponse est **toujours** du JSON ;
- en cas de données invalides, il répond avec le statut **400** (*Bad Request*) et un corps `{"error": "message explicite"}`, **sans appeler l'API cible et sans rien enregistrer**.

> **Pourquoi ?**
>
> Pourquoi du JSON plutôt qu'un formulaire HTML classique ? C'est une exigence du cahier des charges : l'endpoint doit se comporter comme une **vraie API**, dans laquelle client et serveur échangent uniquement du JSON. C'est aussi ce que vous rencontrerez en entreprise dès que vous développerez une API ou une application JavaScript.

## 6.2 Écrire la validation

Ouvrez `api_tester/views.py`. Complétez les imports en haut du fichier, puis ajoutez la fonction `test_api_view` **après** `index_view`. Voici le fichier complet :

*api_tester/views.py*
````
import json
from urllib.parse import urlparse

from django.http import HttpResponseNotAllowed, JsonResponse
from django.shortcuts import render

from .models import ApiLog

# Création des views

def index_view(request):
    history = ApiLog.objects.order_by('-created_at')[:10]
    return render(request, 'api_tester/index.html', {"history": history})

def test_api_view(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    data = json.loads(request.body)
    method = data.get('method')
    url = data.get('url')
    payload = data.get('payload')

    if not method or not url:
        return JsonResponse(
            {"error": "Les champs 'method' et 'url' sont requis."}, status=400
        )

    # Schéma HTTP/HTTPS uniquement (CDC §3.2) : rejette ftp://, file://, etc.
    # avant tout appel sortant, quel que soit le payload fourni.
    if urlparse(url).scheme.lower() not in ('http', 'https'):
        return JsonResponse(
            {"error": "L'URL doit utiliser le schéma http ou https."}, status=400
        )

    method = method.upper()
    valid_methods = dict(ApiLog.METHOD_CHOICES)
    if method not in valid_methods:
        return JsonResponse(
            {"error": "La méthode doit être GET ou POST."}, status=400
        )

    # Provisoire : l'appel à l'API cible sera ajouté en partie 7.
    return JsonResponse({"message": "Validation OK", "method": method, "url": url})
````

## 6.3 Comprendre la vue, contrôle par contrôle

### 1. Seule la méthode POST est acceptée

`request.method` contient la méthode HTTP de la requête reçue. Si ce n'est pas POST, la vue répond avec `HttpResponseNotAllowed(['POST'])` : un statut **405** (*Method Not Allowed*) qui indique aussi la méthode autorisée. Ainsi, taper `/api/test/` dans la barre d'adresse du navigateur (une requête GET) ne déclenche aucun test.

### 2. Le corps est lu en JSON

`request.body` contient le corps **brut** de la requête, sous forme d'octets. `json.loads()` le transforme en dictionnaire Python. Les valeurs sont ensuite lues avec `data.get(...)`, qui renvoie `None` si une clé est absente, au lieu de provoquer une erreur comme `data['...']`.

> **Attention**
>
> N'utilisez **pas** `request.POST` ici : cet objet ne contient que les données d'un formulaire HTML classique (encodage `application/x-www-form-urlencoded`). Avec un corps JSON, `request.POST` est **vide**. Le cahier des charges impose `json.loads(request.body)`.

### 3. Les champs obligatoires

Si `method` ou `url` est absent ou vide, la vue répond immédiatement avec un statut 400 et un message. `JsonResponse` transforme le dictionnaire Python en JSON et ajoute l'en-tête `Content-Type: application/json`. Le paramètre `status=400` fixe le code de statut (200 par défaut).

### 4. Le schéma de l'URL

`urlparse()`, du module standard `urllib.parse`, découpe une URL en morceaux. Son attribut `scheme` contient le **schéma** : ce qui précède `://`. On n'accepte que `http` et `https` : toute autre valeur (`ftp`, `file`…) est refusée.

> **Pourquoi ?**
>
> C'est une mesure de **sécurité**. Le serveur exécute des requêtes vers des adresses fournies par l'utilisateur. Sans ce contrôle, quelqu'un pourrait lui demander d'utiliser d'autres protocoles, par exemple `file://` pour tenter de lire des fichiers du serveur. HTTP et HTTPS sont le même protocole (HTTPS y ajoute simplement le chiffrement) : ce sont les deux seuls dont l'application a besoin. Vous reviendrez sur ces risques en partie 13.

### 5. La méthode autorisée

La méthode est d'abord mise en majuscules (`.upper()`), pour accepter aussi `"get"`. Elle est ensuite comparée aux méthodes du modèle : `dict(ApiLog.METHOD_CHOICES)` transforme la liste de couples en dictionnaire `{'GET': 'GET', 'POST': 'POST'}`, et `in` vérifie la présence d'une clé. La liste des méthodes autorisées reste ainsi écrite **à un seul endroit**, dans le modèle.

C'est ici que la vue compense ce que vous avez constaté en partie 3 : la base de données ne vérifie pas les `choices`, donc c'est au code de le faire.

### 6. Une réponse provisoire

Si tous les contrôles passent, la vue renvoie pour l'instant un simple message de confirmation. Il sera remplacé par l'appel réel à l'API en partie 7. La variable `payload` est déjà lue, mais pas encore utilisée.

## 6.4 Déclarer la route

Ajoutez la nouvelle route dans `api_tester/urls.py` :

*api_tester/urls.py*
````
"""
Configuration des URL pour l'app api_tester.
"""
from django.urls import path

from . import views

urlpatterns = [
    path('', views.index_view, name='index'),
    path('api/test/', views.test_api_view, name='test_api'),
]
````

## 6.5 Vérifier la vue avec le client de test

Comment envoyer une requête POST en JSON sans avoir encore écrit le JavaScript ? Avec le **client de test** de Django, utilisable directement dans le shell. Il simule un navigateur et envoie des requêtes à votre application, sans passer par le réseau.

Ouvrez le shell Django (`python manage.py shell`) et préparez l'environnement de test :

*Shell Django*
````
from django.test.utils import setup_test_environment
setup_test_environment()
from django.test import Client
import json
c = Client()
````

> **À retenir**
>
> `setup_test_environment()` autorise le client de test à s'adresser à votre application (il se présente sous le nom d'hôte `testserver`). Le client désactive aussi la protection CSRF par défaut, ce qui permet de tester la vue seule, avant d'écrire le JavaScript qui transmettra le jeton.

Envoyez maintenant une série de requêtes. Pour chacune, `status_code` donne le statut renvoyé par la vue et `.json()` le corps de la réponse :

*Shell Django*
````
c.get('/api/test/').status_code

r = c.post('/api/test/', data=json.dumps({"url": "https://example.com/"}), content_type='application/json')
r.status_code, r.json()

r = c.post('/api/test/', data=json.dumps({"method": "GET", "url": "ftp://example.com/fichier"}), content_type='application/json')
r.status_code, r.json()

r = c.post('/api/test/', data=json.dumps({"method": "PATCH", "url": "https://example.com/"}), content_type='application/json')
r.status_code, r.json()

r = c.post('/api/test/', data=json.dumps({"method": "get", "url": "https://example.com/"}), content_type='application/json')
r.status_code, r.json()
````

*Sortie attendue*
````
Method Not Allowed: /api/test/
405
Bad Request: /api/test/
(400, {'error': "Les champs 'method' et 'url' sont requis."})
Bad Request: /api/test/
(400, {'error': "L'URL doit utiliser le schéma http ou https."})
Bad Request: /api/test/
(400, {'error': 'La méthode doit être GET ou POST.'})
(200, {'message': 'Validation OK', 'method': 'GET', 'url': 'https://example.com/'})
````

Les lignes `Method Not Allowed: ...` et `Bad Request: ...` ne sont pas des erreurs de votre code : c'est le **journal** de Django, qui signale chaque réponse 4xx. Vous les verrez aussi dans le terminal du serveur.

Le paramètre `content_type='application/json'` est important : il indique au serveur que le corps est du JSON, exactement comme le fera votre JavaScript. Quittez ensuite le shell avec `exit()`.

> **Point de vérification — fin de partie**
>
> Une requête GET renvoie **405**.
>
> Une URL manquante, un schéma `ftp://` et une méthode `PATCH` renvoient chacun **400** avec un message `error` explicite.
>
> Une demande valide renvoie **200**, avec la méthode convertie en majuscules (`get` → `GET`).
>
> Aucun test n'a été ajouté à l'historique : rechargez http://127.0.0.1:8000/, rien n'a changé.

## 6.6 Enregistrer votre travail

*PowerShell*
````
git add .
git commit -m "Vue test_api_view : validation des données reçues en JSON"
````

> **Commit — fin de la partie 6**
>
> Deux fichiers modifiés : `views.py` et `urls.py`.

## Pièges fréquents de la partie 6

| Symptôme | Cause probable | Solution |
| --- | --- | --- |
| `AttributeError: module 'api_tester.views' has no attribute 'test_api_view'` | Route ajoutée avant la vue, ou nom différent. | Vérifiez l'orthographe dans `views.py` et `urls.py`, puis enregistrez les deux fichiers. |
| Toutes les requêtes du shell renvoient `400`, précédées d'une longue trace d'erreur qui se termine par `DisallowedHost` | `setup_test_environment()` n'a pas été appelé : le nom d'hôte `testserver` est refusé. | Tapez les deux premières lignes de la section 6.5, puis recommencez. |
| `JSONDecodeError` | Le corps envoyé n'est pas du JSON (oubli de `json.dumps()` dans le shell). | Utilisez bien `data=json.dumps({...})` et `content_type='application/json'`. |
| La vue renvoie 400 « requis » alors que les champs sont présents | `request.POST` utilisé à la place de `json.loads(request.body)`. | Relisez la section 6.3, contrôle 2. |
| `NameError: name 'urlparse' is not defined` | Import oublié. | `from urllib.parse import urlparse` en haut de `views.py`. |

# Partie 7 — La vue de test : appel avec requests

La vue sait maintenant refuser les demandes invalides. Il est temps de lui faire exécuter le vrai test : **appeler l'API cible** avec la bibliothèque `requests`, mesurer le temps de réponse, **enregistrer** le test dans `ApiLog` et **renvoyer** le résultat en JSON. Au passage, vous allez d'abord étendre l'application aux méthodes **PUT** et **DELETE**, ce qui vous fera modifier un modèle existant.

> **Blocs de compétences**
>
> Compétences travaillées : **DWWM BC02** (développer des composants métier côté serveur, composants d'accès aux données) et **CDA BC01** et **BC02** (développer des composants métier, faire évoluer une base de données).

## 7.1 Ajouter PUT et DELETE au modèle

Un testeur d'API limité à GET et POST est vite frustrant : beaucoup d'API utilisent aussi **PUT** (remplacer une ressource) et **DELETE** (la supprimer). Ajoutez-les à la liste des méthodes du modèle, dans `api_tester/models.py` :

*api_tester/models.py (extrait à modifier)*
````
    METHOD_CHOICES = [
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('DELETE', 'DELETE'),
    ]
````

Modifier un modèle ne suffit jamais : comme vu en partie 3, il faut une **nouvelle migration** qui décrit ce changement. Générez-la puis appliquez-la :

*PowerShell*
````
python manage.py makemigrations api_tester
python manage.py migrate
````

*Sortie attendue (extraits)*
````
Migrations for 'api_tester':
  api_tester\migrations\0002_alter_apilog_method.py
    ~ Alter field method on apilog
...
  Applying api_tester.0002_alter_apilog_method... OK
````

Le symbole `~` signifie « modification d'un champ existant ». Django a nommé la migration d'après ce qu'elle fait : `alter_apilog_method`. Les données déjà enregistrées ne sont pas touchées.

> **À retenir**
>
> Pourquoi une migration, alors que la base ne vérifie pas les `choices` (partie 3) ? Parce que Django garde dans ses migrations une description **complète** de chaque modèle, `choices` compris. Si vous oubliez `makemigrations` après avoir modifié un modèle, l'application peut sembler fonctionner, mais ses migrations ne décrivent plus le modèle réel. La commande `python manage.py makemigrations --check` permet de détecter cet oubli : elle signale les changements qui n'ont pas encore de migration. Règle simple : **modèle modifié = nouvelle migration**, commitée avec le code.

Ajoutez aussi les deux méthodes à la liste déroulante du formulaire, dans `index.html` :

*api_tester/templates/api_tester/index.html (extrait à modifier)*
````
                        <select id="method" name="method" class="form-select">
                            <option value="GET">GET</option>
                            <option value="POST">POST</option>
                            <option value="PUT">PUT</option>
                            <option value="DELETE">DELETE</option>
                        </select>
````

## 7.2 La bibliothèque requests

`requests` est la bibliothèque Python de référence pour envoyer des requêtes HTTP. Vous l'avez installée en partie 2. Son usage tient en une ligne :

*Exemple*
````
response = requests.get("https://pokeapi.co/api/v2/pokemon/ditto", timeout=5)
````

Il existe une fonction par méthode : `requests.get()`, `requests.post()`, `requests.put()` et `requests.delete()`. L'objet `response` renvoyé contient tout ce dont vous avez besoin :

| Attribut ou méthode | Contenu |
| --- | --- |
| `response.status_code` | Le code de statut (200, 404…). |
| `response.elapsed` | Le temps écoulé entre l'envoi de la requête et l'arrivée de la réponse. `response.elapsed.total_seconds()` le donne **en secondes**. |
| `response.json()` | Le corps de la réponse converti en dictionnaire ou en liste Python. Provoque une erreur si le corps n'est pas du JSON. |
| `response.text` | Le corps de la réponse sous forme de texte brut. |
| `response.headers` | Les en-têtes de la réponse. |

> **Attention**
>
> Le paramètre `timeout=5` est **obligatoire** dans ce projet. Sans lui, `requests` attend une réponse **indéfiniment** : une API cible qui ne répond pas bloquerait le serveur Django. Avec `timeout=5`, `requests` abandonne au bout de 5 secondes. Vous traiterez cet abandon en partie 8.

## 7.3 Écrire l'appel

Voici le fichier `api_tester/views.py` complet à la fin de cette partie. Par rapport à la partie 6, il y a un nouvel import (`requests`), un message d'erreur mis à jour pour les méthodes, et la réponse provisoire a été remplacée par l'appel réel :

*api_tester/views.py*
````
import json
from urllib.parse import urlparse

import requests
from django.http import HttpResponseNotAllowed, JsonResponse
from django.shortcuts import render

from .models import ApiLog

# Création des views

def index_view(request):
    history = ApiLog.objects.order_by('-created_at')[:10]
    return render(request, 'api_tester/index.html', {"history": history})

def test_api_view(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    data = json.loads(request.body)
    method = data.get('method')
    url = data.get('url')
    payload = data.get('payload')

    if not method or not url:
        return JsonResponse(
            {"error": "Les champs 'method' et 'url' sont requis."}, status=400
        )

    # Schéma HTTP/HTTPS uniquement (CDC §3.2) : rejette ftp://, file://, etc.
    # avant tout appel sortant, quel que soit le payload fourni.
    if urlparse(url).scheme.lower() not in ('http', 'https'):
        return JsonResponse(
            {"error": "L'URL doit utiliser le schéma http ou https."}, status=400
        )

    method = method.upper()
    valid_methods = dict(ApiLog.METHOD_CHOICES)
    if method not in valid_methods:
        return JsonResponse(
            {"error": "La méthode doit être GET, POST, PUT ou DELETE."}, status=400
        )

    # GET/DELETE n'envoient normalement pas de corps : un payload fourni par erreur
    # pour ces méthodes est ignoré plutôt que de bloquer le test avec une 400.
    if method in ('POST', 'PUT') and payload is not None:
        request_kwargs = {"timeout": 5, "json": payload}
    else:
        payload = None
        request_kwargs = {"timeout": 5}

    dispatch = {
        'GET': requests.get,
        'POST': requests.post,
        'PUT': requests.put,
        'DELETE': requests.delete,
    }

    response = dispatch[method](url, **request_kwargs)

    try:
        response_body = response.json()
    except ValueError:
        # Réponse non-JSON : on renvoie le texte brut (signalé comme tel côté client).
        response_body = response.text

    ApiLog.objects.create(
        url=url,
        method=method,
        status_code=response.status_code,
        response_time=response.elapsed.total_seconds(),  # en secondes, cf. models.py
        payload_sent=payload,
        response_body=response_body,
    )

    return JsonResponse({
        "status_code": response.status_code,
        "response_time": response.elapsed.total_seconds() * 1000,  # en millisecondes
        "response_body": response_body,
    })
````

## 7.4 Comprendre l'appel, étape par étape

### Le payload, uniquement pour POST et PUT

Par convention, GET et DELETE n'envoient pas de corps. La vue prépare donc les paramètres de l'appel dans un dictionnaire, `request_kwargs` :

- pour **POST** ou **PUT** avec un payload : `timeout` et `json=payload`. Le paramètre `json` de `requests` convertit le dictionnaire en JSON et ajoute l'en-tête `Content-Type: application/json` ;
- dans **tous les autres cas** : `timeout` seulement. Un payload fourni avec GET ou DELETE est **ignoré** (et remis à `None`, pour ne pas l'enregistrer), plutôt que de refuser le test.

### Le dictionnaire de dispatch

Plutôt qu'une longue suite de `if method == 'GET': ... elif method == 'POST': ...`, la vue associe chaque méthode à la fonction `requests` correspondante dans un dictionnaire. En Python, une fonction est une valeur comme une autre : on peut la ranger dans un dictionnaire, puis l'appeler.

`dispatch[method]` récupère la bonne fonction, et `(url, **request_kwargs)` l'appelle. L'opérateur `**` **déplie** le dictionnaire en paramètres nommés. Pour un POST avec payload, la ligne équivaut donc à :

*Équivalent*
````
response = requests.post(url, timeout=5, json=payload)
````

> **Pourquoi ?**
>
> La validation de la partie 6 garantit que `method` est l'une des quatre clés du dictionnaire : `dispatch[method]` ne peut donc pas échouer. Ajouter une méthode plus tard reviendra à ajouter une ligne dans `METHOD_CHOICES` et une ligne dans `dispatch`.

### Le corps de la réponse : JSON ou texte

Toutes les API ne renvoient pas du JSON : une page web renvoie du HTML, certaines erreurs renvoient un corps vide. `response.json()` provoque alors une erreur de type `ValueError`. Le bloc `try` / `except` l'intercepte : si la conversion échoue, on garde le **texte brut** (`response.text`). La vue ne plante pas, et l'interface pourra signaler que la réponse n'est pas du JSON.

> **À retenir**
>
> Un `JSONField` accepte aussi une simple chaîne de caractères : le texte brut peut donc être enregistré tel quel dans `response_body`.

### L'enregistrement et la réponse : attention aux unités

Le test est enregistré avec `ApiLog.objects.create()`, puis le résultat est renvoyé au client avec `JsonResponse`. Relisez attentivement les deux lignes qui concernent le temps de réponse :

| Destination | Code | Unité |
| --- | --- | --- |
| La base de données | `response.elapsed.total_seconds()` | **Secondes** (convention du modèle) |
| La réponse JSON au client | `response.elapsed.total_seconds() * 1000` | **Millisecondes** (pour l'affichage) |

Le commentaire en fin de ligne rappelle l'unité à chaque fois : c'est le genre de précision qui évite les erreurs lors d'une future modification.

## 7.5 Vérifier avec de vraies API

Cette fois, la vue appelle réellement Internet. Ouvrez le shell Django et préparez le client de test comme en partie 6 :

*Shell Django*
````
from django.test.utils import setup_test_environment
setup_test_environment()
from django.test import Client
import json
from api_tester.models import ApiLog
c = Client()
````

### Un GET qui renvoie du JSON

*Shell Django*
````
r = c.post('/api/test/', data=json.dumps({"method": "GET", "url": "https://pokeapi.co/api/v2/pokemon/ditto"}), content_type='application/json')
r.status_code, r.json()["status_code"], r.json()["response_time"], r.json()["response_body"]["name"]
ApiLog.objects.first().response_time
````

*Sortie attendue (les temps varient)*
````
(200, 200, 412.337, 'ditto')
0.412337
````

Le **même** temps de réponse vaut `412.337` dans la réponse (millisecondes) et `0.412337` en base (secondes). La vue a bien appelé PokeAPI et enregistré le test. Le temps en millisecondes peut aussi s'afficher avec une longue suite de décimales, comme `401.99800000000005` : c'est une imprécision normale des calculs sur les nombres à virgule, sans conséquence.

### Un POST avec payload

*Shell Django*
````
r = c.post('/api/test/', data=json.dumps({"method": "POST", "url": "https://jsonplaceholder.typicode.com/posts", "payload": {"title": "Test", "userId": 1}}), content_type='application/json')
r.json()["status_code"], r.json()["response_body"]
ApiLog.objects.first().payload_sent
````

*Sortie attendue*
````
(201, {'title': 'Test', 'userId': 1, 'id': 101})
{'title': 'Test', 'userId': 1}
````

JSONPlaceholder est une API de démonstration : elle simule la création d'une ressource en renvoyant le payload reçu, complété d'un `id`. Le payload envoyé a bien été enregistré dans `payload_sent`.

### Une réponse qui n'est pas du JSON

*Shell Django*
````
r = c.post('/api/test/', data=json.dumps({"method": "GET", "url": "https://httpbin.org/html"}), content_type='application/json')
r.json()["status_code"], r.json()["response_body"][:15]
````

*Sortie attendue*
````
(200, '<!DOCTYPE html>')
````

La page HTML renvoyée par httpbin a été conservée en texte brut, sans erreur.

### Et si l'API ne répond pas ?

Faites un dernier essai, vers une adresse qui ne répond jamais. **Patientez 5 secondes** :

*Shell Django*
````
r = c.post('/api/test/', data=json.dumps({"method": "GET", "url": "http://10.255.255.1/"}), content_type='application/json')
````

Cette fois, un long message d'erreur s'affiche. Sa dernière ligne commence par `requests.exceptions.ConnectTimeout`. Dans un navigateur, cette erreur non gérée se traduirait par une **erreur 500** : la vue a « planté ». C'est exactement ce que vous allez corriger dans la partie 8. Quittez le shell avec `exit()`.

> **Point de vérification — fin de partie**
>
> `python manage.py showmigrations api_tester` affiche `[X] 0001_initial` et `[X] 0002_alter_apilog_method`.
>
> La liste « Méthode » de la page propose GET, POST, PUT et DELETE.
>
> Un GET vers PokeAPI renvoie un statut 200, un temps en **millisecondes**, et crée un test en base avec un temps en **secondes**.
>
> Un POST avec payload renvoie 201 et enregistre le payload dans `payload_sent`.
>
> Une page HTML est renvoyée en texte brut, sans erreur.
>
> L'historique de la page d'accueil affiche les nouveaux tests (rechargez-la).

> **À retenir**
>
> Si votre réseau bloque l'une de ces API (réseau d'entreprise, pare-feu), essayez avec une autre adresse de l'annexe, par exemple `https://jsonplaceholder.typicode.com/todos/1`.

## 7.6 Enregistrer votre travail

*PowerShell*
````
git add .
git commit -m "Appel de l'API cible avec requests, support de PUT/DELETE et enregistrement des tests"
````

> **Commit — fin de la partie 7**
>
> Le commit contient `models.py`, `views.py`, `index.html` **et** la nouvelle migration `0002_alter_apilog_method.py`.

## Pièges fréquents de la partie 7

| Symptôme | Cause probable | Solution |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'requests'` | Le venv n'est pas activé, ou `requests` n'a pas été installé. | Activez le venv, puis `python -m pip install -r requirements.txt`. |
| `makemigrations` affiche `No changes detected` | `models.py` n'a pas été enregistré. | Enregistrez le fichier (`Ctrl+S`) et relancez la commande. |
| PUT ou DELETE refusés avec « La méthode doit être… » | Les méthodes n'ont pas été ajoutées à `METHOD_CHOICES`. | La validation lit la liste du modèle : vérifiez la section 7.1. |
| Le temps en base vaut 412 au lieu de 0.412 | La multiplication par 1000 a été faite dans `create()` au lieu de `JsonResponse`. | Secondes en base, millisecondes dans la réponse : relisez la section 7.4. |
| `KeyError` sur `dispatch[method]` | Une méthode acceptée par la validation n'existe pas dans le dictionnaire. | Les clés de `dispatch` doivent correspondre exactement aux méthodes de `METHOD_CHOICES`. |
| `TypeError: Object of type ... is not JSON serializable` | Un objet non convertible en JSON a été placé dans la réponse (par exemple l'objet `response` lui-même). | Ne renvoyez que des valeurs simples : nombres, textes, listes, dictionnaires. |

# Partie 8 — Gérer les erreurs réseau

À la fin de la partie 7, un test vers une adresse qui ne répond pas faisait **planter** la vue. Or un testeur d'API sert justement à tester des API… qui ne fonctionnent pas toujours. Dans cette partie, vous rendez la vue **fiable** : quelle que soit l'erreur réseau, elle doit renvoyer une réponse JSON exploitable et **enregistrer le test** dans l'historique, avec un message explicite.

> **Blocs de compétences**
>
> Compétences travaillées : **DWWM BC02** (développer des composants métier côté serveur) et **CDA BC01** (développer des composants métier sécurisés et robustes).

## 8.1 Deux sortes d'échecs

Il faut bien distinguer deux situations, que `requests` traite très différemment :

| Situation | Exemple | Pour requests | Ce que fait la vue |
| --- | --- | --- | --- |
| L'API **a répondu**, avec un statut d'erreur | 404, 500 | Ce n'est **pas** une erreur : `response.status_code` vaut simplement 404 ou 500. | Rien de spécial : le statut est affiché tel quel (partie 7). |
| L'API **n'a pas répondu** du tout | Délai dépassé, serveur introuvable, URL malformée | Une **exception** est levée : l'exécution de la vue s'arrête. | Intercepter l'exception et renvoyer un message (cette partie). |

Les exceptions de `requests` sont organisées en **famille** : toutes héritent de `requests.exceptions.RequestException`. Vous allez en intercepter trois :

| Exception | Quand ? | Message renvoyé |
| --- | --- | --- |
| `Timeout` | L'API n'a pas répondu dans le délai de 5 secondes. | « La requête a expiré (timeout). » |
| `ConnectionError` | Connexion impossible : nom de domaine inexistant, serveur éteint, connexion refusée. | « Impossible de joindre l'hôte. » |
| `RequestException` | Toutes les autres erreurs de `requests` (par exemple une URL malformée). C'est le filet de sécurité. | « Erreur lors de l'appel à l'API : » suivi du détail |

## 8.2 Intercepter les exceptions

Dans `api_tester/views.py`, remplacez uniquement la ligne `response = dispatch[method](url, **request_kwargs)` par le bloc suivant. Le reste de la vue ne change pas :

*api_tester/views.py (bloc qui remplace l'appel)*
````
    try:
        response = dispatch[method](url, **request_kwargs)
    except requests.exceptions.Timeout:
        error_message = "La requête a expiré (timeout)."
        ApiLog.objects.create(
            url=url,
            method=method,
            status_code=None,
            response_time=None,
            error_message=error_message,
        )
        return JsonResponse({
            "status_code": None,
            "response_time": None,
            "error_message": error_message,
        })
    except requests.exceptions.ConnectionError:
        error_message = "Impossible de joindre l'hôte."
        ApiLog.objects.create(
            url=url,
            method=method,
            status_code=None,
            response_time=None,
            error_message=error_message,
        )
        return JsonResponse({
            "status_code": None,
            "response_time": None,
            "error_message": error_message,
        })
    except requests.exceptions.RequestException as exc:
        error_message = f"Erreur lors de l'appel à l'API : {exc}"
        ApiLog.objects.create(
            url=url,
            method=method,
            status_code=None,
            response_time=None,
            error_message=error_message,
        )
        return JsonResponse({
            "status_code": None,
            "response_time": None,
            "error_message": error_message,
        })
````

Veillez à l'**indentation** : le `try` est au même niveau que les autres instructions de la vue (4 espaces), et le contenu de chaque bloc est décalé de 4 espaces supplémentaires.

## 8.3 Comprendre les choix

### Chaque échec est enregistré

Dans chaque bloc `except`, un `ApiLog` est créé **avant** de répondre, avec `status_code` et `response_time` à `None` et un `error_message` explicite. C'est une exigence du cahier des charges : l'historique doit garder une **trace complète** de tous les tests, y compris ceux qui ont échoué. C'est pour cela que ces deux champs ont été déclarés `null=True` en partie 3.

Seules les demandes **invalides** (erreurs 400 de la partie 6) ne sont pas enregistrées : dans ce cas, aucun test n'a été exécuté.

### Une réponse 200, et non une erreur 500

Les trois blocs renvoient une réponse avec le statut **200**. Cela peut surprendre pour une erreur, mais c'est logique : **votre** endpoint a parfaitement fonctionné, il a exécuté le test et en rend compte. C'est l'**API cible** qui a échoué, et l'information est dans le contenu de la réponse (`status_code` à `null`, `error_message` renseigné). Le JavaScript de la partie 10 s'appuiera sur ce format.

> **À retenir**
>
> En JSON, la valeur Python `None` devient `null`. Le client recevra donc `{"status_code": null, "response_time": null, "error_message": "..."}`.

### L'ordre des blocs except compte

Python teste les blocs `except` **dans l'ordre** et exécute le premier qui correspond. Il faut donc aller du plus précis au plus général : `RequestException`, qui englobe toutes les autres, doit être en **dernier**. Placée en premier, elle intercepterait tout, et les messages précis ne s'afficheraient jamais.

> **Pourquoi ?**
>
> Un délai dépassé **pendant la connexion** lève `ConnectTimeout`, une exception qui hérite à la fois de `Timeout` et de `ConnectionError`. Comme `Timeout` est testée en premier, c'est le message « La requête a expiré (timeout). » qui s'affiche. Si vous inversiez les deux premiers blocs, le même test afficherait « Impossible de joindre l'hôte. ». Ce n'est pas faux, mais c'est moins précis.

> **Attention**
>
> N'utilisez jamais un `except:` seul, ou un `except Exception:` pour intercepter toutes les erreurs. Il masquerait aussi les **bugs de votre propre code** (une faute de frappe dans un nom de variable, par exemple), qui deviendraient invisibles. N'interceptez que les exceptions que vous savez traiter : ici, celles de `requests`.

## 8.4 Vérifier les trois cas d'erreur

Ouvrez le shell Django et préparez le client de test comme en partie 7 (les six mêmes lignes), puis essayez ces trois adresses. La première prend **5 secondes** :

*Shell Django*
````
r = c.post('/api/test/', data=json.dumps({"method": "GET", "url": "http://10.255.255.1/"}), content_type='application/json')
r.status_code, r.json()

r = c.post('/api/test/', data=json.dumps({"method": "GET", "url": "http://domaine-inexistant.test/"}), content_type='application/json')
r.status_code, r.json()

r = c.post('/api/test/', data=json.dumps({"method": "GET", "url": "http://"}), content_type='application/json')
r.status_code, r.json()
````

*Sortie attendue*
````
(200, {'status_code': None, 'response_time': None, 'error_message': 'La requête a expiré (timeout).'})
(200, {'status_code': None, 'response_time': None, 'error_message': "Impossible de joindre l'hôte."})
(200, {'status_code': None, 'response_time': None, 'error_message': "Erreur lors de l'appel à l'API : Invalid URL 'http://': No host supplied"})
````

| Adresse | Pourquoi elle échoue |
| --- | --- |
| `http://10.255.255.1/` | Une adresse IP privée qui n'existe sur aucun réseau : la connexion n'aboutit jamais, et le délai de 5 secondes est dépassé. |
| `http://domaine-inexistant.test/` | Le domaine `.test` est réservé aux essais et n'existe jamais : le nom ne peut pas être résolu. |
| `http://` | Le schéma est valide (il passe la validation de la partie 6), mais il n'y a pas de nom d'hôte : `requests` refuse l'URL. |

Vérifiez enfin que les trois échecs ont bien été enregistrés :

*Shell Django*
````
ApiLog.objects.all()[:3]
exit()
````

*Sortie attendue*
````
<QuerySet [<ApiLog: GET http:// [échec]>, <ApiLog: GET http://domaine-inexistant.test/ [échec]>, <ApiLog: GET http://10.255.255.1/ [échec]>]>
````

> **Point de vérification — fin de partie**
>
> Les trois requêtes renvoient un statut **200** (et non une page d'erreur 500), avec `status_code` et `response_time` à `None` et un `error_message` différent pour chaque cas.
>
> Les trois tests apparaissent dans la base avec la mention `[échec]`, et dans l'historique de la page avec un badge gris « Erreur ».
>
> Un test normal (par exemple vers PokeAPI) fonctionne toujours : pas de régression.

> **À retenir**
>
> Sur certains réseaux, `http://10.255.255.1/` échoue immédiatement au lieu d'attendre 5 secondes, avec le message « Impossible de joindre l'hôte. ». Cela dépend de la configuration de votre box ou de votre réseau. L'important est que la vue réponde en JSON, sans planter.

## 8.5 Enregistrer votre travail

*PowerShell*
````
git add .
git commit -m "Gestion des erreurs réseau (timeout, connexion, URL invalide)"
````

> **Commit — fin de la partie 8**
>
> La vue côté serveur est terminée. La suite se passe dans le navigateur, avec JavaScript.

## Pièges fréquents de la partie 8

| Symptôme | Cause probable | Solution |
| --- | --- | --- |
| Tous les échecs affichent « Erreur lors de l'appel à l'API » | `RequestException` est placée avant les autres blocs. | Elle doit être le **dernier** `except` (section 8.3). |
| `IndentationError: expected an indented block` | Contenu d'un bloc `try` ou `except` mal décalé. | Chaque niveau ajoute 4 espaces. Dans VS Code, sélectionnez des lignes puis `Tab` ou `Maj+Tab` pour les décaler. |
| Le test en échec n'apparaît pas dans l'historique | Le `ApiLog.objects.create(...)` manque dans l'un des blocs. | Chaque bloc `except` doit enregistrer le test **avant** son `return`. |
| `UnboundLocalError: ... 'response'` | Un bloc `except` ne se termine pas par un `return` : la vue continue et utilise `response`, qui n'existe pas. | Chaque bloc `except` doit se terminer par `return JsonResponse(...)`. |
| Le test vers `10.255.255.1` ne s'arrête jamais | Le paramètre `timeout=5` a disparu de `request_kwargs`. | Il doit être présent dans les **deux** branches du `if` / `else` (section 7.3). |

# Partie 9 — JavaScript : fetch et CSRF

Le serveur est prêt : il sait valider une demande, appeler l'API cible, enregistrer le test et renvoyer le résultat en JSON. Il reste à relier la page à ce serveur. Dans cette partie, vous écrivez le premier script JavaScript de l'application. Il **intercepte** l'envoi du formulaire, construit un corps **JSON**, y joint le **jeton CSRF** et envoie la demande à `/api/test/` avec `fetch`, **sans recharger la page**. Pour l'instant, le résultat s'affiche seulement dans la console du navigateur : la mise en forme viendra en partie 10.

> **Blocs de compétences**
>
> Compétences travaillées : **DWWM BC01** (développer la partie dynamique des interfaces utilisateur) et **CDA BC01** (développer des interfaces utilisateur, sécuriser les échanges).

## 9.1 Brancher un fichier JavaScript sur la page

Le code JavaScript sera écrit dans un fichier séparé, `main.js`, rangé dans le dossier `static/` préparé en partie 2. Les fichiers **statiques** (JavaScript, CSS, images) sont envoyés tels quels au navigateur, sans passer par une vue.

Créez le fichier `api_tester/static/api_tester/js/main.js`. Laissez-le vide pour l'instant. Vous pouvez supprimer le `.gitkeep` du dossier `js/`, qui n'est plus vide.

Modifiez ensuite `index.html` à deux endroits. Tout en haut du fichier, **avant** `<!DOCTYPE html>`, ajoutez :

*api_tester/templates/api_tester/index.html (début du fichier)*
````
{% load static %}
<!DOCTYPE html>
````

Tout en bas, **après** le script de Bootstrap et avant `</body>`, ajoutez la ligne qui charge votre script :

*api_tester/templates/api_tester/index.html (fin du fichier)*
````
<script
    src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"
></script>
<script src="{% static 'api_tester/js/main.js' %}"></script>
</body>
</html>
````

`{% load static %}` active la balise `{% static %}` dans ce template. `{% static 'api_tester/js/main.js' %}` produit l'adresse publique du fichier : `/static/api_tester/js/main.js`. En mode développement, `runserver` sert ces fichiers automatiquement : Django les cherche dans le dossier `static/` de chaque application déclarée dans `INSTALLED_APPS`. Aucun réglage supplémentaire n'est nécessaire.

> **Pourquoi ?**
>
> Pourquoi placer le script **en bas** de la page ? Parce que le navigateur lit le HTML de haut en bas. Un script placé dans le `<head>` s'exécuterait avant que le formulaire existe, et `document.getElementById('test-form')` renverrait `null`. En bas de page, tous les éléments sont déjà créés quand le script démarre.

## 9.2 Le jeton CSRF : pourquoi et comment

Une attaque **CSRF** (*Cross-Site Request Forgery*, falsification de requête intersite) consiste à piéger un utilisateur. Un autre site, qu'il visite par exemple, envoie à son insu une requête vers votre application. Le navigateur y joint automatiquement les cookies de l'utilisateur, et l'application croit que la demande vient de lui.

Django s'en protège par défaut. Chaque requête POST doit contenir un **jeton secret**, que seule une page de votre application peut connaître. Un site malveillant ne peut pas lire ce jeton, donc ses requêtes sont refusées avec le statut **403**.

Avec un formulaire HTML classique, le jeton voyage tout seul, dans le champ caché créé par `{% csrf_token %}`. Mais vous allez envoyer du **JSON** avec `fetch` : le champ caché ne sera pas transmis. Il faut donc :

1. **lire** le jeton dans le champ caché de la page : `document.querySelector('[name=csrfmiddlewaretoken]').value` ;
2. l'**envoyer** dans un en-tête HTTP nommé `X-CSRFToken`, que Django sait lire.

> **Attention**
>
> Ne désactivez **jamais** la protection avec le décorateur `@csrf_exempt` pour « faire marcher » un appel `fetch`. C'est une erreur fréquente, et elle est **interdite** par le cahier des charges : elle ouvrirait précisément la faille que Django bloque. La bonne solution est toujours de transmettre le jeton.

## 9.3 Le premier script

Écrivez ce code dans `main.js` :

*api_tester/static/api_tester/js/main.js*
````
const form = document.getElementById('test-form');

form.addEventListener('submit', function (event) {
    event.preventDefault();

    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const method = document.getElementById('method').value;
    const url = document.getElementById('url').value;
    const payloadText = document.getElementById('payload').value.trim();

    // Le payload JSON est parsé côté client avant tout envoi réseau : une erreur de
    // saisie est purement locale, inutile de solliciter le serveur pour la détecter.
    let payload;
    if (payloadText) {
        try {
            payload = JSON.parse(payloadText);
        } catch (error) {
            console.error('Le payload JSON saisi est invalide : ' + error.message);
            return;
        }
    }

    const requestBody = { method: method, url: url };
    if (payload !== undefined) {
        requestBody.payload = payload;
    }

    const body = JSON.stringify(requestBody);

    fetch('/api/test/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
        },
        body: body,
    })
        .then(function (response) {
            return response.json();
        })
        .then(function (data) {
            console.log(data);
        })
        .catch(function (error) {
            console.error(error);
        });
});
````

## 9.4 Comprendre le script

### Intercepter l'envoi du formulaire

`addEventListener('submit', ...)` exécute la fonction à chaque envoi du formulaire, que ce soit par un clic sur « Tester » ou par la touche Entrée. La fonction reçoit un objet `event`, et `event.preventDefault()` **annule le comportement par défaut** : le navigateur n'envoie plus le formulaire et ne recharge plus la page. C'est désormais votre code qui décide quoi faire.

### Lire les champs

Le jeton CSRF est lu dans le champ caché de `{% csrf_token %}`, grâce à son attribut `name`. Les trois champs du formulaire sont lus grâce à leur `id`. La méthode `.trim()` retire les espaces et retours à la ligne en début et en fin de payload : un champ qui ne contient que des espaces est considéré comme vide.

### Vérifier le payload avant l'envoi

Si un payload a été saisi, `JSON.parse()` le convertit en objet JavaScript. Si le texte n'est pas du JSON valide (une virgule en trop, des guillemets simples au lieu de doubles…), `JSON.parse()` lève une erreur. Le bloc `try` / `catch` l'intercepte, affiche un message et **arrête la fonction** avec `return`, **avant** tout appel au serveur. Inutile d'envoyer une demande dont on sait déjà qu'elle est invalide.

### Construire le corps JSON

`requestBody` est un objet JavaScript qui reprend le **contrat** défini en partie 6 : `method`, `url`, et `payload` seulement s'il a été saisi. `JSON.stringify()` le transforme en texte JSON, prêt à être envoyé.

### Envoyer avec fetch

`fetch()` envoie une requête HTTP depuis le navigateur. Son deuxième paramètre décrit la requête :

| Option | Valeur | Rôle |
| --- | --- | --- |
| `method` | `'POST'` | La seule méthode acceptée par `/api/test/`. |
| `Content-Type` | `'application/json'` | Annonce au serveur que le corps est du JSON. C'est ce que vérifiait `content_type` dans le shell. |
| `X-CSRFToken` | le jeton lu dans la page | La preuve que la demande vient bien de votre page. |
| `body` | le texte JSON | Le contenu de la demande. |

### Attendre la réponse : les promesses

Une requête réseau prend du temps. `fetch()` ne bloque pas la page en attendant : il renvoie immédiatement une **promesse**, un objet qui représente un résultat à venir. On enchaîne ensuite des fonctions avec `.then()`, exécutées quand le résultat arrive :

1. le premier `.then()` reçoit la réponse HTTP et lit son corps en JSON avec `response.json()`, qui renvoie lui-même une promesse ;
2. le second `.then()` reçoit les données converties en objet, et les affiche dans la console ;
3. `.catch()` s'exécute si quelque chose échoue en chemin, par exemple si le serveur Django est arrêté.

> **À retenir**
>
> Remarquez que `fetch` **ne considère pas** une réponse 400 ou 500 comme un échec : le premier `.then()` s'exécute quand même. `.catch()` ne se déclenche que si la requête n'a pas pu aboutir du tout. Vous en tiendrez compte en partie 10.

## 9.5 Vérifier dans les outils de développement

Rechargez la page avec **`Ctrl+F5`**. Ce rechargement forcé oblige le navigateur à télécharger la nouvelle version de `main.js`, au lieu d'utiliser une ancienne copie gardée en cache. Ouvrez ensuite les **outils de développement** avec `F12`.

### La console

Ouvrez l'onglet **Console**, puis faites un test : `GET` sur `https://pokeapi.co/api/v2/pokemon/ditto`. La page **ne se recharge pas**, et après un instant, la console affiche un objet : `{status_code: 200, response_time: ..., response_body: {...}}`. Cliquez sur la petite flèche pour le déplier.

Essayez aussi un payload invalide, par exemple `{title: Test}` (sans guillemets) : la console affiche « Le payload JSON saisi est invalide », et aucune requête n'est envoyée.

### L'onglet Réseau

Ouvrez l'onglet **Réseau** (*Network*) et, s'il existe, activez le filtre **XHR** ou **Fetch/XHR** pour ne garder que les appels JavaScript. Faites un test **POST** sur `https://jsonplaceholder.typicode.com/posts`, avec le payload `{"title": "Test", "userId": 1}`. Une ligne `test/` apparaît : cliquez dessus.

Dans l'onglet **En-têtes**, le résumé montre la méthode **POST**, l'adresse `/api/test/` et le statut **200** :

*[Figure : fig-devtools-etat.png] Le résumé de la requête envoyée par `fetch` (ici dans Firefox) : méthode POST vers `/api/test/`, statut 200.*

Plus bas, la section **En-têtes de la requête** liste tout ce que le navigateur a envoyé. Si un bouton **Brut** est proposé, activez-le pour afficher les en-têtes ligne par ligne :

*[Figure : fig-devtools-entetes.png] Les en-têtes de la requête : on y trouve `Content-Type: application/json` et `X-CSRFToken`, ajoutés par votre script, ainsi que le cookie `csrftoken` joint automatiquement par le navigateur.*

> **Pourquoi ?**
>
> Le jeton de l'en-tête `X-CSRFToken` et celui du cookie `csrftoken` n'ont **pas la même valeur**. C'est normal. Django « masque » le jeton différemment à chaque affichage de la page, pour qu'il ne soit jamais identique d'une fois sur l'autre. Il sait ensuite vérifier que les deux valeurs correspondent au même secret. Si le jeton manque ou ne correspond pas, la requête est refusée avec le statut 403.

Enfin, l'onglet **Requête** (*Payload* dans Chrome et Edge) affiche le corps JSON envoyé :

*[Figure : fig-devtools-payload.png] Le corps de la requête : un objet JSON avec `method`, `url` et le `payload` imbriqué, exactement le contrat de l'endpoint.*

> **Point de vérification — fin de partie**
>
> Un clic sur « Tester » **ne recharge pas** la page, et le résultat du test s'affiche dans la console.
>
> Dans l'onglet Réseau, la requête `test/` utilise la méthode **POST**, porte les en-têtes `Content-Type: application/json` et `X-CSRFToken`, et son corps est du JSON.
>
> Un payload invalide est signalé dans la console, sans qu'aucune requête parte vers le serveur.
>
> Après un rechargement de la page (`F5`), les tests effectués apparaissent dans l'historique : ils ont bien été enregistrés.

## 9.6 Enregistrer votre travail

*PowerShell*
````
git add .
git commit -m "Envoi du formulaire en JSON avec fetch et jeton CSRF"
````

> **Commit — fin de la partie 9**
>
> Le commit contient le nouveau fichier `main.js` et les deux modifications de `index.html`.

## Pièges fréquents de la partie 9

| Symptôme | Cause probable | Solution |
| --- | --- | --- |
| La page se recharge quand on clique sur « Tester » | Le script n'est pas chargé, ou `preventDefault()` est absent. | Regardez l'onglet Console : une erreur rouge indique souvent la cause. Vérifiez la balise `<script>` et l'appel à `event.preventDefault()`. |
| `GET /static/api_tester/js/main.js 404` dans le terminal du serveur | Le fichier n'est pas au bon endroit. | Le chemin complet doit être `api_tester/static/api_tester/js/main.js`. Redémarrez `runserver` après avoir créé un nouveau dossier `static`. |
| `TemplateSyntaxError: Invalid block tag ... 'static'` | `{% load static %}` est absent ou mal placé. | Ajoutez-le en toute première ligne de `index.html`. |
| Le serveur répond **403 Forbidden** | Le jeton CSRF n'est pas transmis, ou l'en-tête est mal nommé. | L'en-tête doit s'appeler exactement `X-CSRFToken`. Vérifiez aussi que `{% csrf_token %}` est bien dans le formulaire. |
| Vos modifications de `main.js` ne sont pas prises en compte | Le navigateur utilise une ancienne version en cache. | Rechargez avec `Ctrl+F5`. |
| Rien ne se passe au clic sur « Tester », et une bulle « Veuillez saisir une URL » apparaît | L'URL a été saisie sans `https://` (par exemple `pokeapi.co/...`). Le champ étant de type `url`, le **navigateur** bloque l'envoi avant même que JavaScript s'exécute. | Saisissez toujours l'adresse complète, schéma compris : `https://pokeapi.co/...`. |
| `TypeError: Cannot read properties of null` | Un `id` du script ne correspond à aucun élément de la page. | Comparez les `id` du script (`test-form`, `method`, `url`, `payload`) avec ceux de `index.html`. |

# Partie 10 — Afficher le résultat

Le résultat de chaque test arrive maintenant dans le navigateur, mais seulement dans la console. Dans cette partie, vous l'affichez **dans la page**, dans le panneau `#result-panel` : un badge de statut coloré, le temps de réponse et le corps de la réponse **formaté**. Vous traitez aussi tous les cas particuliers : erreur réseau, réponse qui n'est pas du JSON, demande invalide (400) et serveur Django injoignable.

> **Blocs de compétences**
>
> Compétences travaillées : **DWWM BC01** (développer la partie dynamique des interfaces utilisateur) et **CDA BC01** (développer des interfaces utilisateur sécurisées).

## 10.1 Les quatre formes de réponse

Avant d'écrire le code, recensez tout ce que le script peut recevoir. Chaque forme demande un affichage différent :

| Situation | Ce que reçoit le script | Affichage |
| --- | --- | --- |
| Test réussi (l'API a répondu) | Statut **200**, `{status_code: 404, response_time: 762.9, response_body: ...}` | Badge du statut, temps en ms, corps formaté. |
| Erreur réseau (partie 8) | Statut **200**, `{status_code: null, response_time: null, error_message: "..."}` | Badge gris « Erreur » et le message. |
| Demande invalide (partie 6) | Statut **400**, `{error: "..."}` | « Formulaire invalide » et le message. |
| Serveur Django injoignable | Rien : `fetch` échoue et `.catch()` s'exécute. | Badge « Erreur » et un message générique. |

Le statut de la réponse **HTTP** (200 ou 400) permet de distinguer une demande invalide d'un test réellement exécuté. Il faut donc le mémoriser dans le premier `.then()`, car le second ne reçoit que les données.

## 10.2 Le script complet de cette étape

Voici le contenu complet de `main.js` à la fin de cette partie. Il ajoute quatre fonctions d'affichage **au-dessus** de l'écouteur `submit`, et remplace les `console.log` / `console.error` par des appels à ces fonctions. Remplacez tout le contenu du fichier :

*api_tester/static/api_tester/js/main.js*
````
const form = document.getElementById('test-form');

// Construit le badge Bootstrap correspondant au status_code renvoyé par le serveur.
// Schéma unifié avec les cartes server-rendues dans index.html :
// vert (2xx), jaune (4xx, la cible a répondu mais signale une erreur client),
// rouge (5xx, erreur côté serveur cible), gris "Erreur" (null, pas de réponse reçue).
function createStatusBadge(statusCode) {
    const badge = document.createElement('span');
    badge.classList.add('badge');

    if (statusCode === null || statusCode === undefined) {
        badge.classList.add('bg-secondary');
        badge.textContent = 'Erreur';
    } else if (statusCode >= 200 && statusCode < 300) {
        badge.classList.add('bg-success');
        badge.textContent = String(statusCode);
    } else if (statusCode >= 400 && statusCode < 500) {
        badge.classList.add('bg-warning', 'text-dark');
        badge.textContent = String(statusCode);
    } else if (statusCode >= 500 && statusCode < 600) {
        badge.classList.add('bg-danger');
        badge.textContent = String(statusCode);
    } else {
        badge.classList.add('bg-secondary');
        badge.textContent = String(statusCode);
    }

    return badge;
}

// Affiche le résultat d'un test dans #result-panel. Construit les éléments via
// createElement/textContent (pas d'innerHTML) pour éviter tout risque d'injection.
function displayResult(data) {
    const panel = document.getElementById('result-panel');
    panel.textContent = '';

    const cardBody = document.createElement('div');
    cardBody.classList.add('card-body');

    const header = document.createElement('div');
    header.classList.add('d-flex', 'align-items-center', 'gap-2', 'mb-2');
    header.appendChild(createStatusBadge(data.status_code));

    if (data.response_time !== null && data.response_time !== undefined) {
        const responseTime = document.createElement('span');
        responseTime.classList.add('text-muted');
        responseTime.textContent = `${data.response_time} ms`;
        header.appendChild(responseTime);
    }

    cardBody.appendChild(header);

    if (data.error_message) {
        // Cas d'erreur réseau (timeout/connexion) : pas de corps JSON, juste le message.
        const errorText = document.createElement('p');
        errorText.classList.add('card-text', 'mb-0');
        errorText.textContent = data.error_message;
        cardBody.appendChild(errorText);
    } else {
        if (typeof data.response_body === 'string') {
            // CDC 2.2 : signaler explicitement l'absence de JSON exploitable.
            const notice = document.createElement('p');
            notice.classList.add('card-text', 'text-muted', 'mb-1');
            notice.textContent = 'Réponse non-JSON (texte brut) :';
            cardBody.appendChild(notice);
        }

        const pre = document.createElement('pre');
        pre.classList.add('mb-0');
        pre.textContent = typeof data.response_body === 'string'
            ? data.response_body
            : JSON.stringify(data.response_body, null, 2);
        cardBody.appendChild(pre);
    }

    panel.appendChild(cardBody);
}

// Affiche une erreur de validation (400, method/url manquants) dans #result-panel.
// Format de réponse différent du cas nominal/erreur réseau (cf. test_api_view :
// { "error": "..." }) : requête mal formée vers notre propre endpoint, pas un test
// exécuté, donc aucun ApiLog n'a été créé côté serveur.
function displayValidationError(message) {
    const panel = document.getElementById('result-panel');
    panel.textContent = '';

    const cardBody = document.createElement('div');
    cardBody.classList.add('card-body');

    const title = document.createElement('p');
    title.classList.add('card-text', 'fw-bold', 'mb-1');
    title.textContent = 'Formulaire invalide';
    cardBody.appendChild(title);

    const errorText = document.createElement('p');
    errorText.classList.add('card-text', 'mb-0');
    errorText.textContent = message;
    cardBody.appendChild(errorText);

    panel.appendChild(cardBody);
}

// Affiche un message simple dans #result-panel quand le fetch lui-même échoue
// (requête qui n'aboutit même pas, ex. serveur injoignable).
function displayFetchError(message) {
    const panel = document.getElementById('result-panel');
    panel.textContent = '';

    const cardBody = document.createElement('div');
    cardBody.classList.add('card-body');
    cardBody.appendChild(createStatusBadge(null));

    const errorText = document.createElement('p');
    errorText.classList.add('card-text', 'mb-0');
    errorText.textContent = message;
    cardBody.appendChild(errorText);

    panel.appendChild(cardBody);
}

form.addEventListener('submit', function (event) {
    event.preventDefault();

    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const method = document.getElementById('method').value;
    const url = document.getElementById('url').value;
    const payloadText = document.getElementById('payload').value.trim();

    // Le payload JSON est parsé côté client avant tout envoi réseau : une erreur de
    // saisie est purement locale, inutile de solliciter le serveur pour la détecter.
    let payload;
    if (payloadText) {
        try {
            payload = JSON.parse(payloadText);
        } catch (error) {
            displayValidationError('Le payload JSON saisi est invalide : ' + error.message);
            return;
        }
    }

    const requestBody = { method: method, url: url };
    if (payload !== undefined) {
        requestBody.payload = payload;
    }

    const body = JSON.stringify(requestBody);

    // Capturé pour distinguer, dans le .then suivant, un test réellement exécuté
    // (200, ApiLog créé) d'une simple erreur de validation (400, aucun ApiLog).
    let responseStatus = null;

    fetch('/api/test/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
        },
        body: body,
    })
        .then(function (response) {
            responseStatus = response.status;
            return response.json();
        })
        .then(function (data) {
            // Un 400 (method/url manquants) a un format de réponse différent
            // ({ "error": "..." }) et n'a déclenché aucun appel réseau côté serveur,
            // donc aucun ApiLog : traitement dédié, pas de carte d'historique.
            if (responseStatus === 400) {
                displayValidationError(data.error);
                return;
            }

            displayResult(data);
        })
        .catch(function (error) {
            console.error(error);
            displayFetchError('La requête vers le serveur a échoué.');
        });
});
````

## 10.3 Comprendre les fonctions d'affichage

### createStatusBadge : un badge, deux affichages identiques

Cette fonction fabrique le badge de statut **avec exactement les mêmes règles de couleur** que le template de la partie 5 : vert, jaune, rouge, ou gris « Erreur » quand le statut est `null`. Un même statut aura donc la même couleur, que la carte ait été créée par Django ou par JavaScript. La fonction est écrite **une seule fois** et réutilisée partout : dans le panneau de résultat, dans `displayFetchError`, et bientôt dans l'historique.

`document.createElement('span')` crée une balise en mémoire. `classList.add()` lui ajoute des classes CSS. `textContent` définit son texte. La fonction **renvoie** la balise : c'est l'appelant qui décide où l'insérer.

### displayResult : construire le panneau élément par élément

La fonction commence par vider le panneau (`panel.textContent = ''` supprime tout son contenu), puis reconstruit une carte : l'en-tête avec le badge et le temps, puis le corps de la réponse. Chaque élément est ajouté à son parent avec `appendChild()`.

- S'il y a un `error_message`, c'est une **erreur réseau** : on affiche simplement le message.
- Sinon, on affiche le corps. Si c'est un **objet** (du JSON), `JSON.stringify(data.response_body, null, 2)` le transforme en texte **indenté de 2 espaces**, bien plus lisible. Si c'est déjà une **chaîne** (réponse non-JSON), on l'affiche telle quelle, précédée d'une mention explicite.
- La balise `<pre>` conserve les espaces et les retours à la ligne, indispensables pour lire du JSON indenté.

> **Attention**
>
> Pourquoi tant de `createElement` et de `textContent`, alors qu'une seule ligne `panel.innerHTML = '<span class="badge">' + ... + '</span>'` suffirait ? Pour la **sécurité**. Le corps de la réponse vient d'une API **que vous ne contrôlez pas**. Il peut contenir du HTML, voire du code malveillant comme `<img src=x onerror="alert(document.cookie)">`. Avec `innerHTML`, le navigateur interpréterait ce code : c'est une faille **XSS**. Avec `textContent`, tout est affiché comme du **texte**, sans jamais être exécuté. Règle à retenir : **jamais d'`innerHTML` avec des données venues de l'extérieur**.

### displayValidationError et displayFetchError

`displayValidationError` affiche « Formulaire invalide » suivi du message. Elle sert dans deux cas : une réponse **400** du serveur, et un payload qui n'est pas du JSON valide, détecté avant l'envoi. `displayFetchError` couvre le dernier cas, celui où la requête n'a pas abouti du tout. Ainsi, l'utilisateur a **toujours** un retour visuel.

### La mémorisation du statut HTTP

La variable `responseStatus` est déclarée **avant** `fetch`. Le premier `.then()` y range `response.status`, et le second s'en sert pour aiguiller l'affichage : une réponse 400 va vers `displayValidationError`, tout le reste vers `displayResult`. Une variable déclarée à l'extérieur des deux fonctions est accessible depuis les deux.

## 10.4 Vérifier tous les cas

Rechargez la page avec `Ctrl+F5`, puis testez successivement les adresses ci-dessous. Pour chacune, le panneau de résultat doit ressembler à la figure correspondante.

### Un test réussi

`GET` `https://pokeapi.co/api/v2/pokemon/pikachu` : badge vert, temps de réponse et JSON indenté.

*[Figure : fig-resultat-200.png] Un test réussi : badge vert 200, temps de réponse en millisecondes et corps JSON indenté.*

### Un POST avec payload

`POST` `https://jsonplaceholder.typicode.com/posts`. Le payload est facultatif : sans payload, JSONPlaceholder renvoie seulement l'`id` de la ressource « créée ».

*[Figure : fig-resultat-post-201.png] Un POST : badge vert 201 (*Created*) et la réponse de l'API.*

### Une erreur 404 et une erreur 500

`GET` `https://httpbin.org/status/404`, puis `GET` `https://httpbin.org/status/500`. httpbin renvoie ces statuts avec un corps **vide**.

*[Figure : fig-resultat-404.png] Une erreur 404 : badge jaune. L'API a bien répondu, mais signale que la ressource n'existe pas.*

*[Figure : fig-resultat-500.png] Une erreur 500 : badge rouge. L'API a répondu, mais a rencontré une erreur de son côté.*

> **À retenir**
>
> Sous le badge, la mention « Réponse non-JSON (texte brut) : » apparaît, suivie de… rien. C'est logique : un corps vide n'est pas du JSON valide, donc la vue l'a conservé en texte (une chaîne vide), et le script le signale comme tel.

### Une réponse non-JSON

`GET` `https://httpbin.org/html` : une page HTML, affichée en texte brut et **non interprétée** par le navigateur, grâce à `textContent`.

*[Figure : fig-resultat-non-json.png] Une réponse HTML : la mention « Réponse non-JSON » puis le code HTML affiché comme du texte.*

> **À retenir**
>
> Le temps affiché peut comporter une longue suite de décimales, comme `1235.2479999999998 ms`. Ce n'est pas une erreur de votre code : c'est l'imprécision normale des calculs sur les nombres à virgule, déjà rencontrée en partie 7. Le temps affiché dans l'historique, lui, est arrondi par `widthratio`.

### Une erreur réseau

`GET` `http://10.255.255.1` : après 5 secondes, un badge gris et le message de timeout.

*[Figure : fig-resultat-timeout.png] Un timeout : badge gris « Erreur » et le message renvoyé par la vue.*

### Une demande invalide

`GET` avec l'URL `ftp://example.com/fichier` : le navigateur accepte cette adresse, mais le serveur la refuse (partie 6). Essayez aussi un payload invalide, comme `{title: Test}` : le message s'affiche **sans** qu'aucune requête parte vers le serveur.

*[Figure : fig-resultat-validation.png] Une demande refusée par la validation du serveur : « Formulaire invalide » et le message d'erreur.*

### Le serveur Django arrêté

Enfin, arrêtez `runserver` (`Ctrl+C`) **sans recharger la page**, et cliquez sur « Tester » : le panneau affiche « La requête vers le serveur a échoué. ». Relancez ensuite le serveur.

> **Point de vérification — fin de partie**
>
> Chaque cas affiche le bon badge : vert (2xx), jaune (4xx), rouge (5xx) ou gris « Erreur ».
>
> Le JSON est indenté, et une réponse HTML est affichée en texte brut, sans être interprétée.
>
> Une demande invalide affiche « Formulaire invalide », et un payload mal formé est détecté sans appel au serveur.
>
> Serveur arrêté : un message d'échec s'affiche, la page ne reste jamais sans réponse.
>
> Après un rechargement, les tests exécutés apparaissent dans l'historique, mais **pas** les demandes invalides.

## 10.5 Enregistrer votre travail

*PowerShell*
````
git add .
git commit -m "Affichage du résultat : badges, JSON formaté et cas d'erreur"
````

> **Commit — fin de la partie 10**
>
> Seul `main.js` a changé.

## Pièges fréquents de la partie 10

| Symptôme | Cause probable | Solution |
| --- | --- | --- |
| Le JSON s'affiche sur une seule ligne | Le troisième paramètre de `JSON.stringify` manque, ou le texte est placé dans un `<p>` au lieu d'un `<pre>`. | `JSON.stringify(data.response_body, null, 2)` dans une balise `<pre>`. |
| Le panneau affiche `[object Object]` | L'objet a été placé directement dans `textContent`, sans `JSON.stringify`. | Convertissez l'objet en texte avec `JSON.stringify` avant de l'afficher. |
| Les anciens résultats s'empilent dans le panneau | Le panneau n'est pas vidé avant l'affichage. | `panel.textContent = ''` en début de chaque fonction d'affichage. |
| Une demande invalide affiche un badge et `undefined` | Le cas 400 n'est pas aiguillé vers `displayValidationError`. | Vérifiez `responseStatus = response.status` dans le premier `.then()` et le test `responseStatus === 400`. |
| `ReferenceError: displayResult is not defined` | Faute de frappe dans le nom d'une fonction. | Comparez les noms à l'appel et à la déclaration (majuscules comprises). |

# Partie 11 — L'historique dynamique

Dernière étape de l'interface. Après chaque test, l'historique de droite doit se **mettre à jour tout seul**, sans recharger la page : une nouvelle carte apparaît en haut, et la liste ne dépasse jamais **10 cartes**. Un clic sur une carte doit aussi **pré-remplir le formulaire** avec la méthode et l'URL du test, pour le relancer rapidement. Ce sont les exigences de la section 5 du cahier des charges.

> **Blocs de compétences**
>
> Compétences travaillées : **DWWM BC01** (développer la partie dynamique des interfaces utilisateur) et **CDA BC01** (développer des interfaces utilisateur).

## 11.1 Fabriquer une carte d'historique en JavaScript

Les cartes affichées au chargement de la page sont générées par Django (partie 5). Celles ajoutées après un test seront fabriquées par JavaScript. Pour que l'utilisateur ne voie aucune différence, la carte JavaScript doit avoir **exactement la même structure** et les **mêmes classes** que la carte du template.

Dans `main.js`, ajoutez cette fonction **juste après** `displayValidationError` :

*api_tester/static/api_tester/js/main.js (fonction à ajouter)*
````
// Construit une carte d'historique identique (structure/classes) à celles déjà
// rendues côté serveur dans index.html. `data` est la réponse JSON de test_api_view
// (nominal ou erreur réseau) ; method/url viennent du formulaire, connus du client.
function createHistoryCard(method, url, data) {
    const card = document.createElement('div');
    card.classList.add('card');
    card.dataset.method = method;
    card.dataset.url = url;

    const cardBody = document.createElement('div');
    cardBody.classList.add('card-body');

    const header = document.createElement('div');
    header.classList.add('d-flex', 'justify-content-between', 'align-items-center', 'mb-2');

    const methodBadge = document.createElement('span');
    methodBadge.classList.add('badge', 'bg-secondary');
    methodBadge.textContent = method;
    header.appendChild(methodBadge);

    header.appendChild(createStatusBadge(data.status_code));

    cardBody.appendChild(header);

    const urlText = document.createElement('p');
    urlText.classList.add('card-text', 'text-break', 'mb-1');
    urlText.textContent = url;
    cardBody.appendChild(urlText);

    const meta = document.createElement('p');
    meta.classList.add('card-text', 'mb-0');
    const small = document.createElement('small');
    small.classList.add('text-muted');
    // Le serveur ne renvoie pas de date dans la réponse JSON : on utilise l'heure locale.
    const now = new Date();
    small.textContent = data.response_time !== null && data.response_time !== undefined
        ? `${data.response_time} ms — ${now.toLocaleString()}`
        : now.toLocaleString();
    meta.appendChild(small);
    cardBody.appendChild(meta);

    card.appendChild(cardBody);

    return card;
}
````

Comparez-la avec la carte du template (section 5.2) : même `div.card`, même en-tête avec les deux badges, même paragraphe pour l'URL, même ligne grisée pour le temps et la date. Plusieurs points méritent attention :

- `card.dataset.method = method` crée l'attribut `data-method` : `dataset` est la façon de lire et d'écrire les attributs `data-*` en JavaScript. Les cartes JavaScript porteront donc les mêmes attributs que celles de Django ;
- le badge de statut est fabriqué par `createStatusBadge`, **réutilisée** telle quelle : les couleurs sont forcément les mêmes que dans le panneau de résultat ;
- la méthode et l'URL viennent du **formulaire** (le script les connaît déjà), le statut et le temps viennent de la **réponse** du serveur ;
- la réponse du serveur ne contient pas de date : la carte affiche donc l'heure locale de l'ordinateur, avec `new Date().toLocaleString()`.

> **À retenir**
>
> Vous remarquerez deux différences d'affichage entre les cartes créées par JavaScript et celles générées par Django après un rechargement. **La date** : JavaScript affiche l'heure locale au format français (`30/09/2026 10:38:30`), Django l'heure UTC au format anglais (`Sept. 30, 2026, 8:38 a.m.`), à cause des réglages `TIME_ZONE` et `LANGUAGE_CODE` restés par défaut. **Le temps de réponse** : JavaScript affiche la valeur exacte reçue, avec ses décimales, alors que `widthratio` l'arrondit à l'entier. Ces différences n'empêchent en rien le fonctionnement de l'application.

## 11.2 Ajouter la carte après chaque test

Dans l'écouteur `submit`, modifiez le second `.then()` : après l'appel à `displayResult(data)`, ajoutez l'insertion de la carte. Le bloc complet devient :

*api_tester/static/api_tester/js/main.js (second .then à compléter)*
````
        .then(function (data) {
            // Un 400 (method/url manquants) a un format de réponse différent
            // ({ "error": "..." }) et n'a déclenché aucun appel réseau côté serveur,
            // donc aucun ApiLog : traitement dédié, pas de carte d'historique.
            if (responseStatus === 400) {
                displayValidationError(data.error);
                return;
            }

            displayResult(data);

            // Retire le message "aucun historique" du bloc {% empty %} s'il est
            // encore présent, pour ne pas fausser le comptage des cartes.
            const emptyMessage = historyList.querySelector('p.text-muted');
            if (emptyMessage) {
                emptyMessage.remove();
            }

            historyList.prepend(createHistoryCard(method, url, data));

            if (historyList.children.length > 10) {
                historyList.lastElementChild.remove();
            }
        })
````

Ce code s'exécute uniquement pour un test **réellement exécuté** : une demande invalide (400) s'arrête au `return` précédent, exactement comme côté serveur, où elle ne crée aucun `ApiLog`. L'historique affiché reste ainsi cohérent avec la base.

| Instruction | Rôle |
| --- | --- |
| `historyList.querySelector('p.text-muted')` | Cherche le message « Aucun test effectué pour l'instant. » du bloc `{% empty %}`. S'il existe (premier test sur une base vide), il est supprimé avec `remove()`. |
| `historyList.prepend(...)` | Insère la nouvelle carte **en premier** dans la liste : le test le plus récent apparaît en haut, comme dans le tri de la vue. |
| `historyList.children.length > 10` | Compte les cartes. `children` ne contient que les balises enfants, d'où l'intérêt d'avoir supprimé le message vide. |
| `historyList.lastElementChild.remove()` | Supprime la dernière carte, la plus ancienne, pour revenir à 10. |

> **Pourquoi ?**
>
> La limite de 10 est appliquée **deux fois** : par la vue (`[:10]`) au chargement de la page, et par le script après chaque ajout. Sans cette seconde limite, la liste grandirait indéfiniment tant que la page n'est pas rechargée. La base de données, elle, conserve **tous** les tests : seule l'**affichage** est limité.

La variable `historyList` utilisée ici n'existe pas encore : vous la déclarez à l'étape suivante.

## 11.3 Restaurer un test d'un clic

Ajoutez ce bloc **juste avant** `form.addEventListener('submit', ...)` :

*api_tester/static/api_tester/js/main.js (bloc à ajouter)*
````
// Délégation d'événements : un seul écouteur sur le conteneur, valable aussi
// pour les cartes insérées dynamiquement après le chargement de la page.
// Clic sur une carte d'historique -> pré-remplit le formulaire (method/url),
// sans relancer le test : l'utilisateur doit soumettre lui-même (CDC §5.2).
const historyList = document.getElementById('history-list');

historyList.addEventListener('click', function (event) {
    const card = event.target.closest('[data-method]');

    if (!card) {
        return;
    }

    document.getElementById('method').value = card.dataset.method;
    document.getElementById('url').value = card.dataset.url;
});
````

### La délégation d'événements

Pourquoi un seul écouteur sur le **conteneur** `#history-list`, plutôt qu'un écouteur sur **chaque** carte ? Parce qu'un écouteur ajouté au chargement de la page ne concernerait que les cartes existantes à ce moment-là. Les cartes ajoutées ensuite par JavaScript ne réagiraient pas au clic.

En JavaScript, un clic « remonte » de l'élément cliqué vers ses parents : c'est la **propagation** (*bubbling*). Un clic sur un badge atteint donc aussi la carte, puis le conteneur. En écoutant le conteneur, on reçoit les clics de **toutes** ses cartes, présentes et futures. C'est la **délégation d'événements**.

### Retrouver la carte cliquée

`event.target` est l'élément précis sur lequel l'utilisateur a cliqué : un badge, l'URL, la date… `closest('[data-method]')` remonte ses parents jusqu'au premier qui possède un attribut `data-method`, c'est-à-dire la carte. Si le clic tombe entre deux cartes, `closest()` ne trouve rien et renvoie `null` : la fonction s'arrête.

### Ce que la restauration ne fait pas

Conformément au cahier des charges, la restauration se limite à la **méthode** et à l'**URL**. Elle ne remplit **pas** le payload, même si un payload est enregistré en base pour ce test, et elle ne **relance pas** le test : l'utilisateur garde la main et clique lui-même sur « Tester ».

## 11.4 Le script final

Voici `main.js` dans sa version finale, pour vérifier que chaque bloc est à sa place. Il suit un ordre logique : les fonctions d'abord, puis la déclaration de `historyList` et l'écouteur de clic, et enfin l'écouteur `submit`, qui utilise tout le reste.

*api_tester/static/api_tester/js/main.js (version finale)*
````
const form = document.getElementById('test-form');

// Construit le badge Bootstrap correspondant au status_code renvoyé par le serveur.
// Schéma unifié avec les cartes server-rendues dans index.html :
// vert (2xx), jaune (4xx, la cible a répondu mais signale une erreur client),
// rouge (5xx, erreur côté serveur cible), gris "Erreur" (null, pas de réponse reçue).
function createStatusBadge(statusCode) {
    const badge = document.createElement('span');
    badge.classList.add('badge');

    if (statusCode === null || statusCode === undefined) {
        badge.classList.add('bg-secondary');
        badge.textContent = 'Erreur';
    } else if (statusCode >= 200 && statusCode < 300) {
        badge.classList.add('bg-success');
        badge.textContent = String(statusCode);
    } else if (statusCode >= 400 && statusCode < 500) {
        badge.classList.add('bg-warning', 'text-dark');
        badge.textContent = String(statusCode);
    } else if (statusCode >= 500 && statusCode < 600) {
        badge.classList.add('bg-danger');
        badge.textContent = String(statusCode);
    } else {
        badge.classList.add('bg-secondary');
        badge.textContent = String(statusCode);
    }

    return badge;
}

// Affiche le résultat d'un test dans #result-panel. Construit les éléments via
// createElement/textContent (pas d'innerHTML) pour éviter tout risque d'injection.
function displayResult(data) {
    const panel = document.getElementById('result-panel');
    panel.textContent = '';

    const cardBody = document.createElement('div');
    cardBody.classList.add('card-body');

    const header = document.createElement('div');
    header.classList.add('d-flex', 'align-items-center', 'gap-2', 'mb-2');
    header.appendChild(createStatusBadge(data.status_code));

    if (data.response_time !== null && data.response_time !== undefined) {
        const responseTime = document.createElement('span');
        responseTime.classList.add('text-muted');
        responseTime.textContent = `${data.response_time} ms`;
        header.appendChild(responseTime);
    }

    cardBody.appendChild(header);

    if (data.error_message) {
        // Cas d'erreur réseau (timeout/connexion) : pas de corps JSON, juste le message.
        const errorText = document.createElement('p');
        errorText.classList.add('card-text', 'mb-0');
        errorText.textContent = data.error_message;
        cardBody.appendChild(errorText);
    } else {
        if (typeof data.response_body === 'string') {
            // CDC 2.2 : signaler explicitement l'absence de JSON exploitable.
            const notice = document.createElement('p');
            notice.classList.add('card-text', 'text-muted', 'mb-1');
            notice.textContent = 'Réponse non-JSON (texte brut) :';
            cardBody.appendChild(notice);
        }

        const pre = document.createElement('pre');
        pre.classList.add('mb-0');
        pre.textContent = typeof data.response_body === 'string'
            ? data.response_body
            : JSON.stringify(data.response_body, null, 2);
        cardBody.appendChild(pre);
    }

    panel.appendChild(cardBody);
}

// Affiche une erreur de validation (400, method/url manquants) dans #result-panel.
// Format de réponse différent du cas nominal/erreur réseau (cf. test_api_view :
// { "error": "..." }) : requête mal formée vers notre propre endpoint, pas un test
// exécuté, donc aucun ApiLog n'a été créé côté serveur.
function displayValidationError(message) {
    const panel = document.getElementById('result-panel');
    panel.textContent = '';

    const cardBody = document.createElement('div');
    cardBody.classList.add('card-body');

    const title = document.createElement('p');
    title.classList.add('card-text', 'fw-bold', 'mb-1');
    title.textContent = 'Formulaire invalide';
    cardBody.appendChild(title);

    const errorText = document.createElement('p');
    errorText.classList.add('card-text', 'mb-0');
    errorText.textContent = message;
    cardBody.appendChild(errorText);

    panel.appendChild(cardBody);
}

// Construit une carte d'historique identique (structure/classes) à celles déjà
// rendues côté serveur dans index.html. `data` est la réponse JSON de test_api_view
// (nominal ou erreur réseau) ; method/url viennent du formulaire, connus du client.
function createHistoryCard(method, url, data) {
    const card = document.createElement('div');
    card.classList.add('card');
    card.dataset.method = method;
    card.dataset.url = url;

    const cardBody = document.createElement('div');
    cardBody.classList.add('card-body');

    const header = document.createElement('div');
    header.classList.add('d-flex', 'justify-content-between', 'align-items-center', 'mb-2');

    const methodBadge = document.createElement('span');
    methodBadge.classList.add('badge', 'bg-secondary');
    methodBadge.textContent = method;
    header.appendChild(methodBadge);

    header.appendChild(createStatusBadge(data.status_code));

    cardBody.appendChild(header);

    const urlText = document.createElement('p');
    urlText.classList.add('card-text', 'text-break', 'mb-1');
    urlText.textContent = url;
    cardBody.appendChild(urlText);

    const meta = document.createElement('p');
    meta.classList.add('card-text', 'mb-0');
    const small = document.createElement('small');
    small.classList.add('text-muted');
    // Le serveur ne renvoie pas de date dans la réponse JSON : on utilise l'heure locale.
    const now = new Date();
    small.textContent = data.response_time !== null && data.response_time !== undefined
        ? `${data.response_time} ms — ${now.toLocaleString()}`
        : now.toLocaleString();
    meta.appendChild(small);
    cardBody.appendChild(meta);

    card.appendChild(cardBody);

    return card;
}

// Affiche un message simple dans #result-panel quand le fetch lui-même échoue
// (requête qui n'aboutit même pas, ex. serveur injoignable).
function displayFetchError(message) {
    const panel = document.getElementById('result-panel');
    panel.textContent = '';

    const cardBody = document.createElement('div');
    cardBody.classList.add('card-body');
    cardBody.appendChild(createStatusBadge(null));

    const errorText = document.createElement('p');
    errorText.classList.add('card-text', 'mb-0');
    errorText.textContent = message;
    cardBody.appendChild(errorText);

    panel.appendChild(cardBody);
}

// Délégation d'événements : un seul écouteur sur le conteneur, valable aussi
// pour les cartes insérées dynamiquement après le chargement de la page.
// Clic sur une carte d'historique -> pré-remplit le formulaire (method/url),
// sans relancer le test : l'utilisateur doit soumettre lui-même (CDC §5.2).
const historyList = document.getElementById('history-list');

historyList.addEventListener('click', function (event) {
    const card = event.target.closest('[data-method]');

    if (!card) {
        return;
    }

    document.getElementById('method').value = card.dataset.method;
    document.getElementById('url').value = card.dataset.url;
});

form.addEventListener('submit', function (event) {
    event.preventDefault();

    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const method = document.getElementById('method').value;
    const url = document.getElementById('url').value;
    const payloadText = document.getElementById('payload').value.trim();

    // Le payload JSON est parsé côté client avant tout envoi réseau : une erreur de
    // saisie est purement locale, inutile de solliciter le serveur pour la détecter.
    let payload;
    if (payloadText) {
        try {
            payload = JSON.parse(payloadText);
        } catch (error) {
            displayValidationError('Le payload JSON saisi est invalide : ' + error.message);
            return;
        }
    }

    const requestBody = { method: method, url: url };
    if (payload !== undefined) {
        requestBody.payload = payload;
    }

    const body = JSON.stringify(requestBody);

    // Capturé pour distinguer, dans le .then suivant, un test réellement exécuté
    // (200, ApiLog créé) d'une simple erreur de validation (400, aucun ApiLog).
    let responseStatus = null;

    fetch('/api/test/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken,
        },
        body: body,
    })
        .then(function (response) {
            responseStatus = response.status;
            return response.json();
        })
        .then(function (data) {
            // Un 400 (method/url manquants) a un format de réponse différent
            // ({ "error": "..." }) et n'a déclenché aucun appel réseau côté serveur,
            // donc aucun ApiLog : traitement dédié, pas de carte d'historique.
            if (responseStatus === 400) {
                displayValidationError(data.error);
                return;
            }

            displayResult(data);

            // Retire le message "aucun historique" du bloc {% empty %} s'il est
            // encore présent, pour ne pas fausser le comptage des cartes.
            const emptyMessage = historyList.querySelector('p.text-muted');
            if (emptyMessage) {
                emptyMessage.remove();
            }

            historyList.prepend(createHistoryCard(method, url, data));

            if (historyList.children.length > 10) {
                historyList.lastElementChild.remove();
            }
        })
        .catch(function (error) {
            console.error(error);
            displayFetchError('La requête vers le serveur a échoué.');
        });
});
````

## 11.5 Vérifier le résultat

Rechargez la page avec `Ctrl+F5`.

### L'ajout des cartes et la limite de 10

Faites **au moins 11 tests d'affilée**, sans recharger la page : par exemple plusieurs `GET` sur `https://jsonplaceholder.typicode.com/todos/1`, puis un dernier sur une autre adresse. Chaque test ajoute une carte en haut de l'historique, et la liste ne dépasse jamais 10 cartes.

*[Figure : fig-historique-10-cartes.png] L'historique après une série de tests : 10 cartes au maximum, la plus récente en haut. Les cartes ajoutées par JavaScript affichent l'heure locale, celles générées par Django au chargement l'heure UTC.*

### La restauration

Faites d'abord un test **POST** sur `https://jsonplaceholder.typicode.com/posts` (payload facultatif), pour avoir une carte POST dans l'historique. Rechargez ensuite la page (`F5`) pour vider le panneau de résultat. Choisissez **GET** et laissez le payload vide, puis cliquez sur une carte **POST** de l'historique : le formulaire affiche POST et l'URL de la carte, le payload reste vide, et aucun test n'est lancé.

*[Figure : fig-restauration.png] Après un clic sur une carte POST : la méthode et l'URL sont restaurées, le payload reste vide, et le panneau indique toujours « Aucun test exécuté. ».*

> **Point de vérification — fin de partie**
>
> Chaque test exécuté ajoute une carte **en haut** de l'historique, avec le bon badge, sans rechargement.
>
> Après 11 tests, l'historique compte **10 cartes** : la plus ancienne a disparu.
>
> Une demande invalide (URL `ftp://`) n'ajoute **aucune** carte.
>
> Un clic sur une carte, y compris sur son badge ou son URL, pré-remplit la méthode et l'URL, **sans** remplir le payload et **sans** lancer de test.
>
> Le clic fonctionne aussi bien sur une carte générée par Django que sur une carte ajoutée par JavaScript.
>
> Sur une base vide (supprimez les tests dans le shell Django, ouvert avec `python manage.py shell`, en tapant `from api_tester.models import ApiLog` puis `ApiLog.objects.all().delete()`), le premier test remplace le message « Aucun test effectué pour l'instant. ».

## 11.6 Enregistrer votre travail

*PowerShell*
````
git add .
git commit -m "Historique dynamique : ajout des cartes, limite de 10 et restauration au clic"
````

> **Commit — fin de la partie 11**
>
> L'application est fonctionnellement terminée. Les deux dernières parties la consolident : tests automatisés, sécurité et publication.

## Pièges fréquents de la partie 11

| Symptôme | Cause probable | Solution |
| --- | --- | --- |
| `ReferenceError: historyList is not defined` | Le bloc de la section 11.3, qui déclare `historyList`, a été oublié. | Ajoutez-le juste **avant** `form.addEventListener('submit', ...)`. |
| Les nouvelles cartes ne réagissent pas au clic | Un écouteur a été ajouté sur chaque carte au lieu du conteneur. | Un seul écouteur, sur `#history-list`, avec `closest()` (section 11.3). |
| Le clic sur un badge ne fait rien | `event.target` est utilisé directement, sans `closest()`. | `event.target.closest('[data-method]')` remonte jusqu'à la carte. |
| L'historique dépasse 10 cartes | Le test de longueur manque, ou le message vide est compté comme une carte. | Vérifiez la suppression de `p.text-muted` avant `prepend`, puis le test `> 10`. |
| Une carte apparaît pour une demande invalide | L'insertion est placée avant le `return` du cas 400. | L'insertion doit venir **après** `displayResult(data)`. |
| La nouvelle carte s'ajoute en bas | `append` utilisé au lieu de `prepend`. | `historyList.prepend(...)` insère en premier. |

# Partie 12 — Les tests automatisés

Depuis le début, vous vérifiez votre travail **à la main** : dans le shell, dans le navigateur, dans les outils de développement. C'est indispensable, mais long, et il faudrait tout recommencer après chaque modification. Un **test automatisé** est un petit programme qui vérifie un comportement précis et signale immédiatement toute régression. Dans cette partie, vous écrivez **21 tests** qui couvrent le modèle, la page d'accueil et l'endpoint `/api/test/`, puis vous les lancez tous en une seule commande.

> **Blocs de compétences**
>
> Compétences travaillées : **CDA BC03** (préparer et exécuter les plans de tests d'une application). Les tests garantissent aussi la qualité attendue en **DWWM BC02**.

## 12.1 Comment Django exécute les tests

Les tests se trouvent dans le fichier `api_tester/tests.py`, créé par `startapp`. La commande `python manage.py test` les découvre et les exécute. Quelques règles à connaître :

- un groupe de tests est une **classe** qui hérite de `django.test.TestCase` ;
- chaque **méthode** dont le nom commence par `test_` est un test ;
- un test vérifie des résultats avec des **assertions** : `self.assertEqual(a, b)` échoue si `a` et `b` sont différents, `self.assertIsNone(x)` si `x` n'est pas `None`, etc. ;
- Django crée une **base de données de test**, vide, avant les tests, et la détruit après. Vos données de développement (`db.sqlite3`) ne sont **jamais** touchées ;
- chaque test s'exécute dans une **transaction annulée** à la fin : les données créées par un test n'existent plus pour le suivant. Les tests sont donc indépendants les uns des autres.

> **Pourquoi ?**
>
> Des noms de tests longs et explicites, comme `test_timeout_renvoie_200_avec_champs_null_et_cree_apilog`, sont une bonne pratique. Quand un test échoue, son nom dit immédiatement **ce qui ne fonctionne plus**, sans avoir à lire son code.

## 12.2 Simuler l'API cible : les mocks

Tester `test_api_view` pose un problème : la vue appelle une API **sur Internet**. Un test qui dépend du réseau serait lent, et il échouerait si l'API était en panne ou si l'ordinateur était hors ligne, alors que votre code n'y serait pour rien.

La solution est de **simuler** `requests` pendant le test. Le module standard `unittest.mock` fournit deux outils :

| Outil | Rôle |
| --- | --- |
| `patch('api_tester.views.requests.get')` | Remplace **temporairement**, le temps d'un test, la fonction `requests.get` utilisée par `views.py` par un faux objet. Aucune requête ne part sur le réseau. |
| `MagicMock()` | Un objet « caméléon » qui accepte tous les attributs et tous les appels. On lui dicte ce qu'il doit renvoyer, et il mémorise comment il a été appelé. |

Deux réglages de ce faux objet sont utilisés dans les tests :

- `mock_get.return_value = ...` : ce que renvoie l'appel, ici une fausse réponse HTTP ;
- `mock_get.side_effect = requests.exceptions.Timeout()` : l'appel **lève** cette exception, pour simuler une API qui ne répond pas.

Après l'appel, `mock_post.call_args` indique avec quels paramètres la fonction a été appelée. C'est ainsi qu'on vérifie que la vue transmet bien `timeout=5` et `json=payload` à `requests`.

> **Attention**
>
> On « patche » `api_tester.views.requests.get`, c'est-à-dire **là où la fonction est utilisée**, et non `requests.get` à l'endroit où elle est définie. C'est la règle de `patch` : on remplace le nom tel que le code testé le voit.

## 12.3 Écrire les tests

Remplacez tout le contenu de `api_tester/tests.py`. Le fichier est présenté en trois blocs, à taper à la suite les uns des autres.

### Bloc 1 : les imports, la fausse réponse et les tests du modèle

*api_tester/tests.py (1/3)*
````
import json
from unittest.mock import MagicMock, patch

import requests
from django.test import Client, TestCase
from django.urls import reverse

from .models import ApiLog

# Sentinel : distingue "aucun JSON exploitable" (response.json() doit lever
# ValueError, comme une vraie réponse non-JSON) d'un JSON valide qui vaudrait None.
_NO_JSON = object()

def make_mock_response(status_code=200, json_body=_NO_JSON, text_body="", elapsed_seconds=0.05):
    """Simule un objet requests.Response, sans appel réseau réel."""
    response = MagicMock()
    response.status_code = status_code
    response.elapsed.total_seconds.return_value = elapsed_seconds
    response.text = text_body
    if json_body is _NO_JSON:
        response.json.side_effect = ValueError("Réponse non-JSON")
    else:
        response.json.return_value = json_body
    return response

class ApiLogModelTests(TestCase):
    def test_str_avec_status_code(self):
        log = ApiLog.objects.create(url="https://example.com/", method="GET", status_code=200)
        self.assertIn("200", str(log))

    def test_str_sans_status_code(self):
        log = ApiLog.objects.create(url="https://example.com/", method="GET", status_code=None)
        self.assertIn("échec", str(log))

    def test_tri_par_defaut_plus_recent_dabord(self):
        plus_ancien = ApiLog.objects.create(url="https://example.com/a", method="GET")
        plus_recent = ApiLog.objects.create(url="https://example.com/b", method="GET")
        logs = list(ApiLog.objects.all())
        self.assertEqual(logs[0], plus_recent)
        self.assertEqual(logs[1], plus_ancien)
````

`make_mock_response()` fabrique une **fausse réponse** `requests` avec les attributs que lit la vue : `status_code`, `elapsed.total_seconds()`, `text` et `json()`. Si aucun corps JSON n'est fourni, `json()` lève `ValueError`, exactement comme une vraie réponse non-JSON.

`_NO_JSON` est une **sentinelle** : un objet unique qui sert de valeur par défaut. Pourquoi ne pas utiliser `None` ? Parce que `None` est aussi un JSON valide (`null`). La sentinelle permet de distinguer « aucun JSON » de « un JSON qui vaut `null` ».

Les trois tests du modèle vérifient l'affichage de `__str__` (avec un statut, puis `échec` sans statut) et le tri par défaut.

### Bloc 2 : les tests de la page d'accueil

*api_tester/tests.py (2/3)*
````
class IndexViewTests(TestCase):
    def test_get_renvoie_200_et_le_bon_template(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'api_tester/index.html')

    def test_historique_limite_a_10(self):
        for i in range(15):
            ApiLog.objects.create(url=f"https://example.com/{i}", method="GET", status_code=200)
        response = self.client.get(reverse('index'))
        self.assertEqual(len(response.context['history']), 10)

    def test_historique_plus_recent_dabord(self):
        ApiLog.objects.create(url="https://example.com/1", method="GET")
        deuxieme = ApiLog.objects.create(url="https://example.com/2", method="GET")
        response = self.client.get(reverse('index'))
        self.assertEqual(response.context['history'][0], deuxieme)
````

`self.client` est un client de test, le même que celui utilisé dans le shell, fourni automatiquement par `TestCase`. `reverse('index')` retrouve l'adresse d'une route à partir de son **nom** (le paramètre `name` de la partie 4). Si l'adresse change un jour, les tests continueront de fonctionner.

`response.context['history']` donne accès au contexte transmis au template : on peut ainsi vérifier **ce que la vue envoie** (10 tests, dans le bon ordre), indépendamment de l'affichage HTML.

### Bloc 3 : les tests de l'endpoint /api/test/

*api_tester/tests.py (3/3)*
````
class TestApiViewTests(TestCase):
    def setUp(self):
        self.url = reverse('test_api')

    def post_json(self, payload):
        return self.client.post(self.url, data=json.dumps(payload), content_type='application/json')

    # --- Méthode HTTP et validation ---

    def test_get_est_refuse_405(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_400_si_method_manquant(self):
        response = self.post_json({"url": "https://example.com/"})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
        self.assertEqual(ApiLog.objects.count(), 0)

    def test_400_si_url_manquante(self):
        response = self.post_json({"method": "GET"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(ApiLog.objects.count(), 0)

    def test_400_si_methode_invalide(self):
        response = self.post_json({"method": "PATCH", "url": "https://example.com/"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(ApiLog.objects.count(), 0)

    def test_400_si_schema_url_invalide(self):
        response = self.post_json({"method": "GET", "url": "ftp://example.com/fichier"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(ApiLog.objects.count(), 0)

    def test_csrf_actif_aucun_exempt(self):
        # Le client de test Django désactive le CSRF par défaut : on le réactive
        # explicitement pour confirmer qu'aucune vue n'est marquée @csrf_exempt.
        csrf_client = Client(enforce_csrf_checks=True)
        response = csrf_client.post(
            self.url, data=json.dumps({"method": "GET", "url": "https://example.com/"}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 403)

    # --- Cas nominal ---

    @patch('api_tester.views.requests.get')
    def test_get_nominal_cree_apilog_et_temps_en_ms_au_client(self, mock_get):
        mock_get.return_value = make_mock_response(status_code=200, json_body={"ok": True}, elapsed_seconds=0.5)
        response = self.post_json({"method": "GET", "url": "https://example.com/"})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status_code'], 200)
        self.assertEqual(data['response_time'], 500)  # 0.5 s -> 500 ms au client
        self.assertEqual(data['response_body'], {"ok": True})

        self.assertEqual(ApiLog.objects.count(), 1)
        log = ApiLog.objects.first()
        self.assertEqual(log.method, 'GET')
        self.assertEqual(log.status_code, 200)
        self.assertAlmostEqual(log.response_time, 0.5)  # stocké en secondes en base
        self.assertIsNone(log.payload_sent)
        self.assertEqual(log.response_body, {"ok": True})
        self.assertIsNone(log.error_message)

    @patch('api_tester.views.requests.post')
    def test_post_avec_payload_transmis_et_stocke(self, mock_post):
        mock_post.return_value = make_mock_response(status_code=201, json_body={"id": 1})
        payload = {"nom": "test"}
        response = self.post_json({"method": "POST", "url": "https://example.com/", "payload": payload})
        self.assertEqual(response.status_code, 200)

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "https://example.com/")
        self.assertEqual(kwargs.get('json'), payload)
        self.assertEqual(kwargs.get('timeout'), 5)

        self.assertEqual(ApiLog.objects.first().payload_sent, payload)

    @patch('api_tester.views.requests.put')
    def test_put_avec_payload_transmis_et_stocke(self, mock_put):
        mock_put.return_value = make_mock_response(status_code=200, json_body={"updated": True})
        payload = {"a": 1}
        self.post_json({"method": "PUT", "url": "https://example.com/1", "payload": payload})

        _args, kwargs = mock_put.call_args
        self.assertEqual(kwargs.get('json'), payload)
        self.assertEqual(kwargs.get('timeout'), 5)
        self.assertEqual(ApiLog.objects.first().payload_sent, payload)

    @patch('api_tester.views.requests.delete')
    def test_delete_sans_payload(self, mock_delete):
        mock_delete.return_value = make_mock_response(status_code=204)
        response = self.post_json({"method": "DELETE", "url": "https://example.com/1"})

        self.assertEqual(response.status_code, 200)
        log = ApiLog.objects.first()
        self.assertEqual(log.method, 'DELETE')
        self.assertIsNone(log.payload_sent)

    @patch('api_tester.views.requests.get')
    def test_get_ignore_un_payload_fourni_par_erreur(self, mock_get):
        mock_get.return_value = make_mock_response(status_code=200, json_body={})
        self.post_json({"method": "GET", "url": "https://example.com/", "payload": {"x": 1}})

        _args, kwargs = mock_get.call_args
        self.assertNotIn('json', kwargs)
        self.assertIsNone(ApiLog.objects.first().payload_sent)

    @patch('api_tester.views.requests.get')
    def test_reponse_non_json_repliee_sur_texte_brut(self, mock_get):
        mock_get.return_value = make_mock_response(status_code=200, text_body="<html>hi</html>")
        response = self.post_json({"method": "GET", "url": "https://example.com/"})

        data = response.json()
        self.assertEqual(data['response_body'], "<html>hi</html>")
        self.assertEqual(ApiLog.objects.first().response_body, "<html>hi</html>")

    # --- Erreurs réseau ---

    @patch('api_tester.views.requests.get')
    def test_timeout_renvoie_200_avec_champs_null_et_cree_apilog(self, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout()
        response = self.post_json({"method": "GET", "url": "https://example.com/"})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsNone(data['status_code'])
        self.assertIsNone(data['response_time'])
        self.assertTrue(data['error_message'])

        self.assertEqual(ApiLog.objects.count(), 1)
        log = ApiLog.objects.first()
        self.assertIsNone(log.status_code)
        self.assertIsNone(log.response_time)
        self.assertTrue(log.error_message)

    @patch('api_tester.views.requests.get')
    def test_connection_error_renvoie_200_et_cree_apilog(self, mock_get):
        mock_get.side_effect = requests.exceptions.ConnectionError()
        response = self.post_json({"method": "GET", "url": "https://example.com/"})

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()['status_code'])
        self.assertEqual(ApiLog.objects.count(), 1)

    @patch('api_tester.views.requests.get')
    def test_request_exception_generique_renvoie_200_avec_message(self, mock_get):
        mock_get.side_effect = requests.exceptions.RequestException("boum")
        response = self.post_json({"method": "GET", "url": "https://example.com/"})

        self.assertEqual(response.status_code, 200)
        self.assertIn('boum', response.json()['error_message'])
        self.assertEqual(ApiLog.objects.count(), 1)
````

`setUp()` s'exécute **avant chaque test** de la classe : c'est l'endroit où préparer ce qui est commun. `post_json()` est une petite méthode utilitaire qui évite de répéter `json.dumps` et `content_type` dans chaque test.

Les tests sont regroupés en trois familles, qui reprennent les parties 6, 7 et 8 :

| Famille | Ce qui est vérifié |
| --- | --- |
| **Validation** (partie 6) | Refus de GET (405), des champs manquants, d'une méthode inconnue et d'un schéma `ftp://` (400), **sans créer d'`ApiLog`**. |
| **Cas nominal** (partie 7) | Création de l'`ApiLog`, temps en secondes en base et en millisecondes dans la réponse, payload transmis pour POST et PUT avec `timeout=5`, payload ignoré pour GET, repli sur le texte brut. |
| **Erreurs réseau** (partie 8) | Réponse 200 avec des champs `null` et un message, et test enregistré quand même. |

> **Pourquoi ?**
>
> Le test `test_csrf_actif_aucun_exempt` mérite attention. Le client de test **désactive** la vérification CSRF par défaut, pour simplifier les tests. Ce test crée un client avec `enforce_csrf_checks=True`, qui la réactive, puis envoie une requête **sans jeton** : elle doit être refusée avec le statut **403**. Si quelqu'un ajoutait un jour `@csrf_exempt` sur la vue, ce test échouerait immédiatement. C'est un test de **sécurité**.

## 12.4 Lancer les tests

*PowerShell*
````
python manage.py test api_tester
````

*Sortie attendue*
````
Found 21 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
.....................
----------------------------------------------------------------------
Ran 21 tests in 0.059s

OK
Destroying test database for alias 'default'...
````

Chaque point représente un test réussi. Un test échoué est marqué `F` (une assertion fausse) et un test en erreur `E` (une exception inattendue), avec le détail du problème sous la ligne de tirets. Pour voir le nom de chaque test, ajoutez l'option `-v 2` :

*PowerShell*
````
python manage.py test api_tester -v 2
````

*Sortie attendue (extrait)*
````
test_str_avec_status_code (api_tester.tests.ApiLogModelTests.test_str_avec_status_code) ... ok
test_str_sans_status_code (api_tester.tests.ApiLogModelTests.test_str_sans_status_code) ... ok
...
test_timeout_renvoie_200_avec_champs_null_et_cree_apilog (api_tester.tests.TestApiViewTests.test_timeout_renvoie_200_avec_champs_null_et_cree_apilog) ... ok
````

Pour lancer un seul test, précisez son chemin complet :

*PowerShell*
````
python manage.py test api_tester.tests.TestApiViewTests.test_get_est_refuse_405
````

### Voir un test échouer

Un test n'a de valeur que s'il **échoue** quand le code est faux. Faites l'expérience : dans `index_view`, remplacez temporairement `[:10]` par `[:11]`, puis relancez les tests.

*Sortie attendue (extrait)*
````
FAIL: test_historique_limite_a_10 (api_tester.tests.IndexViewTests.test_historique_limite_a_10)
...
AssertionError: 11 != 10

Ran 21 tests in 0.061s

FAILED (failures=1)
````

Le test signale précisément le problème : 11 tests affichés au lieu de 10. **Remettez `[:10]`** et vérifiez que tout redevient `OK`.

> **Point de vérification — fin de partie**
>
> `python manage.py test api_tester` affiche `Ran 21 tests` et `OK`.
>
> La modification volontaire de `[:10]` fait échouer `test_historique_limite_a_10`, puis tout redevient vert une fois le code rétabli.
>
> Votre base de développement n'a pas été modifiée : l'historique de la page d'accueil est inchangé.

> **À retenir**
>
> Prenez l'habitude de lancer les tests **avant chaque commit**. C'est le moyen le plus sûr de ne pas enregistrer une régression.

## 12.5 Enregistrer votre travail

*PowerShell*
````
git add .
git commit -m "Tests automatisés : modèle, page d'accueil et endpoint /api/test/"
````

> **Commit — fin de la partie 12**
>
> Seul `tests.py` a changé.

## Pièges fréquents de la partie 12

| Symptôme | Cause probable | Solution |
| --- | --- | --- |
| `Ran 0 tests` | Les méthodes ne commencent pas par `test_`, ou la classe n'hérite pas de `TestCase`. | Respectez le préfixe `test_` et `class ...(TestCase)`. |
| Un test d'erreur réseau part réellement sur Internet et échoue | Le `patch` vise le mauvais nom. | Patchez `api_tester.views.requests.get` (là où il est utilisé), section 12.2. |
| `NoReverseMatch: Reverse for 'test_api' not found` | Le nom de la route ne correspond pas. | Les routes s'appellent `index` et `test_api` (paramètre `name` dans `urls.py`). |
| `test_csrf_actif_aucun_exempt` échoue avec `200 != 403` | La vue a été marquée `@csrf_exempt`, ou le middleware CSRF a été retiré de `settings.py`. | Supprimez le décorateur ; ne modifiez pas `MIDDLEWARE`. |
| `test_get_nominal_...` échoue avec `0.5 != 500` ou l'inverse | Les unités de `response_time` sont inversées. | Secondes en base, millisecondes dans la réponse (section 7.4). |

# Partie 13 — Sécurité et finalisation

L'application fonctionne et elle est testée. Cette dernière partie la prépare à être rendue. Vous faites le **bilan de sécurité** du projet et étudiez en détail le risque **SSRF**, propre à ce type d'outil. Vous rédigez ensuite le **README**, vous publiez le projet sur **GitHub**, et vous vérifiez que tous les livrables du cahier des charges sont présents.

> **Blocs de compétences**
>
> Compétences travaillées : **CDA BC01** (sécuriser une application) et **CDA BC03** (préparer et documenter le déploiement), **DWWM BC02** (documenter le déploiement d'une application).

## 13.1 Le bilan de sécurité du projet

Vous avez mis en place, au fil des parties, plusieurs protections. Les voici rassemblées. Vous devez être capable de les **expliquer**, notamment lors de la démonstration de votre projet :

| Protection | Contre quel risque ? | Où ? |
| --- | --- | --- |
| **Timeout** de 5 secondes sur chaque appel `requests` | Une API cible qui ne répond jamais bloquerait le serveur indéfiniment. | Partie 7 : `request_kwargs` |
| **Validation** de la méthode et des champs obligatoires | Des données inattendues ou incomplètes envoyées à la vue. | Partie 6 |
| **Schéma d'URL** limité à `http` et `https` | L'utilisation d'autres protocoles, par exemple `file://` pour tenter de lire des fichiers du serveur. | Partie 6 |
| **Protection CSRF** active, jeton transmis dans `X-CSRFToken`, aucun `@csrf_exempt` | Un site malveillant qui enverrait des requêtes à la place de l'utilisateur. | Parties 9 et 12 |
| **Échappement** automatique des templates Django | Du code HTML ou JavaScript injecté dans une URL de l'historique (XSS). | Partie 5 |
| **`textContent`** au lieu d'`innerHTML` en JavaScript | Du code malveillant contenu dans la réponse d'une API (XSS). | Parties 10 et 11 |
| **Gestion des exceptions** réseau | Une erreur non gérée qui renverrait une page 500 et bloquerait l'interface. | Partie 8 |

## 13.2 Le risque SSRF

### De quoi s'agit-il ?

Une attaque **SSRF** (*Server-Side Request Forgery*, falsification de requête côté serveur) consiste à faire exécuter par un serveur une requête vers une adresse choisie par l'attaquant. Or c'est **exactement** ce que fait votre application : elle envoie des requêtes vers n'importe quelle URL saisie par l'utilisateur. C'est son principe même, mais c'est aussi un risque réel.

Le danger vient de la **position** du serveur. Il se trouve souvent dans un réseau interne, avec des accès que l'utilisateur n'a pas. Si l'application était installée sur un serveur d'entreprise et accessible publiquement, un visiteur pourrait lui faire interroger :

- **le serveur lui-même** : `http://127.0.0.1/...`, pour atteindre des services qui n'écoutent qu'en local (une base de données, une interface d'administration) ;
- **le réseau interne** : `http://192.168.1.1/`, `http://10.0.0.5/`…, des machines normalement invisibles depuis Internet ;
- **les services du fournisseur cloud** : sur de nombreux hébergeurs, l'adresse `http://169.254.169.254/` donne accès à des informations de configuration du serveur, parfois même à des identifiants.

### Constatez-le vous-même

Serveur lancé, testez avec votre propre application l'adresse `http://127.0.0.1:8000/admin/`. Vous obtenez une réponse **200** et le code HTML de la page de connexion de l'administration Django. Votre testeur vient d'interroger… son propre serveur. Sur votre poste, c'est sans conséquence. Sur un serveur exposé à Internet, ce serait une faille.

Au passage, `/admin/` ne répond pas directement 200 : il **redirige** d'abord (statut 302) vers `/admin/login/`, et `requests` suit cette redirection automatiquement. C'est exactement le mécanisme visé par la piste « Redirections contrôlées » du tableau ci-dessous : une adresse d'apparence anodine peut mener ailleurs.

### Les pistes de protection

Le cahier des charges n'exige pas de protection complète contre le SSRF pour ce projet pédagogique. Il exige que vous sachiez **expliquer** le risque et les pistes pour s'en protéger :

| Piste | Principe |
| --- | --- |
| **Liste blanche** | N'autoriser que certains domaines connus (par exemple les API de l'entreprise). C'est la protection la plus sûre, mais elle limite l'outil. |
| **Blocage des adresses internes** | Avant l'appel, résoudre le nom de domaine en adresse IP (module `socket`), puis refuser les adresses privées, locales ou réservées (module `ipaddress` : `is_private`, `is_loopback`, `is_link_local`…). |
| **Redirections contrôlées** | Une URL publique peut **rediriger** vers une adresse interne. Il faut désactiver les redirections automatiques (`allow_redirects=False`) ou vérifier chaque étape. |
| **Authentification** | Réserver l'outil à des utilisateurs connus et identifiés, pour qu'il ne soit pas accessible à n'importe qui. |
| **Isolation réseau** | Installer l'application sur une machine qui n'a accès à aucun réseau interne. |

Documentez ce risque directement dans le code. Dans `api_tester/views.py`, ajoutez ce commentaire juste après la ligne `# Création des views` :

*api_tester/views.py (commentaire à ajouter)*
````
# Création des views

# Note sur la sécurité (SSRF) : test_api_view effectue, sur demande de l'utilisateur,
# des requêtes HTTP sortantes (GET/POST/PUT/DELETE, avec payload arbitraire pour
# PUT/POST) vers une URL également fournie par l'utilisateur. C'est le principe même
# de l'outil, mais c'est aussi un vecteur SSRF classique (scanner un réseau interne,
# interroger des services non exposés publiquement, etc.). La validation de schéma
# (http/https uniquement) ci-dessous est un garde-fou minimal ; elle ne remplace pas,
# en production, une liste blanche de domaines/IP autorisés et un blocage explicite
# des plages d'IP privées/internes (10.0.0.0/8, 127.0.0.0/8, 169.254.0.0/16, etc.) —
# hors périmètre de ce projet pédagogique.
````

### Et pour une mise en production ?

Votre projet est prévu pour tourner **en local**. Avant de l'installer sur un vrai serveur, il faudrait au minimum revoir trois réglages de `settings.py`, comme le rappellent les commentaires générés par Django :

- `DEBUG = True` affiche des pages d'erreur détaillées, qui révèlent le code et la configuration : il doit passer à `False` ;
- `SECRET_KEY` doit être une clé **secrète et unique**, lue depuis une variable d'environnement plutôt qu'écrite dans le code publié sur GitHub ;
- `ALLOWED_HOSTS` doit lister les noms de domaine autorisés à servir l'application.

## 13.3 Rédiger le README

Le fichier `README.md` est la **première chose** que l'on voit en ouvrant un dépôt GitHub. Il doit permettre à n'importe qui de comprendre le projet et de l'installer sans aide. Le cahier des charges demande au minimum : le nom et l'objectif du projet, les prérequis et l'installation, les fonctionnalités, et les limites connues.

Créez `README.md` à la racine du projet. Il est écrit en **Markdown** : `#` pour les titres, `-` pour les listes, trois accents graves pour les blocs de code. Voici une base à adapter, en remplaçant `votre-compte` par votre identifiant GitHub :

*README.md*
````
# Testeur d'API HTTP

Application web Django permettant de tester des endpoints d'API HTTP
(GET/POST/PUT/DELETE) depuis une interface web, avec une communication
front/back en **JSON strict** (pas de formulaires HTML classiques ni de FormData).

## Prérequis

- Windows 10 ou 11, Python 3.13, Git
- Un accès réseau sortant pour tester des API tierces (PokeAPI, httpbin.org, etc.)

## Installation

```powershell
git clone https://github.com/votre-compte/testeur-api-http.git
cd testeur-api-http
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Puis ouvrir http://127.0.0.1:8000/.

## Fonctionnalités

- Formulaire de test : méthode (GET/POST/PUT/DELETE), URL cible et payload JSON
  optionnel (pour PUT/POST), validé côté client avant l'envoi.
- Exécution de la requête côté serveur avec `requests` (`timeout=5` systématique),
  résultat affiché sans rechargement de page (`fetch` JSON, jeton CSRF transmis
  dans l'en-tête `X-CSRFToken`).
- Affichage du résultat : badge de statut coloré (vert 2xx, jaune 4xx, rouge 5xx,
  gris "Erreur" sans réponse), temps de réponse, corps formaté (JSON indenté, ou
  texte brut signalé comme tel).
- Gestion des erreurs réseau (timeout, hôte injoignable, URL invalide) et des
  erreurs de validation, sans jamais bloquer l'interface.
- Historique des 10 derniers tests, enregistré en base (`ApiLog`), mis à jour
  dynamiquement après chaque test.
- Clic sur une carte d'historique : restaure la méthode et l'URL dans le formulaire
  (jamais le payload), sans relancer le test.

## Tests

```powershell
python manage.py test api_tester
```

## Limites connues

- Pas de liste blanche de domaines ni de blocage des plages d'IP internes
  (protection SSRF) : seule une validation du schéma d'URL (http/https) est en place.
- Pas d'authentification : l'outil est prévu pour un usage local de développement,
  pas pour être exposé publiquement tel quel.
- Le corps envoyé à l'API cible est toujours du JSON (pas de multipart/form-data).

## Note sur la sécurité

- **Timeout obligatoire** : chaque appel sortant utilise `timeout=5`.
- **Validation du schéma d'URL** : seules les URL `http://` et `https://` sont acceptées.
- **Risque SSRF** : l'application exécute des requêtes vers des URL fournies par
  l'utilisateur. En production, il faudrait une liste blanche de domaines et un
  blocage des plages d'IP privées (voir le commentaire dans `api_tester/views.py`).
- **Protection CSRF** active sur toute l'application (aucun `@csrf_exempt`).
- **Protection XSS** : échappement automatique des templates et `textContent` en JavaScript.
````

> **À retenir**
>
> Dans VS Code, ouvrez `README.md` puis appuyez sur `Ctrl+Maj+V` : un aperçu montre le rendu du Markdown, tel qu'il apparaîtra sur GitHub.

Vérifiez aussi une dernière fois `requirements.txt` : il doit toujours contenir exactement `Django==6.0.8` et `requests==2.34.2`. Enregistrez ce travail :

*PowerShell*
````
python manage.py test api_tester
git add .
git commit -m "Note de sécurité SSRF et README"
````

## 13.4 Publier le projet sur GitHub

1. Sur **github.com**, créez un nouveau dépôt (bouton **New**), par exemple `testeur-api-http`. **Ne cochez rien** : ni README, ni `.gitignore`, ni licence. Votre dépôt local contient déjà tout, et un dépôt distant non vide créerait un conflit au premier envoi.
2. GitHub affiche l'adresse du dépôt, de la forme `https://github.com/votre-compte/testeur-api-http.git`. Copiez-la.
3. Dans le terminal, reliez votre dépôt local au dépôt GitHub, puis envoyez vos commits :

*PowerShell*
````
git remote add origin https://github.com/votre-compte/testeur-api-http.git
git push -u origin main
````

Au premier envoi, une fenêtre de connexion à GitHub peut s'ouvrir : suivez-la. L'option `-u` mémorise le lien entre votre branche `main` et celle de GitHub. Les fois suivantes, un simple `git push` suffira.

> **Attention**
>
> Avant de pousser, vérifiez avec `git status` et sur la page du dépôt que ni `venv/`, ni `db.sqlite3`, ni aucun fichier `.env` n'est publié. Si c'était le cas, votre `.gitignore` n'était pas en place au moment du `git add` (partie 2).

## 13.5 La liste des livrables

Vérifiez point par point les livrables demandés par le cahier des charges :

| Livrable | Comment le vérifier |
| --- | --- |
| **Dépôt GitHub** avec le code source complet | Sur GitHub, on retrouve `api_tester/`, `api_tester_project/`, `manage.py`, les deux migrations, le template, `main.js` et `tests.py`. |
| **`.gitignore`** adapté | `venv/`, `__pycache__/`, `db.sqlite3` et `.env` n'apparaissent pas sur GitHub. |
| **Historique de commits** lisible | `git log --oneline` montre une progression logique : un commit par partie, de l'initialisation à la finalisation. |
| **`README.md`** | Nom et objectif, prérequis, installation, fonctionnalités, limites connues et note de sécurité. |
| **`requirements.txt`** | Contient `Django==6.0.8` et `requests==2.34.2`. |
| **Démonstration** | Selon les modalités fixées par votre formateur, montrez au minimum : un test réussi, un test en erreur (timeout ou URL invalide), et l'usage de l'historique (ajout d'une carte, restauration au clic). |

> **Point de vérification — fin du projet**
>
> Les 21 tests passent.
>
> Le dépôt GitHub contient tous les fichiers du projet, et aucun fichier ignoré.
>
> Le README s'affiche correctement sur la page d'accueil du dépôt.
>
> Vous savez expliquer, en quelques phrases, le risque SSRF et deux pistes pour s'en protéger.

> **Fin du tutoriel**
>
> Félicitations : votre Testeur d'API HTTP est terminé, testé, documenté et publié.

# Annexes

## A.1 Adresses de test

Ces adresses publiques permettent de vérifier chaque comportement de l'application. Elles sont gratuites et ne demandent aucune inscription.

| Méthode | Adresse | Résultat attendu |
| --- | --- | --- |
| GET | `https://pokeapi.co/api/v2/pokemon/ditto` | Badge vert **200**, JSON (un Pokémon). |
| GET | `https://jsonplaceholder.typicode.com/todos/1` | Badge vert **200**, JSON court. Pratique pour les tests répétés. |
| POST | `https://jsonplaceholder.typicode.com/posts` | Badge vert **201**, le payload renvoyé avec un `id`. Payload : `{"title": "Test", "userId": 1}`. |
| PUT | `https://jsonplaceholder.typicode.com/posts/1` | Badge vert **200**, le payload renvoyé, complété de `"id": 1`. |
| DELETE | `https://jsonplaceholder.typicode.com/posts/1` | Badge vert **200**, corps `{}`. |
| GET | `https://httpbin.org/status/404` | Badge jaune **404**. |
| GET | `https://httpbin.org/status/500` | Badge rouge **500**. |
| GET | `https://httpbin.org/html` | Badge vert **200**, mention « Réponse non-JSON » et code HTML. |
| GET | `http://10.255.255.1` | Badge gris « Erreur », message de timeout après 5 secondes. |
| GET | `http://domaine-inexistant.test` | Badge gris « Erreur », « Impossible de joindre l'hôte. ». |
| GET | `ftp://example.com/fichier` | « Formulaire invalide » : schéma refusé par le serveur. |

> **À retenir**
>
> JSONPlaceholder **simule** les créations, modifications et suppressions : aucune donnée n'est réellement modifiée sur leur serveur. Vous pouvez donc tester POST, PUT et DELETE sans risque.

## A.2 Commandes utiles

Toutes ces commandes se tapent dans le terminal de VS Code, **à la racine du projet** et **avec le venv activé** (`(venv)` en début de ligne).

| Commande | Rôle |
| --- | --- |
| `.\venv\Scripts\Activate.ps1` | Activer l'environnement virtuel. |
| `python -m pip install -r requirements.txt` | Installer les dépendances du projet. |
| `python manage.py runserver` | Lancer le serveur de développement (arrêt : `Ctrl+C`). |
| `python manage.py check` | Vérifier la configuration du projet. |
| `python manage.py makemigrations api_tester` | Générer une migration après une modification du modèle. |
| `python manage.py migrate` | Appliquer les migrations à la base de données. |
| `python manage.py showmigrations api_tester` | Voir les migrations appliquées (`[X]`) ou non (`[ ]`). |
| `python manage.py shell` | Ouvrir le shell Django (sortie : `exit()`). |
| `python manage.py test api_tester` | Lancer les tests automatisés (`-v 2` pour le détail). |
| `git status` | Voir les fichiers modifiés depuis le dernier commit. |
| `git add .` puis `git commit -m "message"` | Enregistrer un commit. |
| `git log --oneline` | Afficher l'historique des commits. |
| `git push` | Envoyer les commits sur GitHub. |

### Dans le shell Django

| Instruction | Rôle |
| --- | --- |
| `from api_tester.models import ApiLog` | Importer le modèle. |
| `ApiLog.objects.count()` | Compter les tests enregistrés. |
| `ApiLog.objects.first()` | Afficher le test le plus récent. |
| `ApiLog.objects.all().delete()` | Vider l'historique. |

## A.3 Les pièges qui reviennent partout

Chaque partie se termine par ses propres pièges fréquents. Ceux-ci peuvent survenir à n'importe quel moment du projet :

| Symptôme | Cause probable | Solution |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'django'` (ou `'requests'`) | Le venv n'est pas activé dans ce terminal. | Vérifiez la présence de `(venv)` et activez-le si besoin. |
| Une modification de `main.js` ou de la page ne change rien | Le navigateur utilise une version en cache. | Rechargez avec `Ctrl+F5`. |
| Une modification d'un fichier Python ne change rien | Le fichier n'est pas enregistré, ou le serveur s'est arrêté après une erreur. | Enregistrez (`Ctrl+S`) et regardez le terminal du serveur : une erreur de syntaxe l'empêche de redémarrer. |
| Les modifications n'apparaissent pas, ou une autre application s'affiche sur http://127.0.0.1:8000/ | Un ancien `runserver` tourne encore. Sous Windows, un second serveur sur le même port démarre souvent **sans erreur**, et c'est l'ancien qui répond. | `Ctrl+C` dans chaque terminal de serveur, ou fermez les terminaux en trop, puis relancez un seul `runserver`. |
| `no such table` ou `no such column` | Une migration n'a pas été générée ou appliquée. | `makemigrations`, puis `migrate`. |
| Erreur 403 lors d'un test dans la page | Le jeton CSRF n'est pas transmis. | Vérifiez `{% csrf_token %}` dans le formulaire et l'en-tête `X-CSRFToken` dans `main.js`. |
| Erreur 500 lors d'un test dans la page | Une exception non gérée dans la vue. | Le terminal du serveur affiche l'erreur complète : lisez sa dernière ligne. |
| Une API de test ne répond plus | Le service est momentanément indisponible, ou bloqué par votre réseau. | Essayez une autre adresse de l'annexe A.1. |

> **À retenir**
>
> Deux réflexes résolvent la majorité des problèmes : **lire le terminal du serveur**, où Django affiche chaque requête et chaque erreur, et **ouvrir la console du navigateur** (`F12`), où s'affichent les erreurs JavaScript.

## A.4 L'historique de commits attendu

En suivant le tutoriel, `git log --oneline --reverse` doit afficher une progression proche de celle-ci, un commit par partie :

*git log --oneline --reverse (sans les identifiants)*
````
Initialisation du projet Django et de l'application api_tester
Ajout du modèle ApiLog et de sa migration initiale
Routage et vue index_view avec l'historique des 10 derniers tests
Interface Bootstrap : formulaire, panneau de résultat et historique en cartes
Vue test_api_view : validation des données reçues en JSON
Appel de l'API cible avec requests, support de PUT/DELETE et enregistrement des tests
Gestion des erreurs réseau (timeout, connexion, URL invalide)
Envoi du formulaire en JSON avec fetch et jeton CSRF
Affichage du résultat : badges, JSON formaté et cas d'erreur
Historique dynamique : ajout des cartes, limite de 10 et restauration au clic
Tests automatisés : modèle, page d'accueil et endpoint /api/test/
Note de sécurité SSRF et README
````

## A.5 Grille d'auto-évaluation

Avant de rendre votre projet, reprenez le barème du cahier des charges et vérifiez chaque critère :

| Critère du barème | Points | Ce qu'il faut pouvoir montrer | Partie |
| --- | --- | --- | --- |
| Exécution d'une requête et affichage du résultat | 20 | Statut, temps de réponse et corps JSON affichés pour GET et POST. | 7, 10 |
| Format JSON exclusif | 10 | Onglet Réseau : `Content-Type: application/json`, corps JSON, `json.loads(request.body)` et `JsonResponse` côté serveur. | 6, 9 |
| Protection CSRF | 10 | Jeton lu dans la page et envoyé dans `X-CSRFToken`, aucun `@csrf_exempt`, test `test_csrf_actif_aucun_exempt`. | 9, 12 |
| Modèle `ApiLog` conforme | 15 | Tous les champs, types et nullabilité du cahier des charges, `JSONField` natifs, migrations commitées. | 3, 7 |
| Gestion des cas d'erreur | 15 | Timeout, hôte injoignable, 4xx/5xx, non-JSON : aucun plantage, message clair, test enregistré. | 8, 10 |
| Historique | 15 | Limite à 10 (base et page), tri du plus récent, restauration de la méthode et de l'URL au clic. | 4, 11 |
| Bonnes pratiques de sécurité | 10 | `timeout=5`, schéma http/https, explication du risque SSRF et des pistes de protection. | 6, 7, 13 |
| Qualité du dépôt et du README | 5 | Commits lisibles, `.gitignore`, README complet, `requirements.txt`. | 2, 13 |
