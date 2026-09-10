"""Sitemap e robots.txt para o Google Search Console."""

from __future__ import annotations

import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import app  # noqa: E402


class SitemapTest(unittest.TestCase):
    def setUp(self) -> None:
        self.app = app
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_robots_txt(self) -> None:
        resp = self.client.get("/robots.txt")
        self.assertEqual(resp.status_code, 200)
        texto = resp.get_data(as_text=True)
        self.assertIn("User-agent: *", texto)
        self.assertIn("Sitemap: https://igrejaceasdrei.com.br/sitemap.xml", texto)
        self.assertIn("Disallow: /admin/", texto)

    def test_sitemap_xml(self) -> None:
        resp = self.client.get("/sitemap.xml")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("xml", (resp.mimetype or "").lower())
        corpo = resp.get_data(as_text=True)
        self.assertIn("<urlset", corpo)
        self.assertIn("https://igrejaceasdrei.com.br/</loc>", corpo)
        self.assertIn("https://igrejaceasdrei.com.br/cultos</loc>", corpo)
        self.assertIn("https://igrejaceasdrei.com.br/batismo/inscricao</loc>", corpo)
        self.assertIn("https://igrejaceasdrei.com.br/evento/leoas</loc>", corpo)


if __name__ == "__main__":
    unittest.main()
