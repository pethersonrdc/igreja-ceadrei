"""Headers de segurança, Open Graph e favicon."""

from __future__ import annotations

import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import app  # noqa: E402


class SecurityHeadersTest(unittest.TestCase):
    def setUp(self) -> None:
        self.app = app
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_home_tem_headers_basicos(self) -> None:
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(resp.headers.get("X-Frame-Options"), "SAMEORIGIN")
        self.assertEqual(
            resp.headers.get("Referrer-Policy"), "strict-origin-when-cross-origin"
        )
        self.assertIn("camera=()", resp.headers.get("Permissions-Policy", ""))
        csp = resp.headers.get("Content-Security-Policy", "")
        self.assertIn("default-src 'self'", csp)
        self.assertIn("frame-ancestors 'self'", csp)
        self.assertIn("https://cdn.jsdelivr.net", csp)

    def test_hsts_em_https_simulado(self) -> None:
        resp = self.client.get("/", headers={"X-Forwarded-Proto": "https"})
        self.assertIn(
            "max-age=31536000",
            resp.headers.get("Strict-Transport-Security", ""),
        )

    def test_open_graph_e_favicon_no_html(self) -> None:
        html = self.client.get("/").get_data(as_text=True)
        self.assertIn('property="og:title"', html)
        self.assertIn('property="og:description"', html)
        self.assertIn('property="og:image"', html)
        self.assertIn("/static/images/emblema.png", html)
        self.assertIn('rel="icon"', html)
        self.assertIn('name="twitter:card"', html)

    def test_favicon_ico(self) -> None:
        resp = self.client.get("/favicon.ico")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("image/png", resp.headers.get("Content-Type", ""))

    def test_nginx_template_tem_headers(self) -> None:
        conf = (ROOT / "deploy" / "hostinger" / "nginx.conf").read_text(
            encoding="utf-8"
        )
        self.assertIn("Content-Security-Policy", conf)
        self.assertIn("X-Frame-Options", conf)
        self.assertIn("location = /favicon.ico", conf)
        self.assertIn("sendfile on", conf)
        self.assertIn("gzip off", conf)


if __name__ == "__main__":
    unittest.main()
