"""
WSGI config for web project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/howto/deployment/wsgi/
"""

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sparktw.settings")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
#from django.conf import settings
#from ws4redis.uwsgi_runserver import uWSGIWebsocketServer
#
#_django_app = get_wsgi_application()
#_websocket_app = uWSGIWebsocketServer()
#
#
#def application(environ, start_response):
#    if environ.get('PATH_INFO').startswith(settings.WEBSOCKET_URL):
#        return _websocket_app(environ, start_response)
#    return _django_app(environ, start_response)
