"""Passenger (cPanel) WSGI loader.

Passenger looks for `passenger_wsgi.py` by default. This file simply imports
`application` from `wsgi.py` so cPanel can serve the FastAPI app.
"""

from wsgi import application

