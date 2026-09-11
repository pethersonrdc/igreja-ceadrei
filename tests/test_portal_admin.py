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

    def test_portal_login_visual_fundo_e_emblema(self) -> None:
        resp = self.client.get("/portal/login")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("tema-portal-login", html)
        self.assertIn("/portal/assets/fundo.jpg", html)
        self.assertIn("/portal/assets/portal-login.css", html)
        self.assertIn("portal-login-card", html)
        self.assertIn("portal-login-ember", html)
        # CSS embutido no HTML (funciona mesmo com static incompleto)
        self.assertIn(".portal-login-card", html)
        self.assertIn("images/emblema.png", html)
        fundo = self.client.get("/portal/assets/fundo.jpg")
        self.assertEqual(fundo.status_code, 200)
        self.assertEqual(fundo.mimetype, "image/jpeg")
        self.assertGreater(len(fundo.data), 1000)
        css = self.client.get("/portal/assets/portal-login.css")
        self.assertEqual(css.status_code, 200)
        self.assertIn("tema-portal-login", css.get_data(as_text=True))

    def test_portal_assets_sem_arquivos_no_disco(self) -> None:
        """Assets embutidos: rotas respondem mesmo sem ficheiros em static/."""
        from pathlib import Path

        css = Path(self.app.static_folder) / "css" / "portal-login.css"
        img = Path(self.app.static_folder) / "images" / "fundo-portal-login.jpg"
        css_bak = css.read_bytes() if css.exists() else None
        img_bak = img.read_bytes() if img.exists() else None
        try:
            if css.exists():
                css.unlink()
            if img.exists():
                img.unlink()
            fundo = self.client.get("/portal/assets/fundo.jpg")
            self.assertEqual(fundo.status_code, 200)
            self.assertGreater(len(fundo.data), 1000)
            style = self.client.get("/portal/assets/portal-login.css")
            self.assertEqual(style.status_code, 200)
            self.assertIn("portal-login-card", style.get_data(as_text=True))
            login = self.client.get("/portal/login")
            self.assertEqual(login.status_code, 200)
            self.assertIn("portal-login-card", login.get_data(as_text=True))
        finally:
            if css_bak is not None:
                css.parent.mkdir(parents=True, exist_ok=True)
                css.write_bytes(css_bak)
            if img_bak is not None:
                img.parent.mkdir(parents=True, exist_ok=True)
                img.write_bytes(img_bak)

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
