import json

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

    if not method or not url:
        return JsonResponse(
            {"error": "Les champs 'method' et 'url' sont requis."}, status=400
        )

    try:
        if method.upper() == 'GET':
            response = requests.get(url, timeout=5)
        else:
            response = requests.post(url, timeout=5)
    except requests.exceptions.Timeout:
        error_message = "La requête a expiré (timeout)."
        ApiLog.objects.create(
            url=url,
            method=method.upper(),
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
            method=method.upper(),
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
            method=method.upper(),
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
        # Réponse non-JSON : traitement affiné en session gestion d'erreurs
        response_body = response.text

    ApiLog.objects.create(
        url=url,
        method=method.upper(),
        status_code=response.status_code,
        response_time=response.elapsed.total_seconds(),  # en secondes, cf. models.py
        payload_sent=data,
        response_body=response_body,
    )

    return JsonResponse({
        "status_code": response.status_code,
        "response_time": response.elapsed.total_seconds() * 1000,  # en millisecondes
        "response_body": response_body,
    })
