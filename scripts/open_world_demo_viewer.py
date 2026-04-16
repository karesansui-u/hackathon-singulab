#!/usr/bin/env python3
"""
Serve the repository locally and open the world demo viewer in a browser.

This is the easiest way to get the bundled demo auto-loaded without using the
directory picker on first launch.
"""

from __future__ import annotations

import http.server
import socketserver
import threading
import webbrowser
from pathlib import Path


HOST = "127.0.0.1"
PORT = 8876
VIEWER_PATH = "/visualization/world_demo_viewer.html"


class ReusableTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    handler = http.server.SimpleHTTPRequestHandler
    server = None
    selected_port = PORT
    for candidate in range(PORT, PORT + 20):
        try:
            server = ReusableTCPServer(
                (HOST, candidate),
                lambda *args, **kwargs: handler(*args, directory=str(repo_root), **kwargs),
            )
            selected_port = candidate
            break
        except OSError:
            continue

    if server is None:
        raise SystemExit("Could not bind a local port for the viewer server.")

    with server:
        url = f"http://{HOST}:{selected_port}{VIEWER_PATH}"
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        print(f"Serving {repo_root} at {url}")
        webbrowser.open(url)
        try:
            thread.join()
        except KeyboardInterrupt:
            print("\nStopping viewer server...")
            server.shutdown()


if __name__ == "__main__":
    main()
