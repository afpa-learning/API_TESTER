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
