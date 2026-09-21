from django.http import HttpResponseNotAllowed, JsonResponse
from django.shortcuts import render

# Création des views


def index_view(request):
    # TODO session historique : injecter les 10 derniers ApiLog
    return render(request, 'api_tester/index.html', {})


def test_api_view(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    # TODO session appel requests : lire le body JSON, appeler requests,
    # mesurer le temps, créer l'ApiLog, renvoyer le vrai résultat
    return JsonResponse({"status": "ok", "detail": "squelette, logique à venir"})
