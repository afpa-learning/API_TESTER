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
