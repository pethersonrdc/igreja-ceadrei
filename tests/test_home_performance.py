"""Home e páginas públicas: menos peso no celular (fontes, hero, vídeo sob demanda)."""

from __future__ import annotations

import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import porta_altar  # noqa: E402
from app import app  # noqa: E402


class HomePerformanceTest(unittest.TestCase):
    def setUp(self) -> None:
        porta_altar.init_db()
        self.app = app
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self._video_ids: list[int] = []

    def tearDown(self) -> None:
        for video_id in self._video_ids:
            porta_altar.apagar_video(video_id)

    def _criar_video(self, **kwargs) -> int:
        dados = {
            "titulo": "Vídeo de teste mobile",
            "descricao": "Capa com botão de play",
            "arquivo": "teste-mobile.mp4",
            "capa": "",
            "culto_titulo": "Culto teste",
            "termino_em": "",
            "tipo": "pos_culto",
        }
        dados.update(kwargs)
        video_id = porta_altar.criar_video(**dados)
        self._video_ids.append(video_id)
        return video_id

    def test_home_fontes_enxutas(self) -> None:
        html = self.client.get("/").get_data(as_text=True)
        self.assertIn("Cormorant+Garamond", html)
        self.assertIn("Outfit", html)
        self.assertNotIn("Libre+Baskerville", html)
        self.assertNotIn("Source+Sans", html)
        self.assertNotIn("wght@300", html)

    def test_home_hero_com_srcset_e_sem_2000px(self) -> None:
        html = self.client.get("/").get_data(as_text=True)
        self.assertIn("hero-media-img", html)
        self.assertIn("w=800", html)
        self.assertIn("srcset=", html)
        self.assertNotIn("w=2000", html)
        self.assertNotIn('background-image: url("https://images.unsplash.com', html)

    def test_home_video_so_carrega_depois_do_toque(self) -> None:
        self._criar_video()
        html = self.client.get("/").get_data(as_text=True)
        self.assertIn("video-lazy", html)
        self.assertIn("teste-mobile.mp4", html)
        self.assertIn("Assistir", html)
        self.assertNotIn("<video", html)
        self.assertNotIn('preload="metadata"', html)
        self.assertNotIn(" autoplay", html)
        self.assertNotIn("autoplay=", html)

    def test_porta_altar_video_lazy(self) -> None:
        self._criar_video(tipo="papo_altar", arquivo="papo-teste.mp4")
        html = self.client.get("/porta-do-altar").get_data(as_text=True)
        self.assertIn("video-lazy", html)
        self.assertIn("papo-teste.mp4", html)
        self.assertNotIn('preload="metadata"', html)
        self.assertNotIn(" autoplay", html)
        self.assertNotIn("autoplay=", html)

    def test_nginx_serve_static_no_disco(self) -> None:
        conf = (ROOT / "deploy" / "hostinger" / "nginx.conf").read_text(encoding="utf-8")
        self.assertIn("location /static/", conf)
        self.assertIn("alias ", conf)
        self.assertIn("sendfile on", conf)
        self.assertIn("gzip off", conf)
        self.assertNotIn("location ~*", conf)


if __name__ == "__main__":
    unittest.main()
