import json
from urllib.parse import urlparse

import requests
from django.http import HttpResponseNotAllowed, JsonResponse
from django.shortcuts import render

from .models import ApiLog

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
