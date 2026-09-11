"""Portal CEASDREI: login único + aparência do site."""

from __future__ import annotations

import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tema_site  # noqa: E402
from app import app  # noqa: E402


class PortalAdminTest(unittest.TestCase):
    def setUp(self) -> None:
        self.app = app
        self.app.config["TESTING"] = True
        self.app.config["SECRET_KEY"] = "teste-portal"
        self.client = self.app.test_client()
        # tema de teste isolado
        self._tema_path = tema_site._path()
        self._tema_backup = None
        if self._tema_path.exists():
            self._tema_backup = self._tema_path.read_text(encoding="utf-8")

    def tearDown(self) -> None:
        if self._tema_backup is None:
            if self._tema_path.exists():
                self._tema_path.unlink()
        else:
            self._tema_path.write_text(self._tema_backup, encoding="utf-8")

    def test_portal_login_abre_hub_e_admins(self) -> None:
        negado = self.client.get("/portal", follow_redirects=False)
        self.assertIn(negado.status_code, (302, 301))

        resp = self.client.post(
            "/portal/login",
            data={"usuario": "ceasdrei", "senha": "ceasdrei"},
            follow_redirects=True,
        )
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("Portal CEASDREI", html)
        self.assertIn("Eventos e painéis", html)
        self.assertIn("Aparência do site", html)
        self.assertIn("Batismo", html)

        # sessão libera painel de batismo sem senha própria
        batismo = self.client.get("/batismo/admin", follow_redirects=False)
        self.assertEqual(batismo.status_code, 200)

    def test_portal_aparencia_salva_tema(self) -> None:
        self.client.post(
            "/portal/login",
            data={"usuario": "ceasdrei", "senha": "ceasdrei"},
        )
        resp = self.client.post(
            "/portal/aparencia",
            data={
                "acao": "salvar",
                "cor_texto": "#112233",
                "cor_fundo": "#fafafa",
                "cor_destaque": "#cc9944",
                "cor_secundaria": "#223344",
                "fonte_titulo": "Playfair Display",
                "fonte_texto": "Lato",
                "estilo_fundo": "suave",
            },
            follow_redirects=True,
        )
        self.assertEqual(resp.status_code, 200)
        tema = tema_site.carregar()
        self.assertEqual(tema["fonte_titulo"], "Playfair Display")
        self.assertEqual(tema["estilo_fundo"], "suave")

        home = self.client.get("/").get_data(as_text=True)
        self.assertIn("--ink:#112233", home)
        self.assertIn("Playfair+Display", home)


if __name__ == "__main__":
    unittest.main()
