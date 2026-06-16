"""Production entry point for the Kattis speedrun app.

Runs the Flask-SocketIO app without the debug reloader and starts the
background judging thread (which in development only starts under the
Werkzeug reloader child). Bind address/port are overridable via the
HOST / PORT environment variables. Intended to be launched by the
systemd unit `kattis-speedrun.service`.
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
for path in (ROOT, os.path.join(ROOT, "kattis-cli")):
    if path not in sys.path:
        sys.path.insert(0, path)

from backend.app import app, start_judging_thread
from backend.extensions import socketio

if __name__ == "__main__":
    start_judging_thread()
    socketio.run(
        app,
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "5000")),
        debug=False,
        allow_unsafe_werkzeug=True,
    )
