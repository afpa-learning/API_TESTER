"""
Configuration WSGI pour le projet api_tester_project.

"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api_tester_project.settings')

application = get_wsgi_application()
