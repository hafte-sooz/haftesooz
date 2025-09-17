"""WSGI entrypoint wrapper for cPanel/Passenger

This file exposes a WSGI `application` callable that wraps the FastAPI
ASGI app defined in `main.py` using a small adapter. Passenger (cPanel)
and other WSGI hosts will import `application` from this module.

The code tries a couple of common adapters in order:
- `AsgiToWsgi` from `asgiref.wsgi` (preferred when available)
- `ASGI2Wsgi` from `asgi2wsgi` as a fallback

If no adapter is available the module exposes a tiny WSGI app that
returns a helpful error message instructing the admin to install
an adapter (e.g. `pip install asgiref` or `pip install asgi2wsgi`).
"""

from __future__ import annotations

from typing import Callable

try:
    # Import the FastAPI ASGI app from main.py
    from main import app as asgi_app
except Exception as exc:  # pragma: no cover - very unlikely during normal import
    # If importing fails, provide a minimal WSGI app explaining the problem.
    def application(environ, start_response):
        start_response('500 Internal Server Error', [('Content-Type', 'text/plain; charset=utf-8')])
        msg = ("Failed to import ASGI app from main.py: " + str(exc) + "\n").encode('utf-8')
        return [msg]
else:
    # Try AsgiToWsgi from asgiref (commonly available via starlette/fastapi deps)
    try:
        from asgiref.wsgi import AsgiToWsgi

        application = AsgiToWsgi(asgi_app)  # type: Callable
    except Exception:
        # Try asgi2wsgi as an alternative adapter
        try:
            from asgi2wsgi import ASGI2Wsgi

            application = ASGI2Wsgi(asgi_app)  # type: Callable
        except Exception:
            # Final fallback: a helpful WSGI app that instructs to install an adapter
            def application(environ, start_response):
                start_response('500 Internal Server Error', [('Content-Type', 'text/plain; charset=utf-8')])
                msg = (
                    "ASGI->WSGI adapter not installed.\n"
                    "Install one of the following in your virtualenv and restart:\n"
                    "  pip install asgiref    # provides AsgiToWsgi\n"
                    "  pip install asgi2wsgi  # alternative adapter\n"
                ).encode('utf-8')
                return [msg]
