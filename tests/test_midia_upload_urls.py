"""Uploads de aniversário/história devem usar /midia, não /static."""

from __future__ import annotations

import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import persistencia  # noqa: E402
from app import app  # noqa: E402


class MidiaUploadUrlTest(unittest.TestCase):
    def test_url_upload_helper(self) -> None:
        self.assertEqual(
            persistencia.url_upload("aniversario", "foto.jpg"),
            "/midia/uploads/aniversario/foto.jpg",
        )
        self.assertEqual(
            persistencia.url_upload("historia", "marco.png"),
            "/midia/uploads/historia/marco.png",
        )
        self.assertEqual(persistencia.url_upload("aniversario", ""), "")
        self.assertEqual(persistencia.url_upload("aniversario", "../x.jpg"), "")

    def test_templates_apontam_midia_upload(self) -> None:
        anni = (ROOT / "templates" / "aniversario.html").read_text(encoding="utf-8")
        hist = (ROOT / "templates" / "historia.html").read_text(encoding="utf-8")
        self.assertIn("midia_upload('aniversario'", anni)
        self.assertNotIn("uploads/aniversario/", anni)
        self.assertIn("midia_upload('historia'", hist)
        self.assertNotIn("uploads/historia/", hist)

    def test_paginas_respondem(self) -> None:
        client = app.test_client()
        self.assertEqual(client.get("/aniversario").status_code, 200)
        self.assertEqual(client.get("/historia").status_code, 200)
        self.assertEqual(client.get("/galeria").status_code, 200)


if __name__ == "__main__":
    unittest.main()
