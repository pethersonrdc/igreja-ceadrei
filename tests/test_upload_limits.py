"""Limites de upload de vídeo da mídia (Papo de Altar)."""

from __future__ import annotations

import io
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import app as app_module  # noqa: E402


class UploadLimitsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.app = app_module.app
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_limite_cabe_video_de_varios_minutos(self) -> None:
        self.assertGreaterEqual(app_module.MAX_UPLOAD_MB, 1024)
        self.assertGreaterEqual(
            self.app.config["MAX_CONTENT_LENGTH"],
            1024 * 1024 * 1024,
        )

    def test_413_mostra_aviso_e_nao_bloqueia_por_duracao(self) -> None:
        original = self.app.config["MAX_CONTENT_LENGTH"]
        self.app.config["MAX_CONTENT_LENGTH"] = 1024
        try:
            with self.client.session_transaction() as sess:
                sess["admin_ok"] = True
            resp = self.client.post(
                "/porta-do-altar/admin",
                data={
                    "acao": "video_criar",
                    "titulo": "Papo de Altar",
                    "termino_em": "2026-08-24T20:00",
                    "tipo": "papo_altar",
                    "video": (io.BytesIO(b"x" * 4096), "culto.mp4"),
                },
                content_type="multipart/form-data",
                follow_redirects=True,
            )
            self.assertEqual(resp.status_code, 200)
            html = resp.get_data(as_text=True)
            self.assertIn("grande demais", html)
            self.assertIn("mais de 3 minutos são permitidos", html)
        finally:
            self.app.config["MAX_CONTENT_LENGTH"] = original

    def test_painel_explica_que_nao_ha_limite_de_3_min(self) -> None:
        with self.client.session_transaction() as sess:
            sess["admin_ok"] = True
        resp = self.client.get("/porta-do-altar/admin")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("não há limite de 3 min", html)
        self.assertIn(str(app_module.MAX_UPLOAD_MB), html)


if __name__ == "__main__":
    unittest.main()
