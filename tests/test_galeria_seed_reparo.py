"""Galeria vazia com arquivos órfãos no disco deve republicar automaticamente."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
import sys

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import gallery  # noqa: E402


class GaleriaSeedReparoTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self._prev = {
            "UPLOAD_DIR": gallery.UPLOAD_DIR,
            "DB_PATH": gallery.DB_PATH,
            "SEED_FLAG_PATH": gallery.SEED_FLAG_PATH,
            "SEED_DIR": gallery.SEED_DIR,
            "init_db": gallery.init_db,
            "_seed_flag_path": gallery._seed_flag_path,
        }
        gallery.UPLOAD_DIR = base / "uploads"
        gallery.UPLOAD_DIR.mkdir()
        gallery.DB_PATH = base / "galeria.db"
        gallery.SEED_FLAG_PATH = base / "galeria_seed_ok.json"
        gallery.SEED_DIR = base / "seed"
        gallery.SEED_DIR.mkdir()

        def _flag() -> Path:
            return gallery.SEED_FLAG_PATH

        def _init() -> None:
            gallery.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
            gallery.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            with gallery._connect() as conn:
                conn.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS posts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        culto_titulo TEXT NOT NULL,
                        culto_dia TEXT NOT NULL,
                        titulo TEXT NOT NULL,
                        criado_em TEXT NOT NULL,
                        expira_em TEXT NOT NULL DEFAULT ''
                    );
                    CREATE TABLE IF NOT EXISTS fotos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        post_id INTEGER NOT NULL,
                        arquivo TEXT NOT NULL
                    );
                    """
                )

        gallery._seed_flag_path = _flag  # type: ignore[method-assign]
        gallery.init_db = _init  # type: ignore[method-assign]
        gallery.init_db()

    def tearDown(self) -> None:
        gallery.UPLOAD_DIR = self._prev["UPLOAD_DIR"]
        gallery.DB_PATH = self._prev["DB_PATH"]
        gallery.SEED_FLAG_PATH = self._prev["SEED_FLAG_PATH"]
        gallery.SEED_DIR = self._prev["SEED_DIR"]
        gallery.init_db = self._prev["init_db"]
        gallery._seed_flag_path = self._prev["_seed_flag_path"]
        self._tmp.cleanup()

    def test_republica_orfaos_mesmo_com_flag(self) -> None:
        Image.new("RGB", (200, 120), (40, 80, 120)).save(
            gallery.UPLOAD_DIR / "orfao.png", format="PNG"
        )
        gallery.SEED_FLAG_PATH.write_text(
            json.dumps({"ok": True, "motivo": "apagou_post_9"}),
            encoding="utf-8",
        )
        self.assertEqual(gallery.listar_posts_ativos(), [])
        post_id = gallery.seed_fotos_iniciais()
        self.assertIsNotNone(post_id)
        posts = gallery.listar_posts_ativos()
        self.assertEqual(len(posts), 1)
        arquivos = [f["arquivo"] for f in posts[0]["fotos"]]
        self.assertEqual(arquivos, ["orfao.png"])

    def test_nao_recria_se_midia_apagou_tudo(self) -> None:
        gallery.SEED_FLAG_PATH.write_text(
            json.dumps({"ok": True, "motivo": "apagou_post_9"}),
            encoding="utf-8",
        )
        Image.new("RGB", (80, 60), (1, 2, 3)).save(gallery.SEED_DIR / "seed.png")
        self.assertIsNone(gallery.seed_fotos_iniciais())
        self.assertEqual(gallery.listar_posts_ativos(), [])


if __name__ == "__main__":
    unittest.main()
