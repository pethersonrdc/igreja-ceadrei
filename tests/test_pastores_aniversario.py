"""Pastores: só o painel pastoral define a data do aniversário da igreja."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Isola o banco antes de importar app/pastores nas rotas
_TMP = tempfile.TemporaryDirectory()
os.environ["PASTORES_DB_PATH"] = str(Path(_TMP.name) / "pastores-test.db")

import pastores  # noqa: E402
from app import app  # noqa: E402


class PastoresAniversarioTest(unittest.TestCase):
    def setUp(self) -> None:
        self._db = Path(os.environ["PASTORES_DB_PATH"])
        if self._db.exists():
            self._db.unlink()
        pastores._db_schema_ok = False
        pastores._db_import_ok = False
        pastores.DB_PATH = self._db
        pastores.init_db()

        self.app = app
        self.app.config["TESTING"] = True
        self.app.config["SECRET_KEY"] = "teste-aniversario"
        self.client = self.app.test_client()

    def tearDown(self) -> None:
        pastores._db_schema_ok = False
        pastores._db_import_ok = False
        if self._db.exists():
            self._db.unlink()

    def test_salvar_aniversario_trava_titulo_e_origem(self) -> None:
        eid = pastores.salvar_aniversario_igreja(
            data_iso="2026-10-12",
            horario="19:30",
            local="Templo",
            descricao="Celebração",
            aviso="Preparem-se!",
        )
        self.assertIsInstance(eid, int)
        eventos = pastores.listar_aniversario_igreja()
        self.assertEqual(len(eventos), 1)
        ev = eventos[0]
        self.assertEqual(ev["origem"], pastores.ORIGEM_ANIVERSARIO_IGREJA)
        self.assertEqual(ev["titulo"], "Aniversário da Igreja")
        self.assertEqual(ev["lider"], "Pastores")
        self.assertEqual(ev["data"], "2026-10-12")

        cal = pastores.calendario_mes(2026, 10)
        dia = next(d for d in cal["dias"] if d and d["dia"] == 12)
        self.assertTrue(any(e["origem"] == "aniversario_igreja" for e in dia["eventos"]))

    def test_admin_exige_login_pastores(self) -> None:
        resp = self.client.get("/pastores/admin?aba=calendario")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/pastores/login", resp.headers.get("Location", ""))

        resp = self.client.post(
            "/pastores/admin?aba=calendario&ano=2026&mes=10",
            data={"acao": "aniversario_igreja", "data": "2026-10-12"},
            follow_redirects=False,
        )
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/pastores/login", resp.headers.get("Location", ""))

    def test_pastor_publica_data_no_calendario(self) -> None:
        with self.client.session_transaction() as sess:
            sess["pastores_ok"] = True

        resp = self.client.get("/pastores/admin?aba=calendario")
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)
        self.assertIn("Aniversário da igreja", html)
        self.assertIn('name="acao" value="aniversario_igreja"', html)
        self.assertIn("5 dias", html)
        self.assertIn('name="data_inicio"', html)
        self.assertIn('name="data_fim"', html)

        resp = self.client.post(
            "/pastores/admin?aba=calendario&ano=2026&mes=10",
            data={
                "acao": "aniversario_igreja",
                "data_inicio": "2026-10-23",
                "data_fim": "2026-10-27",
                "horario": "19:30",
                "local": "Templo",
                "aviso": "Aniversário da igreja!",
            },
            follow_redirects=True,
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.get_data(as_text=True)
        self.assertIn("5 dia(s)", body)

        eventos = pastores.listar_aniversario_igreja()
        self.assertEqual(len(eventos), 5)
        self.assertEqual(
            [e["data"] for e in eventos],
            [
                "2026-10-23",
                "2026-10-24",
                "2026-10-25",
                "2026-10-26",
                "2026-10-27",
            ],
        )

        publico = self.client.get("/calendario-lideres?ano=2026&mes=10")
        self.assertEqual(publico.status_code, 200)
        self.assertIn("Aniversário da Igreja", publico.get_data(as_text=True))

    def test_periodo_padrao_5_dias_sem_fim(self) -> None:
        datas = pastores.datas_aniversario_periodo("2026-09-23")
        self.assertEqual(
            datas,
            [
                "2026-09-23",
                "2026-09-24",
                "2026-09-25",
                "2026-09-26",
                "2026-09-27",
            ],
        )
        ids = pastores.salvar_aniversario_igreja_periodo(
            data_inicio_iso="2026-09-23",
            horario="19:00",
        )
        self.assertEqual(len(ids), 5)
        # Republicar o mesmo período atualiza, não duplica
        ids2 = pastores.salvar_aniversario_igreja_periodo(
            data_inicio_iso="2026-09-23",
            data_fim_iso="2026-09-27",
        )
        self.assertEqual(len(ids2), 5)
        self.assertEqual(len(pastores.listar_aniversario_igreja()), 5)

    def test_responsavel_nao_usa_origem_aniversario(self) -> None:
        from app import _processar_evento_responsavel
        from flask import session as flask_session

        with self.app.test_request_context(
            "/batismo/admin",
            method="POST",
            data={"data": "2026-10-12", "acao": "evento"},
        ):
            flask_session["batismo_ok"] = True
            ok = _processar_evento_responsavel(pastores.ORIGEM_ANIVERSARIO_IGREJA)
            self.assertTrue(ok)
        self.assertEqual(pastores.listar_aniversario_igreja(), [])


if __name__ == "__main__":
    unittest.main()
