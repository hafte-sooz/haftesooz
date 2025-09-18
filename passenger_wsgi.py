import sys, os, subprocess, time, requests
from wsgiref.util import setup_testing_defaults

# Add project directory to sys.path
sys.path.insert(0, os.path.dirname(__file__))

# Path to daphne binary inside your virtualenv
daphne_cmd = "/home/kecxpozx/virtualenv/haftesooz/3.9/bin/daphne"
daphne_port = 8001
pidfile = "/tmp/daphne_haftesooz.pid"


def start_daphne():
    """Start Daphne ASGI server if it's not already running."""
    if not os.path.exists(pidfile):
        with open(pidfile, "w") as f:
            proc = subprocess.Popen(
                [daphne_cmd, "-b", "127.0.0.1", "-p", str(daphne_port), "main:app"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            f.write(str(proc.pid))
        time.sleep(2)


# Start Daphne once when Passenger loads this file
start_daphne()


def application(environ, start_response):
    """WSGI entrypoint called by Passenger."""
    setup_testing_defaults(environ)

    method = environ['REQUEST_METHOD']
    path = environ.get('PATH_INFO', '/')
    query = environ.get('QUERY_STRING', '')
    url = f"http://127.0.0.1:{daphne_port}{path}"
    if query:
        url += "?" + query

    # Read request body if exists
    length = int(environ.get('CONTENT_LENGTH') or 0)
    body = environ['wsgi.input'].read(length) if length > 0 else b''

    # Build headers
    headers = {
        k[5:].replace('_', '-'): v
        for k, v in environ.items() if k.startswith('HTTP_')
    }

    try:
        # Send request to local Daphne server
        resp = requests.request(method, url, headers=headers, data=body)
        start_response(f"{resp.status_code} OK", list(resp.headers.items()))
        return [resp.content]

    except Exception as e:
        err = f"Internal error: {str(e)}".encode()
        start_response("500 Internal Server Error", [("Content-Type", "text/plain")])
        return [err]
