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
