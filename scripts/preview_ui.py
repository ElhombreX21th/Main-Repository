"""Serve the ReembolsaBR UI demo using only the Python standard library."""

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

WEB_DIR = Path(__file__).resolve().parents[1] / "app" / "web"


class PreviewHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path: str) -> str:
        clean_path = path.split("?", 1)[0]
        if clean_path in {"/", "/demo"}:
            clean_path = "/index.html"
        return str(WEB_DIR / clean_path.lstrip("/"))


if __name__ == "__main__":
    address = ("0.0.0.0", 4173)
    print("ReembolsaBR demo: http://127.0.0.1:4173/demo")
    ThreadingHTTPServer(address, PreviewHandler).serve_forever()
