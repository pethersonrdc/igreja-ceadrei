"""Galeria: variantes Pillow/srcset, sem lazy na Mídia, carrossel sob demanda."""

from __future__ import annotations

import tempfile
import unittest
import uuid
from pathlib import Path
import sys

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import gallery  # noqa: E402
from app import app  # noqa: E402


class GaleriaVariantesUnitTest(unittest.TestCase):
    """Testa Pillow/srcset sem tocar no SQLite real."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self._uploads = Path(self._tmp.name)
        self._prev_upload = gallery.UPLOAD_DIR
        gallery.UPLOAD_DIR = self._uploads

    def tearDown(self) -> None:
        gallery.UPLOAD_DIR = self._prev_upload
        self._tmp.cleanup()

    def _salvar_foto(self, nome: str = "culto.jpg", size=(2400, 1600)) -> str:
        caminho = self._uploads / nome
        Image.new("RGB", size, (30, 60, 90)).save(caminho, format="JPEG", quality=90)
        return nome

    def test_gerar_variantes_mantem_original(self) -> None:
        nome = self._salvar_foto("abc.jpg")
        criados = gallery.gerar_variantes(nome)
        self.assertEqual(len(criados), 3)
        self.assertTrue((self._uploads / "abc.jpg").exists())
        for w in gallery.VARIANT_WIDTHS:
            path = self._uploads / f"abc_{w}.jpg"
            self.assertTrue(path.exists(), path.name)
            with Image.open(path) as im:
                self.assertLessEqual(im.size[0], w)

    def test_srcset_inclui_variantes_e_original(self) -> None:
        nome = self._salvar_foto("xyz.jpg")
        gallery.gerar_variantes(nome)
        srcset = gallery.srcset_galeria(nome)
        self.assertIn("xyz_480.jpg 480w", srcset)
        self.assertIn("xyz_960.jpg 960w", srcset)
        self.assertIn("xyz_1600.jpg 1600w", srcset)
        self.assertIn("xyz.jpg 2400w", srcset)

    def test_apagar_arquivo_e_variantes(self) -> None:
        nome = self._salvar_foto("del.jpg")
        gallery.gerar_variantes(nome)
        gallery.apagar_arquivo_e_variantes(nome)
        self.assertFalse((self._uploads / "del.jpg").exists())
        self.assertFalse((self._uploads / "del_480.jpg").exists())


class GaleriaPerformanceHttpTest(unittest.TestCase):
    def setUp(self) -> None:
        gallery.init_db()
        self.app = app
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self._post_ids: list[int] = []
        self._arquivos: list[str] = []

    def tearDown(self) -> None:
        for post_id in self._post_ids:
            gallery.apagar_post(post_id)
        # Segurança extra caso o post não tenha sido registrado
        for nome in self._arquivos:
            gallery.apagar_arquivo_e_variantes(nome)

    def _criar_foto(self, prefix: str = "t") -> str:
        nome = f"{prefix}-{uuid.uuid4().hex}.jpg"
        caminho = gallery.UPLOAD_DIR / nome
        Image.new("RGB", (1800, 1200), (40, 80, 120)).save(
            caminho, format="JPEG", quality=88
        )
        gallery.gerar_variantes(nome)
        self._arquivos.append(nome)
        return nome

    def test_galeria_publica_sem_lazy_com_srcset_e_photoswipe(self) -> None:
        nome = self._criar_foto("pub")
        post_id = gallery.criar_post("Culto", "Domingo", "Publicada", [nome])
        self._post_ids.append(post_id)

        html = self.client.get("/galeria").get_data(as_text=True)
        self.assertNotIn('loading="lazy"', html)
        self.assertIn("srcset=", html)
        self.assertIn(f"{Path(nome).stem}_480.jpg", html)
        self.assertIn(f"{Path(nome).stem}_960.jpg", html)
        # Grid usa variante leve no src; original fica no href do lightbox
        self.assertIn(f'src="/static/uploads/galeria/{Path(nome).stem}_960.jpg"', html)
        self.assertIn(f'href="/static/uploads/galeria/{nome}"', html)
        self.assertIn("data-pswp-gallery", html)
        self.assertIn("galeria-lightbox.js", html)
        self.assertIn("photoswipe", html.lower())

    def test_home_carrossel_com_src_real(self) -> None:
        nomes = [self._criar_foto(f"home{i}") for i in range(3)]
        post_id = gallery.criar_post("Culto", "Domingo", "Carrossel", nomes)
        self._post_ids.append(post_id)

        html = self.client.get("/").get_data(as_text=True)
        stem0 = Path(nomes[0]).stem
        stem1 = Path(nomes[1]).stem
        # Sempre src real (evita tela branca se o JS antigo estiver em cache)
        self.assertIn(f'src="/static/uploads/galeria/{stem0}_960.jpg"', html)
        self.assertIn(f'src="/static/uploads/galeria/{stem1}_960.jpg"', html)
        self.assertNotIn("data:image/gif;base64", html)
        self.assertIn("carousel.js?v=", html)


if __name__ == "__main__":
    unittest.main()
